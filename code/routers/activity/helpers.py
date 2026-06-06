import time as time_module

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User


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


def get_delete_admin_by_name(db: Session, admin_name: str) -> User:
    admin = get_admin_by_name(db, admin_name)

    if admin.name not in DELETE_ALLOWED_ADMIN_NAMES:
        raise HTTPException(
            status_code=403,
            detail="แอดมินนี้ไม่มีสิทธิ์ลบนิสิต"
        )

    return admin

TARGET_GROUP_LIST = ["all", "freshman", "senior"]


def validate_target_group(target_group: str):
    if target_group not in TARGET_GROUP_LIST:
        raise HTTPException(status_code=400, detail="กลุ่มผู้เข้าร่วมไม่ถูกต้อง")


def validate_activity_data(data):
    validate_target_group(data.target_group)

    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด")

    if (
        data.checkin_open_time is not None
        and data.checkin_close_time is not None
        and data.checkin_open_time >= data.checkin_close_time
    ):
        raise HTTPException(status_code=400, detail="เวลาเปิดเช็คอินต้องน้อยกว่าเวลาปิดเช็คอิน")

    if (
        data.checkout_open_time is not None
        and data.checkout_close_time is not None
        and data.checkout_open_time >= data.checkout_close_time
    ):
        raise HTTPException(status_code=400, detail="เวลาเปิดเช็คเอาท์ต้องน้อยกว่าเวลาปิดเช็คเอาท์")

    if data.max_participants is not None and data.max_participants <= 0:
        raise HTTPException(status_code=400, detail="max_participants ต้องมากกว่า 0")

    if data.activity_radius_meter is not None and data.activity_radius_meter <= 0:
        raise HTTPException(status_code=400, detail="activity_radius_meter ต้องมากกว่า 0")

    if data.activity_lat is not None and not (-90 <= float(data.activity_lat) <= 90):
        raise HTTPException(status_code=400, detail="activity_lat ไม่ถูกต้อง")

    if data.activity_lng is not None and not (-180 <= float(data.activity_lng) <= 180):
        raise HTTPException(status_code=400, detail="activity_lng ไม่ถูกต้อง")
