from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import SessionLocal
from models import User, Student
from schemas.schemas_user import UserLoginRequest
from schemas.schemas_student import StudentResponse

router = APIRouter(prefix="/student-auth/v1", tags=["Student Auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=StudentResponse)
def student_login(data: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(
            status_code=500,
            detail=f"ไม่พบชื่อผู้ใช้นี้ในระบบ: {data.username}"
        )

    if user.password != data.password:
        raise HTTPException(
            status_code=500,
            detail="รหัสผ่านไม่ถูกต้องสำหรับชื่อผู้ใช้"
        )

    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="ผู้ใช้นี้ไม่มีสิทธิ์เข้าใช้งานนิสิต"
        )

    if user.is_active is not True:
        raise HTTPException(
            status_code=403,
            detail="บัญชีนี้ถูกปิดการใช้งาน"
        )

    student = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
        )
        .filter(Student.user_id == user.user_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=500,
            detail=f"ไม่พบข้อมูลนักศึกษาที่เชื่อมกับชื่อผู้ใช้นี้: {data.username}"
        )

    return {
        "student_id": student.student_id,
        "student_code": student.student_code,
        "prefix": student.prefix,
        "first_name": student.first_name,
        "last_name": student.last_name,
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
        "created_at": student.created_at,
        "updated_at": student.updated_at,
        "user": {
            "username": student.user.username if student.user else None,
            "password": student.user.password if student.user else None,
        }
    }