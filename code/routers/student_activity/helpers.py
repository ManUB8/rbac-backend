from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
import time as time_module
from database import get_db, SessionLocal

from models import Student, Activity, StudentActivity, User
DELETE_ALLOWED_ADMIN_NAMES = ["mangpo", "first", "soda", "Tatum", "Tum"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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


def get_scan_admin_by_name(db: Session, admin_name: str) -> User:
    admin = (
        db.query(User)
        .filter(
            User.name == admin_name,
            User.role.in_(["admin", "temporary_admin"]),
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


def get_time_window_status(open_time, close_time, current_time) -> str:

    if open_time is None or close_time is None:
        return "invalid"

    if current_time < open_time:
        return "not_started"

    if current_time > close_time:
        return "closed"

    return "valid"


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


def format_time_dot(value):
    if value is None:
        return ""
    return value.strftime("%H.%M")
    
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


def is_time_in_window(open_time, close_time, current_time) -> bool:
    if open_time is None or close_time is None:
        return False

    return open_time <= current_time <= close_time


def calculate_earned_hours(activity, item):
    volunteer_hours = float(activity.volunteer_hours or 0)

    if activity.check_type == "checkin_only":
        return volunteer_hours if item.checkin_status == "valid" else 0

    if activity.check_type == "checkin_checkout":
        valid_count = 0

        if item.checkin_status == "valid":
            valid_count += 1

        if item.checkout_status == "valid":
            valid_count += 1

        if valid_count == 2:
            return volunteer_hours

        if valid_count == 1:
            return volunteer_hours / 2

        return 0

    if activity.check_type == "checkout_only":
        return volunteer_hours if item.checkout_status == "valid" else 0

    return 0


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


def get_scan_status_text(status, valid_text: str, manual_text: str):
    if status == "valid":
        return valid_text

    if status == "manual":
        return manual_text

    return None


def build_student_activity_response(
    item: StudentActivity,
    student: Student,
    activity: Activity
):
    volunteer_hours = float(activity.volunteer_hours or 0)

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
        # เวลากิจกรรมจริง
        "hours": float(activity.hours or 0),
        # ชั่วโมงจิตอาสาของกิจกรรม
        "volunteer_hours": volunteer_hours,
        "check_detail": {
            "attendance_status": item.attendance_status,
            "registered_at": item.registered_at,
            # ชั่วโมงจิตอาสาที่ได้จริง
            "earned_hours": float(item.earned_hours or 0),
            # ชั่วโมงจิตอาสาของกิจกรรม
            "volunteer_hours": volunteer_hours,
            "checkin": {
                "checkin_at": item.checkin_at,
                "checkin_status": item.checkin_status,
                "checkin_status_text": get_scan_status_text(
                    item.checkin_status,
                    "ตรงเวลา",
                    "มาสาย"
                ),
                "checkin_lat": (
                    float(item.checkin_lat)
                    if item.checkin_lat is not None
                    else None
                ),

                "checkin_lng": (
                    float(item.checkin_lng)
                    if item.checkin_lng is not None
                    else None
                ),
            },

            "checkout": {
                "checkout_at": item.checkout_at,
                "checkout_status": item.checkout_status,
                "checkout_status_text": get_scan_status_text(
                    item.checkout_status,
                    "ตรงเวลา",
                    "เช็คเอาท์นอกเวลา"
                ),
                "checkout_lat": (
                    float(item.checkout_lat)
                    if item.checkout_lat is not None
                    else None
                ),
                "checkout_lng": (
                    float(item.checkout_lng)
                    if item.checkout_lng is not None
                    else None
                ),
            },
        },

        "created_by_id": item.created_by_id,
        "created_by_name": item.created_by_name,
        "updated_by_id": item.updated_by_id,
        "updated_by_name": item.updated_by_name,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }