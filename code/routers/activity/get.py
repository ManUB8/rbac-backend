from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from typing import Optional
from datetime import date
from database import get_db

from models import Activity, ActivityHourType, StudentActivity
from schemas.schemas_activity import (
    ActivityAdminListResponse,
    ActivityAdminSearchRequest,
    ActivityFilterAllResponse,
    ActivityListPublicResponse,
    ActivityResponse,
    ActivityWithRegisterCountResponse,
    AdminActivityFilterInfo,
    ActivityFilterByDateResponse
)

from .helpers import get_db


router = APIRouter()


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


@router.get("/filter-by-date", response_model=ActivityFilterByDateResponse)
def get_activity_filter_by_date(
    activity_date: Optional[date] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    target_group: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Activity).filter(Activity.activity_status == True)

    if activity_date is not None:
        query = query.filter(Activity.activity_date == activity_date)

    if start_date is not None:
        query = query.filter(Activity.activity_date >= start_date)

    if end_date is not None:
        query = query.filter(Activity.activity_date <= end_date)

    if target_group is not None and target_group.strip() != "":
        query = query.filter(Activity.target_group == target_group)

    activities = (
        query
        .order_by(Activity.activity_date.asc(), Activity.start_time.asc())
        .all()
    )

    data = []

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
            if activity.max_participants is not None:
                register_text = f"{registered_count}/{activity.max_participants}"
                is_full = registered_count >= activity.max_participants
            else:
                register_text = str(registered_count)

        data.append({
            "activity_id": activity.activity_id,
            "activity_name": activity.activity_name,
            "activity_date": activity.activity_date,
            "start_time": activity.start_time,
            "end_time": activity.end_time,
            "location": activity.location,

            "check_type": activity.check_type,
            "target_group": activity.target_group,

            "activity_lat": activity.activity_lat,
            "activity_lng": activity.activity_lng,
            "activity_radius_meter": activity.activity_radius_meter,

            "require_registration": activity.require_registration,
            "max_participants": activity.max_participants,
            "registered_count": registered_count,
            "register_text": register_text,
            "is_full": is_full,
        })

    return {
        "detail": "ดึงกิจกรรมตามวันที่สำเร็จ",
        "data": data
    }