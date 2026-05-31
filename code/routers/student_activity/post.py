from fastapi import APIRouter, Depends, HTTPException
from .helpers import (
    get_scan_admin_by_name,
    get_student_by_code,
    get_activity_by_id,
    validate_activity_location,
    get_time_window_status,
    get_unix_time,
    calculate_earned_hours,
    build_student_activity_response,
    get_scan_status_text,
    format_activity_time_text,
    format_time_dot
)
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from sqlalchemy import and_, or_, func
from datetime import datetime
from zoneinfo import ZoneInfo
from database import get_db
from models import Student, Activity, StudentActivity,StudentPosition , Position
from schemas.schemas_student_activity import (
    StudentActivityRegisterRequest,
    StudentActivityCheckinRequest,
    StudentActivityResponse,
    StudentActivityAdminSearchRequest,
    StudentActivityAdminListResponse,
    StudentActivityAllInOneSearchRequest,
    StudentActivityAllInOneResponse,
)

router = APIRouter()

@router.post("/register", response_model=StudentActivityResponse)
def register_activity(
    body: StudentActivityRegisterRequest,
    db: Session = Depends(get_db)
):
    student = get_student_by_code(db, body.student_code)
    activity = get_activity_by_id(db, body.activity_id)

    if not activity.require_registration:
        raise HTTPException(
            status_code=400,
            detail="กิจกรรมนี้ไม่จำเป็นต้องลงทะเบียนล่วงหน้า"
        )

    existing = (
        db.query(StudentActivity)
        .filter(
            StudentActivity.student_id == student.student_id,
            StudentActivity.activity_id == activity.activity_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="นิสิตลงทะเบียนกิจกรรมนี้แล้ว"
        )

    registered_count = (
        db.query(func.count(StudentActivity.student_activity_id))
        .filter(StudentActivity.activity_id == activity.activity_id)
        .scalar()
        or 0
    )

    if activity.max_participants is not None and registered_count >= activity.max_participants:
        raise HTTPException(
            status_code=400,
            detail="กิจกรรมนี้มีผู้ลงทะเบียนเต็มแล้ว"
        )

    now = get_unix_time()

    item = StudentActivity(
        student_id=student.student_id,
        activity_id=activity.activity_id,
        attendance_status="ไม่เข้าร่วม",
        registered_at=now,
        checkin_at=None,
        checkout_at=None,

        created_by_id=student.user_id,
        created_by_name=f"{student.first_name} {student.last_name}",
        updated_by_id=student.user_id,
        updated_by_name=f"{student.first_name} {student.last_name}",

        created_at=now,
        updated_at=now,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "detail": "ลงทะเบียนกิจกรรมสำเร็จ",
        "data": build_student_activity_response(item, student, activity)
    }

@router.post("/checkin", response_model=StudentActivityResponse)
def checkin_activity(
    body: StudentActivityCheckinRequest,
    db: Session = Depends(get_db)
):
    admin = get_scan_admin_by_name(db, body.created_by_name)
    student = get_student_by_code(db, body.student_code)
    activity = get_activity_by_id(db, body.activity_id)

    if activity.check_type == "checkout_only":
        raise HTTPException(status_code=400, detail="กิจกรรมนี้ไม่รองรับการเช็คอิน")

    validate_activity_location(activity, body.checkin_lat, body.checkin_lng)

    # current_time = datetime.now().time()
    current_time = datetime.now(ZoneInfo("Asia/Bangkok")).time()
    # is_valid_checkin_time = is_time_in_window(
    #     activity.checkin_open_time,
    #     activity.checkin_close_time,
    #     current_time
    # )
    checkin_time_status = get_time_window_status(
        activity.checkin_open_time,
        activity.checkin_close_time,
        current_time
    )

    is_valid_checkin_time = checkin_time_status == "valid"

    if admin.role == "temporary_admin":
        if checkin_time_status == "not_started":
            raise HTTPException(
                status_code=403,
                detail="ยังไม่ถึงเวลาเช็คอิน"
            )

        if checkin_time_status == "closed":
            raise HTTPException(
                status_code=403,
                detail="หมดเวลาลงทะเบียนเช็คอินแล้ว"
            )

    item = (
        db.query(StudentActivity)
        .filter(
            StudentActivity.student_id == student.student_id,
            StudentActivity.activity_id == activity.activity_id
        )
        .first()
    )

    if activity.require_registration and not item:
        raise HTTPException(status_code=400, detail="กิจกรรมนี้ต้องลงทะเบียนก่อนเช็คอิน")

    if item and item.checkin_at is not None:
        raise HTTPException(status_code=400, detail="นิสิตเช็คอินกิจกรรมนี้แล้ว")

    now = get_unix_time()

    if not item:
        item = StudentActivity(
            student_id=student.student_id,
            activity_id=activity.activity_id,
            registered_at=None,
            created_by_id=admin.user_id,
            created_by_name=admin.name,
            created_at=now,
        )
        db.add(item)

    item.attendance_status = "เข้าร่วม"
    item.checkin_at = now
    item.checkin_status = "valid" if is_valid_checkin_time else "manual"
    item.earned_hours = calculate_earned_hours(activity, item)
    item.checkin_lat = body.checkin_lat
    item.checkin_lng = body.checkin_lng
    item.updated_by_id = admin.user_id
    item.updated_by_name = admin.name
    item.updated_at = now

    db.commit()
    db.refresh(item)

    return {
        "detail": "เช็คอินสำเร็จ",
        "data": build_student_activity_response(item, student, activity)
    }

@router.post("/admin/get-all", response_model=StudentActivityAdminListResponse)
def get_all_student_activities_admin(
    body: StudentActivityAdminSearchRequest,
    db: Session = Depends(get_db)
):
    page = max(body.page, 1)
    limit = max(body.limit, 1)
    offset = (page - 1) * limit

    query = (
        db.query(StudentActivity)
        .join(Student, Student.student_id == StudentActivity.student_id)
        .join(Activity, Activity.activity_id == StudentActivity.activity_id)
        .options(
            joinedload(StudentActivity.student),
            joinedload(StudentActivity.activity)
        )
    )

    if body.activity_id.strip() != "":
        query = query.filter(StudentActivity.activity_id == int(body.activity_id))

    if body.student_code.strip() != "":
        query = query.filter(Student.student_code.ilike(f"%{body.student_code.strip()}%"))

    if body.search.strip() != "":
        search_text = f"%{body.search.strip()}%"
        full_name = func.concat(Student.first_name, " ", Student.last_name)

        query = query.filter(
            or_(
                Student.student_code.ilike(search_text),
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
                full_name.ilike(search_text),
            )
        )

    if body.year_status.strip() != "":
        query = query.filter(Student.year_status == body.year_status.strip())

    if body.faculty_id.strip() != "":
        query = query.filter(Student.faculty_id == int(body.faculty_id))

    if body.major_id.strip() != "":
        query = query.filter(Student.major_id == int(body.major_id))

    total_all = query.count()

    items = (
        query
        .order_by(StudentActivity.student_activity_id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []

    for item in items:
        if item.student and item.activity:
            result.append(
                build_student_activity_response(
                    item,
                    item.student,
                    item.activity
                )
            )

    return {
        "detail": "ดึงข้อมูลนิสิตที่เข้าร่วมกิจกรรมสำเร็จ",
        "total_all": total_all,
        "page": page,
        "limit": limit,
        "data": result
    }


@router.post("/admin/get-allinone-last", response_model=StudentActivityAllInOneResponse)
def get_student_activity_all_in_one(
    body: StudentActivityAllInOneSearchRequest,
    db: Session = Depends(get_db)
):
    has_filter = any([
        body.search.strip() != "",
        body.student_code.strip() != "",
        body.year_status.strip() != "",
        body.faculty_id.strip() != "",
        body.major_id.strip() != "",
        body.hour_type.strip() != "",
    ])

    if not has_filter:
        return {
            "detail": "กรุณาระบุเงื่อนไขค้นหาก่อน",
            "data": None
        }

    query = (
        db.query(StudentActivity)
        .join(Student, Student.student_id == StudentActivity.student_id)
        .join(Activity, Activity.activity_id == StudentActivity.activity_id)
        .options(
            joinedload(StudentActivity.student),
            joinedload(StudentActivity.activity)
        )
    )

    if body.student_code.strip() != "":
        query = query.filter(Student.student_code.ilike(f"%{body.student_code.strip()}%"))

    if body.search.strip() != "":
        search_text = f"%{body.search.strip()}%"
        full_name = func.concat(Student.first_name, " ", Student.last_name)

        query = query.filter(
            or_(
                Student.student_code.ilike(search_text),
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
                full_name.ilike(search_text),
            )
        )

    if body.year_status.strip() != "":
        query = query.filter(Student.year_status == body.year_status.strip())

    if body.faculty_id.strip() != "":
        query = query.filter(Student.faculty_id == int(body.faculty_id))

    if body.major_id.strip() != "":
        query = query.filter(Student.major_id == int(body.major_id))

    if body.hour_type.strip() != "":
        query = query.filter(Activity.hour_type_id == body.hour_type.strip())

    items = (
        query
        .order_by(Student.student_code.asc(), Activity.activity_date.desc())
        .all()
    )

    student_map = {}

    for item in items:
        student = item.student
        activity = item.activity

        if not student or not activity:
            continue

        position_id = getattr(student, "position_id", None)
        position_name = getattr(student, "position_name", None)

        if position_name is None and hasattr(student, "position"):
            position_name = student.position.position_name if student.position else None

        if student.student_id not in student_map:
            student_map[student.student_id] = {
                "student_id": student.student_id,
                "student_code": student.student_code,
                "prefix": student.prefix,
                "full_name": f"{student.prefix or ''}{student.first_name} {student.last_name}",
                "first_name": student.first_name,
                "last_name": student.last_name,

                "position_id": position_id,
                "position_name": position_name,

                "faculty_id": student.faculty_id,
                "major_id": student.major_id,
                "year_status": student.year_status,
                "faculty_name": student.faculty_name,
                "major_name": student.major_name,

                "total_activity": 0,
                "total_hours": 0,
                "activity": []
            }

        student_map[student.student_id]["activity"].append({
            "student_activity_id": item.student_activity_id,
            "activity_id": activity.activity_id,
            "activity_name": activity.activity_name,
            "activity_date": activity.activity_date,
            "activity_time_text": format_activity_time_text(
                activity.start_time,
                activity.end_time,
                activity.hours
            ),
            "location": activity.location,
            "activity_img": activity.activity_img,
            "hours": activity.hours,
            "hour_type_id": str(activity.hour_type_id) if activity.hour_type_id else None,

            "check_type": activity.check_type,
            "require_registration": activity.require_registration,
            "max_participants": activity.max_participants,

            "attendance_status": item.attendance_status,
            "registered_at": item.registered_at,
            "checkin_at": item.checkin_at,
            "checkin_status": item.checkin_status,
            "checkin_status_text": get_scan_status_text(item.checkin_status, "ตรงเวลา", "มาสาย"),
            "checkout_at": item.checkout_at,
            "checkout_status": item.checkout_status,
            "checkout_status_text": get_scan_status_text(item.checkout_status, "ตรงเวลา", "เช็คเอาท์นอกเวลา"),
            "earned_hours": float(item.earned_hours or 0),
        })

        student_map[student.student_id]["total_activity"] += 1
        student_map[student.student_id]["total_hours"] += float(activity.hours or 0)

    data_list = list(student_map.values())
    data = data_list[0] if len(data_list) > 0 else None

    return {
        "detail": "ดึงข้อมูลกิจกรรมทั้งหมดของนิสิตสำเร็จ",
        "data": data
    }


@router.post("/admin/get-allinone", response_model=StudentActivityAllInOneResponse)
def get_student_activity_all_in_one(
    body: StudentActivityAllInOneSearchRequest,
    db: Session = Depends(get_db)
):
    has_filter = any([
        body.search.strip() != "",
        body.student_code.strip() != "",
        body.year_status.strip() != "",
        body.faculty_id.strip() != "",
        body.major_id.strip() != "",
        body.hour_type.strip() != "",
    ])

    if not has_filter:
        return {
            "detail": "กรุณาระบุเงื่อนไขค้นหาก่อน",
            "data": None
        }

    query = (
        db.query(Student, StudentPosition, Position, StudentActivity, Activity)
        .outerjoin(
            StudentPosition,
            and_(
                StudentPosition.student_id == Student.student_id,
                StudentPosition.is_current == True,
                StudentPosition.end_date.is_(None),
            )
        )
        .outerjoin(Position, Position.position_id == StudentPosition.position_id)
        .outerjoin(StudentActivity, StudentActivity.student_id == Student.student_id)
        .outerjoin(Activity, Activity.activity_id == StudentActivity.activity_id)
    )

    if body.student_code.strip() != "":
        query = query.filter(
            Student.student_code.ilike(f"%{body.student_code.strip()}%")
        )

    if body.search.strip() != "":
        search_text = f"%{body.search.strip()}%"
        full_name = func.concat(Student.first_name, " ", Student.last_name)

        query = query.filter(
            or_(
                Student.student_code.ilike(search_text),
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
                full_name.ilike(search_text),
            )
        )

    if body.year_status.strip() != "":
        query = query.filter(Student.year_status == body.year_status.strip())

    if body.faculty_id.strip() != "":
        query = query.filter(Student.faculty_id == int(body.faculty_id))

    if body.major_id.strip() != "":
        query = query.filter(Student.major_id == int(body.major_id))

    if body.hour_type.strip() != "":
        query = query.filter(Activity.hour_type_id == body.hour_type.strip())

    items = (
        query
        .order_by(Student.student_code.asc(), Activity.activity_date.desc().nullslast())
        .all()
    )

    if len(items) == 0:
        return {
            "detail": "ไม่พบนิสิต",
            "data": None
        }

    student_map = {}

    for student, student_position, position, student_activity, activity in items:
        if not student:
            continue

        if student.student_id not in student_map:
            student_map[student.student_id] = {
                "student_id": student.student_id,
                "student_code": student.student_code,
                "prefix": student.prefix,
                "full_name": f"{student.first_name} {student.last_name}",
                "first_name": student.first_name,
                "last_name": student.last_name,

                "position_id": position.position_id if position else None,
                "position_name": position.position_name if position else None,
                "student_position_id": student_position.student_position_id if student_position else None,
                "position_start_date": student_position.start_date if student_position else None,
                "position_end_date": student_position.end_date if student_position else None,

                "faculty_id": student.faculty_id,
                "major_id": student.major_id,
                "year_status": student.year_status,
                "faculty_name": student.faculty_name,
                "major_name": student.major_name,
                
                "total_activity": 0,
                # เวลากิจกรรมรวม
                "total_hours": 0,
                # ชั่วโมงจิตอาสารวม
                "total_volunteer_hours": 0,
                # ชั่วโมงจิตอาสาที่ได้จริงรวม
                "total_earned_hours": 0,
                "activity": []
            }

        if student_activity and activity:
            student_map[student.student_id]["activity"].append({
                "student_activity_id": student_activity.student_activity_id,
                "activity_id": activity.activity_id,
                "activity_name": activity.activity_name,
                "activity_date": activity.activity_date,
                "activity_time_text": format_activity_time_text(
                    activity.start_time,
                    activity.end_time,
                    activity.hours
                ),
                "location": activity.location,
                "activity_img": activity.activity_img,
                # เวลาเริ่มกิจกรรม
                "start_time": format_time_dot(activity.start_time),

                # เวลาจบกิจกรรม
                "end_time": format_time_dot(activity.end_time),

                # เวลากิจกรรมจริง
                "hours": float(activity.hours or 0),

                # ชั่วโมงจิตอาสาของกิจกรรม
                "volunteer_hours": float(activity.volunteer_hours or 0),

                # ชั่วโมงจิตอาสาที่ได้จริง
                "earned_hours": float(student_activity.earned_hours or 0),

                "hour_type_id": (
                    str(activity.hour_type_id)
                    if activity.hour_type_id
                    else None
                ),

                "check_type": activity.check_type,

                "require_registration": activity.require_registration,

                "max_participants": activity.max_participants,

                "check_detail": {
                    "attendance_status": student_activity.attendance_status,

                    "registered_at": student_activity.registered_at,

                    # ชั่วโมงจิตอาสาที่ได้จริง
                    "earned_hours": float(
                        student_activity.earned_hours or 0
                    ),

                    # ชั่วโมงจิตอาสาของกิจกรรม
                    "volunteer_hours": float(
                        activity.volunteer_hours or 0
                    ),

                    "checkin": {
                        "checkin_at": student_activity.checkin_at,

                        "checkin_status": student_activity.checkin_status,

                        "checkin_status_text": get_scan_status_text(
                            student_activity.checkin_status,
                            "ตรงเวลา",
                            "มาสาย"
                        ),

                        "checkin_lat": (
                            float(student_activity.checkin_lat)
                            if student_activity.checkin_lat is not None
                            else None
                        ),

                        "checkin_lng": (
                            float(student_activity.checkin_lng)
                            if student_activity.checkin_lng is not None
                            else None
                        ),
                    },

                    "checkout": {
                        "checkout_at": student_activity.checkout_at,

                        "checkout_status": student_activity.checkout_status,

                        "checkout_status_text": get_scan_status_text(
                            student_activity.checkout_status,
                            "ตรงเวลา",
                            "เช็คเอาท์นอกเวลา"
                        ),

                        "checkout_lat": (
                            float(student_activity.checkout_lat)
                            if student_activity.checkout_lat is not None
                            else None
                        ),

                        "checkout_lng": (
                            float(student_activity.checkout_lng)
                            if student_activity.checkout_lng is not None
                            else None
                        ),
                    },
                },
            })

            student_map[student.student_id]["total_activity"] += 1

            # เวลากิจกรรมรวม
            student_map[student.student_id]["total_hours"] += float(
                activity.hours or 0
            )

            # ชั่วโมงจิตอาสารวม
            student_map[student.student_id]["total_volunteer_hours"] += float(
                activity.volunteer_hours or 0
            )

            # ชั่วโมงจิตอาสาที่ได้จริงรวม
            student_map[student.student_id]["total_earned_hours"] += float(
                student_activity.earned_hours or 0
            )
    data_list = list(student_map.values())
    data = data_list[0] if len(data_list) > 0 else None

    return {
        "detail": "ดึงข้อมูลกิจกรรมทั้งหมดของนิสิตสำเร็จ",
        "data": data
    }
    
