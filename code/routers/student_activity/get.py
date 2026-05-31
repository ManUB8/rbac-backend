from fastapi import APIRouter, Depends, HTTPException
from .helpers import build_student_activity_response,get_student_by_code ,format_activity_time_text, get_scan_status_text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from database import get_db
from models import Student, Activity, StudentActivity
from schemas.schemas_student_activity import (
    StudentActivityResponse,
    StudentActivityListResponse,
    StudentActivityAvailableListResponse
)

router = APIRouter()

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

@router.get("/student/available/{student_code}",response_model=StudentActivityAvailableListResponse)
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

        # button status
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

            
            "checkin_open_time": activity.checkin_open_time,
            "checkin_close_time": activity.checkin_close_time,
            "checkout_open_time": activity.checkout_open_time,
            "checkout_close_time": activity.checkout_close_time,

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