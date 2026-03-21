from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Activity, User
from schemas import (
    ActivityCreateRequest,
    ActivityUpdateRequest,
    ActivityDeleteRequest,
    ActivityResponse,
    ActivityMessageResponse,
    ActivityDeleteResponse,
)

router = APIRouter(prefix="/activity/v1", tags=["Activity"])


# =========================================================
# Database
# =========================================================
def get_db():
    """
    เปิด/ปิด database session ให้แต่ละ request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# Helper
# =========================================================
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


# =========================================================
# POST
# =========================================================
@router.post("/create", response_model=ActivityMessageResponse)
def create_activity(data: ActivityCreateRequest, db: Session = Depends(get_db)):
    """
    สร้างกิจกรรมใหม่ (เฉพาะ admin)
    """
    admin = get_admin_by_name(db, data.created_by_name)

    if data.start_time >= data.end_time:
        raise HTTPException(
            status_code=500,
            detail="เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด"
        )

    activity = Activity(
        activity_name=data.activity_name,
        activity_date=data.activity_date,
        start_time=data.start_time,
        end_time=data.end_time,
        hours=data.hours,
        location=data.location,
        description=data.description,
        activity_img=data.activity_img,
        created_by_id=admin.id,
        created_by_name=admin.name,
        updated_by_id=admin.id,
        updated_by_name=admin.name,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return {
        "detail": f"สร้างกิจกรรมสำเร็จ",
        "data": activity
    }


# =========================================================
# GET
# =========================================================
@router.get("/get-all", response_model=list[ActivityResponse])
def get_all_activities(db: Session = Depends(get_db)):
    """
    ดึงกิจกรรมทั้งหมด
    """
    activities = db.query(Activity).order_by(Activity.id.desc()).all()
    return activities


@router.get("/get-one/{activity_id}", response_model=ActivityResponse)
def get_activity_by_id(activity_id: int, db: Session = Depends(get_db)):
    """
    ดึงกิจกรรมตาม id
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    return activity


# =========================================================
# PATCH
# =========================================================
@router.patch("/update/{activity_id}", response_model=ActivityMessageResponse)
def update_activity(
    activity_id: int,
    data: ActivityUpdateRequest,
    db: Session = Depends(get_db)
):
    #  เช็คว่า id ตรงกัน
    if activity_id != data.activity_id:
        raise HTTPException(
            status_code=500,
            detail="activity_id ใน URL และ body ไม่ตรงกัน"
        )

    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    admin = get_admin_by_name(db, data.updated_by_name)

    update_data = data.model_dump(exclude_unset=True)

    new_start_time = update_data.get("start_time", activity.start_time)
    new_end_time = update_data.get("end_time", activity.end_time)

    if new_start_time >= new_end_time:
        raise HTTPException(status_code=500, detail="เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด")

    for key, value in update_data.items():
        if key not in ["updated_by_name", "activity_id"]:
            setattr(activity, key, value)

    activity.updated_by_id = admin.id
    activity.updated_by_name = admin.name

    db.commit()
    db.refresh(activity)

    return {
        "detail": f"แก้ไขกิจกรรมสำเร็จ",
        "data": activity
    }

# =========================================================
# DELETE
# =========================================================

@router.delete("/delete/{activity_id}", response_model=ActivityDeleteResponse)
def delete_activity(
    activity_id: int,
    data: ActivityDeleteRequest,
    db: Session = Depends(get_db)
):
    #  เช็ค id
    if activity_id != data.activity_id:
        raise HTTPException(
            status_code=500,
            detail="activity_id ใน URL และ body ไม่ตรงกัน"
        )

    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    admin = get_admin_by_name(db, data.updated_by_name)

    name = activity.activity_name

    activity.updated_by_id = admin.id
    activity.updated_by_name = admin.name
    db.flush()

    db.delete(activity)
    db.commit()

    return {
        "detail": f"ลบกิจกรรมสำเร็จ: {name}"
    }