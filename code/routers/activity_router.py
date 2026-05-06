from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import time, datetime
import time as time_module

from database import SessionLocal
from models import Activity, User
from schemas.schemas_activity import (
    ActivityCreateRequest,
    ActivityUpdateRequest,
    ActivityDeleteRequest,
    ActivityResponse,
    ActivityMessageResponse,
    ActivityDeleteResponse,
)

router = APIRouter(prefix="/activity/v1", tags=["Activity"])


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


def validate_activity_data(data):
    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด")

    if data.max_participants is not None and data.max_participants <= 0:
        raise HTTPException(status_code=400, detail="max_participants ต้องมากกว่า 0")

    if data.activity_radius_meter is not None and data.activity_radius_meter <= 0:
        raise HTTPException(status_code=400, detail="activity_radius_meter ต้องมากกว่า 0")

    if data.activity_lat is not None and not (-90 <= data.activity_lat <= 90):
        raise HTTPException(status_code=400, detail="activity_lat ไม่ถูกต้อง")

    if data.activity_lng is not None and not (-180 <= data.activity_lng <= 180):
        raise HTTPException(status_code=400, detail="activity_lng ไม่ถูกต้อง")


@router.post("/create", response_model=ActivityMessageResponse)
def create_activity(data: ActivityCreateRequest, db: Session = Depends(get_db)):
    admin = get_admin_by_name(db, data.created_by_name)

    validate_activity_data(data)

    now = get_unix_time()

    activity = Activity(
        activity_name=data.activity_name,
        activity_date=data.activity_date,
        start_time=data.start_time,
        end_time=data.end_time,
        hours=data.hours,
        location=data.location,
        description=data.description,
        activity_img=data.activity_img,
        activity_status=data.activity_status,

        check_type=data.check_type,
        require_registration=data.require_registration,
        max_participants=data.max_participants,
        activity_lat=data.activity_lat,
        activity_lng=data.activity_lng,
        activity_radius_meter=data.activity_radius_meter,

        created_by_id=admin.user_id,
        created_by_name=admin.name,
        updated_by_id=admin.user_id,
        updated_by_name=admin.name,
        created_at=now,
        updated_at=now,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return {"detail": "สร้างกิจกรรมสำเร็จ", "data": activity}


@router.get("/get-all", response_model=list[ActivityResponse])
def get_all_active_activities(db: Session = Depends(get_db)):
    return (
        db.query(Activity)
        .filter(Activity.activity_status == True)
        .order_by(Activity.activity_id.desc())
        .all()
    )


@router.get("/admin/get-all", response_model=list[ActivityResponse])
def get_all_activities_admin(db: Session = Depends(get_db)):
    return (
        db.query(Activity)
        .order_by(Activity.activity_id.desc())
        .all()
    )


@router.get("/get-one/{activity_id}", response_model=ActivityResponse)
def get_activity_by_id(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    return activity


@router.patch("/update/{activity_id}", response_model=ActivityMessageResponse)
def update_activity(activity_id: int, data: ActivityUpdateRequest, db: Session = Depends(get_db)):
    if activity_id != data.activity_id:
        raise HTTPException(status_code=400, detail="activity_id ไม่ตรงกัน")

    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    admin = get_admin_by_name(db, data.updated_by_name)

    update_data = data.model_dump(exclude_unset=True)

    new_start_time = update_data.get("start_time", activity.start_time)
    new_end_time = update_data.get("end_time", activity.end_time)

    if new_start_time >= new_end_time:
        raise HTTPException(status_code=400, detail="เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด")

    new_max_participants = update_data.get("max_participants", activity.max_participants)
    if new_max_participants is not None and new_max_participants <= 0:
        raise HTTPException(status_code=400, detail="max_participants ต้องมากกว่า 0")

    new_radius = update_data.get("activity_radius_meter", activity.activity_radius_meter)
    if new_radius is not None and new_radius <= 0:
        raise HTTPException(status_code=400, detail="activity_radius_meter ต้องมากกว่า 0")

    new_lat = update_data.get("activity_lat", activity.activity_lat)
    if new_lat is not None and not (-90 <= float(new_lat) <= 90):
        raise HTTPException(status_code=400, detail="activity_lat ไม่ถูกต้อง")

    new_lng = update_data.get("activity_lng", activity.activity_lng)
    if new_lng is not None and not (-180 <= float(new_lng) <= 180):
        raise HTTPException(status_code=400, detail="activity_lng ไม่ถูกต้อง")

    for key, value in update_data.items():
        if key not in ["updated_by_name", "activity_id"]:
            setattr(activity, key, value)

    activity.updated_by_id = admin.user_id
    activity.updated_by_name = admin.name
    activity.updated_at = get_unix_time()

    db.commit()
    db.refresh(activity)

    return {"detail": "แก้ไขกิจกรรมสำเร็จ", "data": activity}


@router.delete("/delete/{activity_id}", response_model=ActivityDeleteResponse)
def delete_activity(activity_id: int, data: ActivityDeleteRequest, db: Session = Depends(get_db)):
    if activity_id != data.activity_id:
        raise HTTPException(status_code=400, detail="activity_id ไม่ตรงกัน")

    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    admin = get_admin_by_name(db, data.updated_by_name)

    activity.activity_status = False
    activity.updated_by_id = admin.user_id
    activity.updated_by_name = admin.name
    activity.updated_at = get_unix_time()

    db.commit()
    db.refresh(activity)

    return {
        "detail": f"แอดมิน {admin.name} ลบกิจกรรมสำเร็จ",
        "activity_id": activity.activity_id,
        "activity_status": activity.activity_status,
        "updated_by_id": activity.updated_by_id,
        "updated_by_name": activity.updated_by_name,
    }