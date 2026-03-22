from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import time as time_module
from datetime import datetime

from database import get_db
from models import Student, Activity, StudentActivity, User
from schemas.schemas_student_activity import (
    StudentActivityCreateRequest,
    StudentActivityUpdateRequest,
    StudentActivityDeleteRequest,
    StudentActivityResponse,
    StudentActivityListResponse,
    StudentActivityDeleteResponse,
)

router = APIRouter(prefix="/student_activities/v1", tags=["Student Activities"])


THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]


def get_unix_time() -> int:
    return int(time_module.time())


def get_admin_by_name(db: Session, name: str) -> User:
    admin = (
        db.query(User)
        .filter(
            User.name == name,
            User.role == "admin",
            User.is_active == True
        )
        .first()
    )
    if not admin:
        raise HTTPException(status_code=403, detail=f"ผู้ใช้นี้ไม่มีสิทธิ์ admin: {name}")
    return admin


def format_time_short(time_obj):
    return time_obj.strftime("%H.%M")


def format_hours_text(hours):
    if hours is None:
        return "-"
    hours_float = float(hours)
    if hours_float.is_integer():
        return f"{int(hours_float)} ชั่วโมง"
    return f"{hours_float:g} ชั่วโมง"


def format_activity_time_text(start_time, end_time, hours):
    return f"{format_time_short(start_time)} - {format_time_short(end_time)} น. ({format_hours_text(hours)})"


def format_registered_at_thai(ts):
    if ts is None:
        return None

    dt = datetime.fromtimestamp(ts)
    day = dt.day
    month = THAI_MONTHS[dt.month]
    year = dt.year + 543
    time_text = dt.strftime("%H:%M:%S")

    return f"ลงทะเบียนเมื่อ {day} {month} {year} เวลา {time_text}"


def build_student_activity_response(item: StudentActivity, student: Student, activity: Activity):
    registered_time = item.created_at

    return {
        "student_activity_id": item.student_activity_id,
        "student_id": student.student_id,
        "activity_id": activity.activity_id,
        "student_code": student.student_code,
        "full_name": f"{student.first_name} {student.last_name}",
        "activity_name": activity.activity_name,
        "activity_date": activity.activity_date,
        "activity_time_text": format_activity_time_text(
            activity.start_time,
            activity.end_time,
            activity.hours
        ),
        "location": activity.location,
        "attendance_status": item.attendance_status,
        "registered_at": registered_time,
        "registered_at_text": format_registered_at_thai(registered_time),
        "checkin_at": item.checkin_at,
        "created_by_id": item.created_by_id,
        "created_by_name": item.created_by_name,
        "updated_by_id": item.updated_by_id,
        "updated_by_name": item.updated_by_name,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.post("/create", response_model=StudentActivityResponse)
def create_student_activity(body: StudentActivityCreateRequest, db: Session = Depends(get_db)):
    admin = get_admin_by_name(db, body.created_by_name)

    student = db.query(Student).filter(Student.student_code == body.student_code).first()
    if not student:
        raise HTTPException(status_code=500, detail="ไม่พบนิสิต")

    activity = db.query(Activity).filter(Activity.activity_id == body.activity_id).first()
    if not activity:
        raise HTTPException(status_code=500, detail="ไม่พบกิจกรรม")

    existing = (
        db.query(StudentActivity)
        .filter(
            StudentActivity.student_id == student.student_id,
            StudentActivity.activity_id == activity.activity_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=500, detail="นิสิตลงทะเบียนกิจกรรมนี้แล้ว")

    now = get_unix_time()

    new_item = StudentActivity(
        student_id=student.student_id,
        activity_id=activity.activity_id,
        attendance_status="เข้าร่วม",
        checkin_at=now,
        created_by_id=admin.user_id,
        created_by_name=admin.name,
        updated_by_id=admin.user_id,
        updated_by_name=admin.name,
        created_at=now,
        updated_at=now,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {
        "detail": "ลงทะเบียนเข้าร่วมกิจกรรมเรียบร้อยแล้ว",
        "data": build_student_activity_response(new_item, student, activity)
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
def update_student_activity(student_activity_id: int, body: StudentActivityUpdateRequest, db: Session = Depends(get_db)):
    if student_activity_id != body.student_activity_id:
        raise HTTPException(status_code=500, detail="student_activity_id ใน URL และ body ไม่ตรงกัน")

    admin = get_admin_by_name(db, body.updated_by_name)

    item = db.query(StudentActivity).filter(
        StudentActivity.student_activity_id == student_activity_id
    ).first()

    if not item:
        raise HTTPException(status_code=500, detail="ไม่พบข้อมูลการเข้าร่วมกิจกรรม")

    student = db.query(Student).filter(Student.student_id == item.student_id).first()
    if not student:
        raise HTTPException(status_code=500, detail="ไม่พบนิสิต")

    activity = db.query(Activity).filter(Activity.activity_id == item.activity_id).first()
    if not activity:
        raise HTTPException(status_code=500, detail="ไม่พบกิจกรรม")

    if body.student_id is not None:
        new_student = db.query(Student).filter(Student.student_id == body.student_id).first()
        if not new_student:
            raise HTTPException(status_code=500, detail="ไม่พบนิสิตจากรหัสใหม่")
        item.student_id = new_student.student_id
        student = new_student

    if body.activity_id is not None:
        new_activity = db.query(Activity).filter(Activity.activity_id == body.activity_id).first()
        if not new_activity:
            raise HTTPException(status_code=500, detail="ไม่พบกิจกรรมใหม่")
        item.activity_id = new_activity.activity_id
        activity = new_activity

    if body.attendance_status is not None:
        if body.attendance_status not in ["เข้าร่วม", "ไม่เข้าร่วม"]:
            raise HTTPException(status_code=500, detail="attendance_status ต้องเป็น 'เข้าร่วม' หรือ 'ไม่เข้าร่วม'")
        item.attendance_status = body.attendance_status
        item.checkin_at = get_unix_time() if body.attendance_status == "เข้าร่วม" else None

    duplicate = (
        db.query(StudentActivity)
        .filter(
            StudentActivity.student_id == item.student_id,
            StudentActivity.activity_id == item.activity_id,
            StudentActivity.student_activity_id != item.student_activity_id
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=500, detail="มีข้อมูลนิสิตและกิจกรรมนี้อยู่แล้ว")

    item.updated_by_id = admin.user_id
    item.updated_by_name = admin.name
    item.updated_at = get_unix_time()

    db.commit()
    db.refresh(item)

    return {
        "detail": "แก้ไขข้อมูลการเข้าร่วมกิจกรรมสำเร็จ",
        "data": build_student_activity_response(item, student, activity)
    }


@router.delete("/delete/{student_activity_id}", response_model=StudentActivityDeleteResponse)
def delete_student_activity(student_activity_id: int, body: StudentActivityDeleteRequest, db: Session = Depends(get_db)):
    if student_activity_id != body.student_activity_id:
        raise HTTPException(status_code=500, detail="student_activity_id ใน URL และ body ไม่ตรงกัน")

    admin = get_admin_by_name(db, body.updated_by_name)

    item = db.query(StudentActivity).filter(
        StudentActivity.student_activity_id == student_activity_id
    ).first()

    if not item:
        raise HTTPException(status_code=500, detail="ไม่พบข้อมูลการเข้าร่วมกิจกรรม")

    deleted_id = item.student_activity_id
    db.delete(item)
    db.commit()

    return {
        "detail": "ลบข้อมูลการเข้าร่วมกิจกรรมสำเร็จ",
        "student_activity_id": deleted_id,
        "updated_by_id": admin.user_id,
        "updated_by_name": admin.name,
    }