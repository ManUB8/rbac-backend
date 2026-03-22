from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import time as time_module

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


def get_unix_time() -> int:
    return int(time_module.time())


@router.post("/create", response_model=UserMessageResponse)
def create_user(data: UserCreateRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=500, detail="Username already exists")

    if not data.created_by_name:
        raise HTTPException(status_code=500, detail="created_by_name is required")

    creator = db.query(User).filter(
        User.name == data.created_by_name,
        User.role == "admin",
        User.is_active == True
    ).first()

    if not creator:
        raise HTTPException(status_code=403, detail="Creator must be admin")

    now = get_unix_time()

    user = User(
        username=data.username,
        password=data.password,
        role=data.role,
        name=data.name,
        is_active=True,
        created_by_id=creator.user_id,
        created_by_name=creator.name,
        updated_by_id=creator.user_id,
        updated_by_name=creator.name,
        created_at=now,
        updated_at=now,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"detail": "สร้างผู้ใช้งานสำเร็จ", "data": user}


@router.get("/all-users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/get-one/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=500, detail="User not found")
    return user


@router.patch("/update/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdateRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=500, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)

    if "username" in update_data and update_data["username"] != user.username:
        existing_user = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_user:
            raise HTTPException(status_code=500, detail="Username already exists")

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

    user.updated_by_id = updater.user_id
    user.updated_by_name = updater.name
    user.updated_at = get_unix_time()

    db.commit()
    db.refresh(user)

    return user


@router.delete("/delete/{user_id}", response_model=UserDeleteResponse)
def delete_user(user_id: int, data: UserDeleteRequest, db: Session = Depends(get_db)):
    if user_id != data.deleted_user_id:
        raise HTTPException(status_code=500, detail="user_id ใน URL และ body ไม่ตรงกัน")

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
        raise HTTPException(status_code=403, detail=f"ผู้ใช้นี้ไม่มีสิทธิ์แอดมิน: {data.deleted_by_name}")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=500, detail="User not found")

    if user.user_id == admin.user_id:
        raise HTTPException(status_code=500, detail="ไม่สามารถลบบัญชีของตัวเองได้")

    user.is_active = False
    user.updated_by_id = admin.user_id
    user.updated_by_name = admin.name
    user.updated_at = get_unix_time()

    db.commit()

    return {
        "detail": "ปิดการใช้งานผู้ใช้สำเร็จ",
        "deleted_by": admin.name,
        "deleted_user": user.name,
    }