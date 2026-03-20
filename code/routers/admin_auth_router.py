from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User
from schemas import AdminLoginRequest, AdminLoginResponse

router = APIRouter(prefix="/admin-auth/v1", tags=["Admin Auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/login", response_model=AdminLoginResponse)
def admin_login(data: AdminLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(
            status_code=404,detail=f"ไม่พบชื่อผู้ใช้นี้ในระบบ: {data.username}"
        )

    if user.password != data.password:
        raise HTTPException(
            status_code=404,detail=f"รหัสผ่านไม่ถูกต้องสำหรับชื่อผู้ใช้"
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=403,detail=f"ผู้ใช้นี้ไม่มีสิทธิ์เข้าใช้งานแอดมิน"
        )

    if user.is_active is not True:
        raise HTTPException(
            status_code=403,detail=f"บัญชีนี้ถูกปิดการใช้งาน"
        )

    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
    }