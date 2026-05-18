from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import time, datetime
import time as time_module

from database import SessionLocal
from models import Activity, User, StudentActivity, ActivityHourType
from schemas.schemas_activity import (
    ActivityCreateRequest,
    ActivityUpdateRequest,
    ActivityDeleteRequest,
    ActivityResponse,
    ActivityMessageResponse,
    ActivityDeleteResponse,
    AdminActivityFilterInfo,
    ActivityAdminSearchRequest,
    ActivityAdminListResponse,
    ActivityWithRegisterCountResponse,
    ActivityListPublicResponse,
    ActivityFilterAllResponse
)

router = APIRouter(prefix="/activity/v1", tags=["Activity"])
DELETE_ALLOWED_ADMIN_NAMES = ["mangpo", "first", "soda","Tatum","Tum"]


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
    hour_type = (
        db.query(ActivityHourType)
        .filter(
            ActivityHourType.hour_type_id == data.hour_type_id,
            ActivityHourType.is_active == True
        )
        .first()
    )

    if not hour_type:
        raise HTTPException(status_code=400, detail="ไม่พบประเภทชั่วโมงกิจกรรม")

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
        hour_type_id=data.hour_type_id,

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


@router.get("/get-all", response_model=ActivityListPublicResponse)
def get_all_active_activities(db: Session = Depends(get_db)):
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

        is_full = False
        register_text = None

        if activity.require_registration:
            max_participants = activity.max_participants or 0
            register_text = f"{registered_count}/{max_participants}"

            if activity.max_participants is not None:
                is_full = registered_count >= activity.max_participants

        activity_data = ActivityWithRegisterCountResponse.model_validate(activity)
        activity_data.registered_count = registered_count
        activity_data.register_text = register_text
        activity_data.is_full = is_full

        result.append(activity_data)

    return {
        "detail": "ดึงข้อมูลกิจกรรมทั้งหมดสำเร็จ",
        "data": result
    }


@router.post("/admin/get-all", response_model=ActivityAdminListResponse)
def get_all_activities_admin(
    data: ActivityAdminSearchRequest,
    db: Session = Depends(get_db)
):
    page = max(data.page, 1)
    limit = max(data.limit, 1)
    offset = (page - 1) * limit

    total_active_activity = (
        db.query(Activity)
        .filter(Activity.activity_status == True)
        .count()
    )

    total_inactive_activity = (
        db.query(Activity)
        .filter(Activity.activity_status == False)
        .count()
    )

    query = db.query(Activity)

    if data.search:
        search_text = f"%{data.search}%"
        query = query.filter(Activity.activity_name.ilike(search_text))

    if data.activity_status != "":
        activity_status_bool = data.activity_status.lower() == "true"
        query = query.filter(Activity.activity_status == activity_status_bool)

    if data.check_type != "":
        query = query.filter(Activity.check_type == data.check_type)

    if data.require_registration != "":
        require_registration_bool = data.require_registration.lower() == "true"
        query = query.filter(Activity.require_registration == require_registration_bool)
    if data.hour_type_id != "":
        query = query.filter(Activity.hour_type_id == data.hour_type_id)

    total_activity = query.count()

    activities = (
        query
        .order_by(Activity.activity_id.desc())
        .offset(offset)
        .limit(limit)
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

        is_full = False
        register_text = None

        if activity.require_registration:
            max_participants = activity.max_participants or 0
            register_text = f"{registered_count}/{max_participants}"

            if activity.max_participants is not None:
                is_full = registered_count >= activity.max_participants

        activity_data = ActivityWithRegisterCountResponse.model_validate(activity)
        activity_data.registered_count = registered_count
        activity_data.register_text = register_text
        activity_data.is_full = is_full

        result.append(activity_data)

    return {
        "total_activity": total_activity,
        "total_active_activity": total_active_activity,
        "total_inactive_activity": total_inactive_activity,
        "activity": result,
    }
    
    
@router.get("/get-one/{activity_id}", response_model=ActivityResponse)
def get_activity_by_id(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=400, detail="ไม่พบกิจกรรม")

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
    
    if "hour_type_id" in update_data:
        hour_type = (
            db.query(ActivityHourType)
            .filter(
                ActivityHourType.hour_type_id == update_data["hour_type_id"],
                ActivityHourType.is_active == True
            )
            .first()
        )

    if not hour_type:
        raise HTTPException(status_code=400, detail="ไม่พบประเภทชั่วโมงกิจกรรม")

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
def delete_activity(
    activity_id: int,
    data: ActivityDeleteRequest,
    db: Session = Depends(get_db)
):
    if activity_id != data.activity_id:
        raise HTTPException(status_code=400, detail="activity_id ไม่ตรงกัน")

    activity = (
        db.query(Activity)
        .filter(Activity.activity_id == activity_id)
        .first()
    )

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    admin = get_delete_admin_by_name(db, data.updated_by_name)

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
    
@router.get("/filter-info", response_model=list[AdminActivityFilterInfo])
def get_activity_filter_info(db: Session = Depends(get_db)):

    activities = (
        db.query(Activity)
        .filter(Activity.activity_status == True)
        .order_by(Activity.activity_date.desc())
        .all()
    )

    result = [
        {
            "id": 0,
            "name": "ทั้งหมด",
            "code": ""
        }
    ]

    for activity in activities:
        result.append({
            "id": activity.activity_id,
            "name": activity.activity_name,
            "code": str(activity.activity_id)
        })

    return result


@router.get("/filter-all", response_model=ActivityFilterAllResponse)
def get_activity_filter_all(db: Session = Depends(get_db)):
    hour_types = (
        db.query(ActivityHourType)
        .order_by(ActivityHourType.hour_type_name.asc())
        .all()
    )

    return {
        "hour_type": [
            {
                "label": item.hour_type_name,
                "id": str(item.hour_type_id)
            }
            for item in hour_types
        ],

        "check_type": [
            {
                "label": "เช็คอินอย่างเดียว",
                "id": "checkin_only"
            },
            {
                "label": "เช็คเอาท์อย่างเดียว",
                "id": "checkout_only"
            },
            {
                "label": "เช็คอิน / เช็คเอาท์",
                "id": "checkin_checkout"
            }
        ],

        "activity_status": [
            {
                "label": "เปิดใช้งาน",
                "id": "true"
            },
            {
                "label": "ปิดการใช้งาน",
                "id": "false"
            }
        ],

        "require_registration": [
            {
                "label": "ต้องลงทะเบียนก่อน",
                "id": "true"
            },
            {
                "label": "เข้าร่วมได้เลย",
                "id": "false"
            }
        ]
    }