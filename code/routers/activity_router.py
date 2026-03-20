from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Activity
from schemas import (
    ActivityCreateRequest,
    ActivityUpdateRequest,
    ActivityResponse,
    ActivityMessageResponse,
    ActivityDeleteResponse,
)

router = APIRouter(prefix="/activity/v1", tags=["Activity"])


def get_db():
    """
    เปิด/ปิด database session ให้แต่ละ request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/create", response_model=ActivityMessageResponse)
def create_activity(data: ActivityCreateRequest, db: Session = Depends(get_db)):
    """
    สร้างกิจกรรมใหม่
    """

    # ตรวจสอบว่าเวลาเริ่มต้องน้อยกว่าเวลาจบ
    if data.start_time >= data.end_time:
        raise HTTPException(
            status_code=400,
            detail="start_time must be earlier than end_time"
        )

    activity = Activity(
        activity_name=data.activity_name,
        activity_date=data.activity_date,
        start_time=data.start_time,
        end_time=data.end_time,
        hours=data.hours,
        location=data.location,
        description=data.description,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return {
    "detail": "สร้างกิจกรรมสำเร็จ",
    "data": activity
}

@router.get("/all", response_model=list[ActivityResponse])
def get_all_activities(db: Session = Depends(get_db)):
    """
    ดึงกิจกรรมทั้งหมด
    """
    activities = db.query(Activity).order_by(Activity.id.desc()).all()
    return activities


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity_by_id(activity_id: int, db: Session = Depends(get_db)):
    """
    ดึงกิจกรรมตาม id
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    return activity


@router.patch("/{activity_id}", response_model=ActivityMessageResponse)
def update_activity(activity_id: int, data: ActivityUpdateRequest, db: Session = Depends(get_db)):
    """
    แก้ไขกิจกรรม
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    update_data = data.model_dump(exclude_unset=True)

    # ใช้ค่าเดิมถ้า field เวลาไม่ได้ส่งมา
    new_start_time = update_data.get("start_time", activity.start_time)
    new_end_time = update_data.get("end_time", activity.end_time)

    if new_start_time >= new_end_time:
        raise HTTPException(
            status_code=400,
            detail="start_time must be earlier than end_time"
        )

    for key, value in update_data.items():
        setattr(activity, key, value)

    db.commit()
    db.refresh(activity)

    return {
        "msg": "แก้ไขกิจกรรมสำเร็จ",
        "data": activity
    }


@router.delete("/{activity_id}", response_model=ActivityDeleteResponse)
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    """
    ลบกิจกรรม
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    db.delete(activity)
    db.commit()

    return {
        "msg": "ลบกิจกรรมสำเร็จ"
    }