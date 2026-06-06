from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Activity, ActivityHourType
from schemas.schemas_activity import ActivityCreateRequest, ActivityMessageResponse

from .helpers import get_admin_by_name, get_db, get_unix_time, validate_activity_data


router = APIRouter()


@router.post("/create", response_model=ActivityMessageResponse)
def create_activity(data: ActivityCreateRequest, db: Session = Depends(get_db)):
    admin = get_admin_by_name(db, data.created_by_name)

    validate_activity_data(data)

    hour_type = (
        db.query(ActivityHourType)
        .filter(ActivityHourType.hour_type_id == data.hour_type_id)
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
        volunteer_hours=data.volunteer_hours,
        location=data.location,
        description=data.description,
        activity_img=data.activity_img,
        activity_status=data.activity_status,
        checkin_open_time=data.checkin_open_time,
        checkin_close_time=data.checkin_close_time,
        checkout_open_time=data.checkout_open_time,
        checkout_close_time=data.checkout_close_time,
        hour_type_id=data.hour_type_id,
        target_group=data.target_group,
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