from fastapi import APIRouter, Depends, HTTPException
from .helpers import get_delete_admin_by_name
from sqlalchemy.orm import Session, joinedload
from database import get_db
from datetime import time
from models import Student, Activity, StudentActivity
from schemas.schemas_student_activity import (
    StudentActivityDeleteResponse,
    StudentActivityDeleteRequest,
)


router = APIRouter()

@router.delete("/admin/delete-all-student-activities")
def delete_all_student_activities(
    db: Session = Depends(get_db)
):
    total = db.query(StudentActivity).count()

    db.query(StudentActivity).delete()

    db.commit()

    return {
        "detail": "ลบข้อมูลการเข้าร่วมกิจกรรมทั้งหมดสำเร็จ",
        "total_deleted": total
    }
    
@router.delete("/admin/delete-all-activities")
def delete_all_activities(
    db: Session = Depends(get_db)
):
    total_student_activity = db.query(StudentActivity).count()
    total_activity = db.query(Activity).count()

    db.query(StudentActivity).delete()
    db.query(Activity).delete()

    db.commit()

    return {
        "detail": "ลบกิจกรรมทั้งหมดสำเร็จ",
        "total_deleted_activity": total_activity,
        "total_deleted_student_activity": total_student_activity
    }

@router.delete("/admin/delete-all-student-activities/{activity_id}")
def delete_all_student_activity_by_activity(
    activity_id: int,
    db: Session = Depends(get_db)
):
    total = (
        db.query(StudentActivity)
        .filter(StudentActivity.activity_id == activity_id)
        .count()
    )

    (
        db.query(StudentActivity)
        .filter(StudentActivity.activity_id == activity_id)
        .delete()
    )

    db.commit()

    return {
        "detail": "ลบข้อมูลผู้เข้าร่วมกิจกรรมสำเร็จ",
        "activity_id": activity_id,
        "total_deleted": total
    }


@router.delete( "/delete/{student_activity_id}", response_model=StudentActivityDeleteResponse )
def delete_student_activity(
    student_activity_id: int,
    body: StudentActivityDeleteRequest,
    db: Session = Depends(get_db)
):
    if student_activity_id != body.student_activity_id:
        raise HTTPException(
            status_code=400,
            detail="student_activity_id ใน URL และ body ไม่ตรงกัน"
        )

    admin = get_delete_admin_by_name(db, body.updated_by_name)

    item = (
        db.query(StudentActivity)
        .filter(StudentActivity.student_activity_id == student_activity_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบข้อมูลการเข้าร่วมกิจกรรม"
        )

    deleted_id = item.student_activity_id

    db.delete(item)
    db.commit()

    return {
        "detail": f"แอดมิน {admin.name} ลบข้อมูลการเข้าร่วมกิจกรรมสำเร็จ",
        "student_activity_id": deleted_id,
        "updated_by_id": admin.user_id,
        "updated_by_name": admin.name,
    }
    
  