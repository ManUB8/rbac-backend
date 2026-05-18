from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from math import radians, sin, cos, sqrt, atan2
import time as time_module
from sqlalchemy import func, or_

from database import get_db
from models import Student, Activity, StudentActivity, User
from schemas.schemas_student_activity import (
    StudentActivityRegisterRequest,
    StudentActivityCheckinRequest,
    StudentActivityCheckoutRequest,
    StudentActivityResponse,
    StudentActivityListResponse,
    StudentActivityUpdateRequest,
    StudentActivityDeleteResponse,
    StudentActivityDeleteRequest,
    StudentActivityUpdateRequest,
    StudentActivityAvailableListResponse,
    StudentActivityAdminSearchRequest,
    StudentActivityAdminListResponse,
    StudentActivityAllInOneSearchRequest,
    StudentActivityAllInOneResponse,
    
)

router = APIRouter(prefix="/student_activities/v1", tags=["Student Activities"])
DELETE_ALLOWED_ADMIN_NAMES = ["mangpo", "first", "soda","Tatum","Tum"]


def get_unix_time() -> int:
    return int(time_module.time())


def get_admin_by_name(db: Session, admin_name: str) -> User:
    admin = (
        db.query(User)
        .filter(
            User.name == admin_name,
            User.role == "admin",
            User.is_active == True
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=403,
            detail=f"ผู้ใช้นี้ไม่มีสิทธิ์แอดมินหรือไม่พบในระบบ: {admin_name}"
        )

    return admin


def get_delete_admin_by_name(db: Session, admin_name: str) -> User:
    admin = get_admin_by_name(db, admin_name)

    if admin.name not in DELETE_ALLOWED_ADMIN_NAMES:
        raise HTTPException(
            status_code=403,
            detail="แอดมินนี้ไม่มีสิทธิ์ลบนิสิต"
        )

    return admin

def format_time_short(time_obj):
    return time_obj.strftime("%H.%M")


def format_hours_text(hours):
    if hours is None:
        return "-"

    h = float(hours)
    if h.is_integer():
        return f"{int(h)} ชั่วโมง"

    return f"{h:g} ชั่วโมง"


def format_activity_time_text(start_time, end_time, hours):
    return f"{format_time_short(start_time)} - {format_time_short(end_time)} น. ({format_hours_text(hours)})"


def calculate_distance_meter(lat1, lng1, lat2, lng2):
    r = 6371000

    lat1 = radians(float(lat1))
    lng1 = radians(float(lng1))
    lat2 = radians(float(lat2))
    lng2 = radians(float(lng2))

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return r * c


def validate_activity_location(activity: Activity, lat: float, lng: float):
    if activity.activity_lat is None or activity.activity_lng is None:
        raise HTTPException(status_code=400, detail="กิจกรรมนี้ยังไม่ได้กำหนดพิกัด")

    radius = activity.activity_radius_meter or 100

    distance = calculate_distance_meter(
        lat,
        lng,
        activity.activity_lat,
        activity.activity_lng
    )

    if distance > radius:
        raise HTTPException(
            status_code=400,
            detail=f"อยู่นอกพื้นที่กิจกรรม ระยะห่างประมาณ {int(distance)} เมตร"
        )


def get_student_by_code(db: Session, student_code: str) -> Student:
    student = db.query(Student).filter(Student.student_code == student_code).first()

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนิสิต")

    return student


def get_activity_by_id(db: Session, activity_id: int) -> Activity:
    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    if activity.activity_status is not True:
        raise HTTPException(status_code=400, detail="กิจกรรมนี้ปิดใช้งานแล้ว")

    return activity


def build_student_activity_response(item: StudentActivity, student: Student, activity: Activity):
    return {
        "student_activity_id": item.student_activity_id,
        "student_id": student.student_id,
        "activity_id": activity.activity_id,
        "student_code": student.student_code,
        "full_name": f"{student.first_name} {student.last_name}",
        "faculty_name": student.faculty_name,
        "major_name": student.major_name,
        "year_status": student.year_status,
        "activity_name": activity.activity_name,
        "activity_date": activity.activity_date,
        "activity_time_text": format_activity_time_text(
            activity.start_time,
            activity.end_time,
            activity.hours
        ),
        "location": activity.location,

        "check_type": activity.check_type,
        "require_registration": activity.require_registration,
        "max_participants": activity.max_participants,

        "attendance_status": item.attendance_status,
        "registered_at": item.registered_at,
        "checkin_at": item.checkin_at,
        "checkout_at": item.checkout_at,

        "checkin_lat": float(item.checkin_lat) if item.checkin_lat is not None else None,
        "checkin_lng": float(item.checkin_lng) if item.checkin_lng is not None else None,
        "checkout_lat": float(item.checkout_lat) if item.checkout_lat is not None else None,
        "checkout_lng": float(item.checkout_lng) if item.checkout_lng is not None else None,

        "created_by_id": item.created_by_id,
        "created_by_name": item.created_by_name,
        "updated_by_id": item.updated_by_id,
        "updated_by_name": item.updated_by_name,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


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
    admin = get_admin_by_name(db, body.created_by_name)
    student = get_student_by_code(db, body.student_code)
    activity = get_activity_by_id(db, body.activity_id)

    validate_activity_location(activity, body.checkin_lat, body.checkin_lng)

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


@router.patch("/checkout", response_model=StudentActivityResponse)
def checkout_activity(
    body: StudentActivityCheckoutRequest,
    db: Session = Depends(get_db)
):
    admin = get_admin_by_name(db, body.updated_by_name)
    student = get_student_by_code(db, body.student_code)
    activity = get_activity_by_id(db, body.activity_id)

    if activity.check_type != "checkin_checkout":
        raise HTTPException(status_code=400, detail="กิจกรรมนี้เป็นแบบเช็คอินอย่างเดียว ไม่ต้องเช็คเอาท์")

    validate_activity_location(activity, body.checkout_lat, body.checkout_lng)

    item = (
        db.query(StudentActivity)
        .options(joinedload(StudentActivity.student), joinedload(StudentActivity.activity))
        .filter(
            StudentActivity.student_id == student.student_id,
            StudentActivity.activity_id == activity.activity_id
        )
        .first()
    )
    
    if activity.require_registration and not item:
        raise HTTPException(status_code=400, detail="กิจกรรมนี้ต้องลงทะเบียนก่อนเช็คเอาท์")

    if not item:
        raise HTTPException(status_code=400, detail="ต้องเช็คอินก่อน จึงจะเช็คเอาท์ได้")

    if item.checkin_at is None:
        raise HTTPException(status_code=400, detail="ต้องเช็คอินก่อน จึงจะเช็คเอาท์ได้")

    if item.checkout_at is not None:
        raise HTTPException(status_code=400, detail="นิสิตเช็คเอาท์กิจกรรมนี้แล้ว")

    now = get_unix_time()

    item.checkout_at = now
    item.checkout_lat = body.checkout_lat
    item.checkout_lng = body.checkout_lng
    item.updated_by_id = admin.user_id
    item.updated_by_name = admin.name
    item.updated_at = now

    db.commit()
    db.refresh(item)

    return {
        "detail": "เช็คเอาท์สำเร็จ",
        "data": build_student_activity_response(item, student, activity)
    }

@router.get("/get-all/", response_model=StudentActivityListResponse)
def get_all_student_activities(db: Session = Depends(get_db)):
    items = (
        db.query(StudentActivity)
        .options(joinedload(StudentActivity.student), joinedload(StudentActivity.activity))
        .order_by(StudentActivity.student_activity_id.desc())
        .all()
    )

    result = []
    for item in items:
        if item.student and item.activity:
            result.append(build_student_activity_response(item, item.student, item.activity))

    return {
        "detail": "ดึงข้อมูลการเข้าร่วมกิจกรรมทั้งหมดสำเร็จ",
        "data": result
    }


@router.get("/get-one/{student_activity_id}", response_model=StudentActivityResponse)
def get_student_activity(student_activity_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(StudentActivity)
        .options(joinedload(StudentActivity.student), joinedload(StudentActivity.activity))
        .filter(StudentActivity.student_activity_id == student_activity_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการเข้าร่วมกิจกรรม")

    return {
        "detail": "ดึงข้อมูลการเข้าร่วมกิจกรรมสำเร็จ",
        "data": build_student_activity_response(item, item.student, item.activity)
    }


@router.patch("/update/{student_activity_id}", response_model=StudentActivityResponse)
def update_student_activity(
    student_activity_id: int,
    body: StudentActivityUpdateRequest,
    db: Session = Depends(get_db)
):
    if student_activity_id != body.student_activity_id:
        raise HTTPException(
            status_code=400,
            detail="student_activity_id ใน URL และ body ไม่ตรงกัน"
        )

    admin = get_admin_by_name(db, body.updated_by_name)

    item = (
        db.query(StudentActivity)
        .options(
            joinedload(StudentActivity.student),
            joinedload(StudentActivity.activity)
        )
        .filter(StudentActivity.student_activity_id == student_activity_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการเข้าร่วมกิจกรรม")

    student = item.student
    activity = item.activity

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนิสิต")

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    if body.activity_id is not None:
        new_activity = (
            db.query(Activity)
            .filter(Activity.activity_id == body.activity_id)
            .first()
        )

        if not new_activity:
            raise HTTPException(status_code=404, detail="ไม่พบกิจกรรมใหม่")

        duplicate = (
            db.query(StudentActivity)
            .filter(
                StudentActivity.student_id == item.student_id,
                StudentActivity.activity_id == new_activity.activity_id,
                StudentActivity.student_activity_id != item.student_activity_id
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="นิสิตคนนี้มีข้อมูลกิจกรรมนี้อยู่แล้ว"
            )

        item.activity_id = new_activity.activity_id
        activity = new_activity

    if body.attendance_status is not None:
        if body.attendance_status not in ["เข้าร่วม", "ไม่เข้าร่วม"]:
            raise HTTPException(
                status_code=400,
                detail="attendance_status ต้องเป็น 'เข้าร่วม' หรือ 'ไม่เข้าร่วม'"
            )

        now = get_unix_time()
        item.attendance_status = body.attendance_status

        if body.attendance_status == "ไม่เข้าร่วม":
            item.checkin_at = None
            item.checkout_at = None
            item.checkin_lat = None
            item.checkin_lng = None
            item.checkout_lat = None
            item.checkout_lng = None

        if body.attendance_status == "เข้าร่วม":
            if activity.check_type == "checkin_only":
                item.checkin_at = item.checkin_at or now
                item.checkout_at = None

            elif activity.check_type == "checkout_only":
                item.checkout_at = item.checkout_at or now
                item.checkin_at = None

            elif activity.check_type == "checkin_checkout":
                item.checkin_at = item.checkin_at or now
                item.checkout_at = item.checkout_at or now

            else:
                raise HTTPException(
                    status_code=400,
                    detail="check_type ไม่ถูกต้อง"
                )

    item.updated_by_id = admin.user_id
    item.updated_by_name = admin.name
    item.updated_at = get_unix_time()

    db.commit()
    db.refresh(item)

    return {
        "detail": "แก้ไขข้อมูลการเข้าร่วมกิจกรรมสำเร็จ",
        "data": build_student_activity_response(item, student, activity)
    }
    

@router.delete(
    "/delete/{student_activity_id}",
    response_model=StudentActivityDeleteResponse
)
def delete_student_activity(
    student_activity_id: int,
    body: StudentActivityDeleteRequest,
    db: Session = Depends(get_db)
):
    if student_activity_id != body.student_activity_id:
        raise HTTPException(
            status_code=400,
            detail="student_activity_id ใน URL และ body ไม่ตรงกัน"
        )

    admin = get_delete_admin_by_name(db, body.updated_by_name)

    item = (
        db.query(StudentActivity)
        .filter(StudentActivity.student_activity_id == student_activity_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบข้อมูลการเข้าร่วมกิจกรรม"
        )

    deleted_id = item.student_activity_id

    db.delete(item)
    db.commit()

    return {
        "detail": f"แอดมิน {admin.name} ลบข้อมูลการเข้าร่วมกิจกรรมสำเร็จ",
        "student_activity_id": deleted_id,
        "updated_by_id": admin.user_id,
        "updated_by_name": admin.name,
    }
    
    
@router.get("/student/available/{student_code}", response_model=StudentActivityAvailableListResponse)
def get_available_activities_for_student(
    student_code: str,
    db: Session = Depends(get_db)
):
    student = get_student_by_code(db, student_code)

    activities = (
        db.query(Activity)
        .filter(Activity.activity_status == True)
        .order_by(Activity.activity_id.desc())
        .all()
    )

    result = []

    for activity in activities:
        registered_count = (
            db.query(func.count(StudentActivity.student_activity_id))
            .filter(StudentActivity.activity_id == activity.activity_id)
            .scalar()
            or 0
        )

        existing = (
            db.query(StudentActivity)
            .filter(
                StudentActivity.student_id == student.student_id,
                StudentActivity.activity_id == activity.activity_id
            )
            .first()
        )

        is_registered = existing is not None

        is_full = False
        if activity.max_participants is not None:
            is_full = registered_count >= activity.max_participants

        register_text = None
        if activity.require_registration:
            register_text = f"{registered_count}/{activity.max_participants or 0}"

        if activity.require_registration:
            if is_registered:
                button_text = "ลงทะเบียนแล้ว"
                button_status = "registered"
            elif is_full:
                button_text = "ลงทะเบียนเต็มแล้ว"
                button_status = "full"
            else:
                button_text = "ลงทะเบียน"
                button_status = "can_register"
        else:
            button_text = "เข้าร่วมได้เลย"
            button_status = "can_join"

        result.append({
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

            "check_type": activity.check_type,
            "require_registration": activity.require_registration,
            "max_participants": activity.max_participants,

            "registered_count": registered_count,
            "register_text": register_text,
            "is_registered": is_registered,
            "is_full": is_full,

            "button_text": button_text,
            "button_status": button_status,
        })

    return {
        "detail": "ดึงข้อมูลกิจกรรมสำหรับนิสิตสำเร็จ",
        "student_code": student_code,
        "data": result
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

    if body.activity_id != "":
        query = query.filter(StudentActivity.activity_id == int(body.activity_id))

    if body.student_code != "":
        query = query.filter(Student.student_code.ilike(f"%{body.student_code}%"))

    if body.search != "":
        search_text = f"%{body.search}%"
        full_name = func.concat(Student.first_name, " ", Student.last_name)

        query = query.filter(
            or_(
                Student.student_code.ilike(search_text),
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
                full_name.ilike(search_text),
            )
        )

    if body.year_status != "":
        query = query.filter(Student.year_status == int(body.year_status))

    if body.faculty_id != "":
        query = query.filter(Student.faculty_id == int(body.faculty_id))

    if body.major_id != "":
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
            "total_all": 0,
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

    if body.student_code != "":
        query = query.filter(Student.student_code.ilike(f"%{body.student_code}%"))

    if body.search != "":
        search_text = f"%{body.search}%"
        full_name = func.concat(Student.first_name, " ", Student.last_name)

        query = query.filter(
            or_(
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
                full_name.ilike(search_text),
            )
        )

    if body.year_status != "":
        query = query.filter(Student.year_status == body.year_status)

    if body.faculty_id != "":
        query = query.filter(Student.faculty_id == int(body.faculty_id))

    if body.major_id != "":
        query = query.filter(Student.major_id == int(body.major_id))

    if body.hour_type != "":
        query = query.filter(Activity.hour_type_id == body.hour_type)

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

        if student.student_id not in student_map:
            student_map[student.student_id] = {
            "student_id": student.student_id,
            "student_code": student.student_code,
            "full_name": f"{student.first_name} {student.last_name}",
            "first_name": student.first_name,
            "last_name": student.last_name,
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
            "checkout_at": item.checkout_at,
        })

        student_map[student.student_id]["total_activity"] += 1
        student_map[student.student_id]["total_hours"] += float(activity.hours or 0)

    data_list = list(student_map.values())
    data = data_list[0] if len(data_list) > 0 else None

    return {
        "detail": "ดึงข้อมูลกิจกรรมทั้งหมดของนิสิตสำเร็จ",
        "total_all": len(data),
        "data": data
    }