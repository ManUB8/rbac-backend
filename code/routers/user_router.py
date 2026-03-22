from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User
from schemas.schemas_user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserMessageResponse,
    UserDeleteRequest,
    UserDeleteResponse,
)

router = APIRouter(prefix="/user/v1", tags=["User Management"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------
# mock current user
# ตอนนี้ยังไม่มี auth ก็หยิบ user คนแรกในระบบไปก่อน
# ---------------------------------------------------
def get_current_user(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        return None
    return user


# ---------------------------------------------------
# CREATE USER
# ยังไม่บังคับ admin ในช่วงเริ่มระบบ
# ---------------------------------------------------
@router.post("/create", response_model=UserMessageResponse)
def create_user(
    data: UserCreateRequest,
    db: Session = Depends(get_db),
):
    # เช็ค username ซ้ำ
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=500, detail="Username already exists")

    # 🔥 เช็ค creator จาก name → เอา id จริงมาใช้
    if not data.created_by_name:
        raise HTTPException(status_code=500, detail="created_by_name is required")

    creator = db.query(User).filter(
        User.name == data.created_by_name,
        User.role == "admin",
        User.is_active == True
    ).first()

    if not creator:
        raise HTTPException(status_code=403, detail="Creator must be admin")

    user = User(
        username=data.username,
        password=data.password,
        role=data.role,
        name=data.name,
        is_active=True,

        # ✅ ใช้ id จริงจาก DB
        created_by_id=creator.id,
        created_by_name=creator.name,
        updated_by_id=creator.id,
        updated_by_name=creator.name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "detail": "สร้างผู้ใช้งานสำเร็จ",
        "data": user
    }


# ---------------------------------------------------
# GET ALL USERS
# ---------------------------------------------------
@router.get("/all-users", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    return users


# ---------------------------------------------------
# GET USER BY ID
# ---------------------------------------------------
@router.get("/get-one/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=500, detail="User not found")
    return user


# ---------------------------------------------------
# UPDATE USER
# ---------------------------------------------------
@router.patch("/update/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=500, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)

    # เช็ค username ซ้ำ
    if "username" in update_data and update_data["username"] != user.username:
        existing_user = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_user:
            raise HTTPException(status_code=500, detail="Username already exists")

    # เช็ค updater
    if not data.updated_by_name:
        raise HTTPException(status_code=500, detail="updated_by_name is required")

    updater = db.query(User).filter(
        User.name == data.updated_by_name,
        User.role == "admin",
        User.is_active == True
    ).first()

    if not updater:
        raise HTTPException(status_code=403, detail="Updater must be admin")

    for key, value in update_data.items():
        setattr(user, key, value)

    #  ใช้ id จริง
    user.updated_by_id = updater.id
    user.updated_by_name = updater.name

    db.commit()
    db.refresh(user)

    return user


# ---------------------------------------------------
# DELETE USER
# soft delete = ปิดการใช้งาน
# ---------------------------------------------------
@router.delete("/delete/{user_id}", response_model=UserDeleteResponse)
def delete_user(
    user_id: int,
    data: UserDeleteRequest,
    db: Session = Depends(get_db),
):
    
    # 🔥 เช็คว่า ID ใน URL กับ body ต้องตรงกัน
    if user_id != data.deleted_user_id:
        raise HTTPException(
            status_code=500,
            detail="user_id ใน URL และ body ไม่ตรงกัน"
        )

    # -----------------------------
    # หา admin
    # -----------------------------
    admin = (
        db.query(User)
        .filter(
            User.name == data.deleted_by_name,
            User.role == "admin",
            User.is_active == True
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=403,
            detail=f"ผู้ใช้นี้ไม่มีสิทธิ์แอดมิน: {data.deleted_by_name}"
        )

    # -----------------------------
    # หา user ที่จะลบ
    # -----------------------------
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=500, detail="User not found")

    # -----------------------------
    # กันลบตัวเอง
    # -----------------------------
    if user.id == admin.id:
        raise HTTPException(
            status_code=500,
            detail="ไม่สามารถลบบัญชีของตัวเองได้"
        )

    # -----------------------------
    # soft delete
    # -----------------------------
    user.is_active = False
    user.updated_by_id = admin.id
    user.updated_by_name = admin.name

    db.commit()

    return {
        "detail": "ปิดการใช้งานผู้ใช้สำเร็จ",
        "deleted_by": admin.name,
        "deleted_user": user.name,
    }