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
    get_admin_by_name,
    validate_student_target_group,
)
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from datetime import datetime
from zoneinfo import ZoneInfo
from database import get_db
from models import  Activity, StudentActivity
from schemas.schemas_student_activity import (
    StudentActivityCheckoutRequest,
    StudentActivityResponse,
    StudentActivityUpdateRequest,
    StudentActivityUpdateRequest
)

router = APIRouter()


@router.patch("/checkout", response_model=StudentActivityResponse)
def checkout_activity(
    body: StudentActivityCheckoutRequest,
    db: Session = Depends(get_db)
):
    admin = get_scan_admin_by_name(db, body.updated_by_name)
    student = get_student_by_code(db, body.student_code)
    activity = get_activity_by_id(db, body.activity_id)
    validate_student_target_group(student, activity)

    if activity.check_type not in ["checkout_only", "checkin_checkout"]:
        raise HTTPException(status_code=400, detail="กิจกรรมนี้ไม่รองรับการเช็คเอาท์")

    validate_activity_location(activity, body.checkout_lat, body.checkout_lng)

    # current_time = datetime.now().time()
    current_time = datetime.now(ZoneInfo("Asia/Bangkok")).time()
    # is_valid_checkout_time = is_time_in_window(
    #     activity.checkout_open_time,
    #     activity.checkout_close_time,
    #     current_time
    # )
    checkout_time_status = get_time_window_status(
        activity.checkout_open_time,
        activity.checkout_close_time,
        current_time
    )

    is_valid_checkout_time = checkout_time_status == "valid"

    if admin.role == "temporary_admin":
        if checkout_time_status == "not_started":
            raise HTTPException(
                status_code=403,
                detail="ยังไม่ถึงเวลาเช็คเอาท์"
            )

        if checkout_time_status == "closed":
            raise HTTPException(
                status_code=403,
                detail="หมดเวลาลงทะเบียนเช็คเอาท์แล้ว"
            )

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

    if not item and activity.check_type == "checkin_checkout":
        raise HTTPException(status_code=400, detail="ต้องเช็คอินก่อน จึงจะเช็คเอาท์ได้")

    if not item and activity.check_type == "checkout_only":
        now = get_unix_time()
        item = StudentActivity(
            student_id=student.student_id,
            activity_id=activity.activity_id,
            registered_at=None,
            created_by_id=admin.user_id,
            created_by_name=admin.name,
            created_at=now,
        )
        db.add(item)

    if activity.check_type == "checkin_checkout" and item.checkin_at is None:
        raise HTTPException(status_code=400, detail="ต้องเช็คอินก่อน จึงจะเช็คเอาท์ได้")

    if item.checkout_at is not None:
        raise HTTPException(status_code=400, detail="นิสิตเช็คเอาท์กิจกรรมนี้แล้ว")

    now = get_unix_time()

    item.attendance_status = "เข้าร่วม"
    item.checkout_at = now
    item.checkout_status = "valid" if is_valid_checkout_time else "manual"
    item.earned_hours = calculate_earned_hours(activity, item)
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

        validate_student_target_group(student, new_activity)

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
    
