from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Activity, ActivityHourType
from schemas.schemas_activity import ActivityMessageResponse, ActivityUpdateRequest

from .helpers import get_admin_by_name, get_db, get_unix_time


router = APIRouter()


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
    new_checkin_open_time = update_data.get("checkin_open_time", activity.checkin_open_time)
    new_checkin_close_time = update_data.get("checkin_close_time", activity.checkin_close_time)
    new_checkout_open_time = update_data.get("checkout_open_time", activity.checkout_open_time)
    new_checkout_close_time = update_data.get("checkout_close_time", activity.checkout_close_time)
    
    if "hour_type_id" in update_data:
        hour_type = (
            db.query(ActivityHourType)
            .filter(
                ActivityHourType.hour_type_id == update_data["hour_type_id"],
            )
            .first()
        )

        if not hour_type:
            raise HTTPException(status_code=400, detail="ไม่พบประเภทชั่วโมงกิจกรรม")

    if new_start_time >= new_end_time:
        raise HTTPException(status_code=400, detail="เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด")

    if (
        new_checkin_open_time is not None
        and new_checkin_close_time is not None
        and new_checkin_open_time >= new_checkin_close_time
    ):
        raise HTTPException(status_code=400, detail="เวลาเปิดเช็คอินต้องน้อยกว่าเวลาปิดเช็คอิน")

    if (
        new_checkout_open_time is not None
        and new_checkout_close_time is not None
        and new_checkout_open_time >= new_checkout_close_time
    ):
        raise HTTPException(status_code=400, detail="เวลาเปิดเช็คเอาท์ต้องน้อยกว่าเวลาปิดเช็คเอาท์")

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
