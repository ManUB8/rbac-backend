from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import SessionLocal
from models import User, Student
from schemas.schemas_user import (UserLoginRequest)


router = APIRouter(prefix="/student-auth/v1", tags=["Student Auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def student_login(data: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    # 1. หา user
    if not user:
        raise HTTPException(
            status_code=500,detail=f"ไม่พบชื่อผู้ใช้นี้ในระบบ: {data.username}"
        )

    if user.password != data.password:
        raise HTTPException(
            status_code=500,detail=f"รหัสผ่านไม่ถูกต้องสำหรับชื่อผู้ใช้"
        )

    if user.role != "student":
        raise HTTPException(
            status_code=403,detail=f"ผู้ใช้นี้ไม่มีสิทธิ์เข้าใช้งานนิสิต"
    )

    if user.is_active is not True:
        raise HTTPException(
            status_code=403,detail=f"บัญชีนี้ถูกปิดการใช้งาน"
        )

    student = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major)
        )
        .filter(Student.user_id == user.id)
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=500,detail=f"ไม่พบข้อมูลนักศึกษาที่เชื่อมกับชื่อผู้ใช้นี้: {data.username}"
        )


    # 3. return ตาม format ที่ต้องการ
    return {
        "id": student.id,
        "student_id": student.student_id,
        "prefix": student.prefix,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "citizen_id": student.citizen_id,
        "gender": student.gender,
        "faculty_id": student.faculty_id,
        "major_id": student.major_id,
        "user_id": student.user_id,
        "faculty_name": student.faculty.faculty_name if student.faculty else None,
        "major_name": student.major.major_name if student.major else None,
        "img_stu": student.img_stu,
        "created_by_id": student.created_by_id,
        "created_by_name": student.created_by_name,
        "updated_by_id": student.updated_by_id,
        "updated_by_name": student.updated_by_name,
    }