from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Activity, StudentActivity
from schemas.schemas_activity import (
    ActivityDeleteRequest,
    ActivityDeleteResponse
)

from .helpers import (
    get_db,
    get_delete_admin_by_name,
    get_unix_time
)

router = APIRouter()


@router.delete("/delete/{activity_id}", response_model=ActivityDeleteResponse)
def delete_activity(
    activity_id: int,
    data: ActivityDeleteRequest,
    db: Session = Depends(get_db)
):
    if activity_id != data.activity_id:
        raise HTTPException(
            status_code=400,
            detail="activity_id ไม่ตรงกัน"
        )

    activity = (
        db.query(Activity)
        .filter(Activity.activity_id == activity_id)
        .first()
    )

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบกิจกรรม"
        )

    admin = get_delete_admin_by_name(
        db,
        data.updated_by_name
    )

    current_time = get_unix_time()

    db.query(StudentActivity).filter(
        StudentActivity.activity_id == activity_id
    ).delete(synchronize_session=False)

    activity.activity_status = False
    activity.updated_by_id = admin.user_id
    activity.updated_by_name = admin.name
    activity.updated_at = current_time

    db.commit()
    db.refresh(activity)

    return {
        "detail": f"แอดมิน {admin.name} ลบกิจกรรมสำเร็จ",
        "activity_id": activity.activity_id,
        "activity_status": activity.activity_status,
        "updated_by_id": activity.updated_by_id,
        "updated_by_name": activity.updated_by_name,
    }


@router.delete("/delete-status/{activity_id}", response_model=ActivityDeleteResponse)
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


@router.delete("/hard-delete/{activity_id}")
def hard_delete_activity(
    activity_id: int,
    data: ActivityDeleteRequest,
    db: Session = Depends(get_db)
):
    activity = (
        db.query(Activity)
        .filter(Activity.activity_id == activity_id)
        .first()
    )

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบกิจกรรม"
        )

    db.query(StudentActivity).filter(
        StudentActivity.activity_id == activity_id
    ).delete(synchronize_session=False)

    db.delete(activity)

    db.commit()

    return {
        "detail": "ลบกิจกรรมออกจากฐานข้อมูลถาวรสำเร็จ"
    }