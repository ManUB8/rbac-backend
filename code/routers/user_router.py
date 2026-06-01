from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import time as time_module
from sqlalchemy import func

from database import SessionLocal
from models import User
from schemas.schemas_user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserMessageResponse,
    UserDeleteRequest,
    UserDeleteResponse,
    UserGetAllRequest,
    UserGetAllResponse,
)

router = APIRouter(prefix="/user/v1", tags=["User Management"])
DELETE_ALLOWED_ADMIN_NAMES = ["mangpo", "first", "soda","Tatum","Tum"]


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
from sqlalchemy import func

@router.post("/get-all", response_model=UserGetAllResponse)
def get_all_users_filter(
    data: UserGetAllRequest,
    db: Session = Depends(get_db)
):
    page = max(data.page, 1)
    limit = max(data.limit, 1)
    offset = (page - 1) * limit

    allowed_roles = ["admin", "temporary_admin"]

    # -----------------------------
    # total role ทั้งหมดของระบบ
    # เฉพาะ admin / temporary_admin
    # -----------------------------
    role_rows = (
        db.query(
            User.role,
            func.count(User.user_id)
        )
        .filter( User.role.in_(allowed_roles))
        .group_by(User.role)
        .all()
    )

    total_role = {
        row[0]: row[1]
        for row in role_rows
    }

    total_user_all = sum(total_role.values())

    # -----------------------------
    # query filter สำหรับ data
    # -----------------------------
    query = (
        db.query(User)
        .filter(User.role.in_(allowed_roles))
    )

    if data.search:
        search_text = f"%{data.search}%"

        query = query.filter(
            User.name.ilike(search_text)
        )

    if data.role:
        query = query.filter(
            User.role == data.role
        )

    total_all = query.count()

    total_page = (
        (total_all + limit - 1) // limit
        if total_all else 0
    )

    users = (
        query
        .order_by(User.user_id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "detail": "ดึงข้อมูลผู้ใช้งานสำเร็จ",
        "page": page,
        "limit": limit,
        "total_all": total_all,
        "total_page": total_page,
        # total เฉพาะ admin / temporary_admin
        "total_user_all": total_user_all,
        "total_role": total_role,
        "data": users,
    }
    
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
def delete_user(
    user_id: int,
    data: UserDeleteRequest,
    db: Session = Depends(get_db)
):
    if user_id != data.deleted_user_id:
        raise HTTPException(
            status_code=500,
            detail="user_id ใน URL และ body ไม่ตรงกัน"
        )

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

    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=500,
            detail="User not found"
        )

    if user.user_id == admin.user_id:
        raise HTTPException(
            status_code=500,
            detail="ไม่สามารถลบบัญชีของตัวเองได้"
        )

    deleted_user_name = user.name

    # ลบจริง
    db.delete(user)

    db.commit()

    return {
        "detail": "ลบผู้ใช้สำเร็จ",
        "deleted_by": admin.name,
        "deleted_user": deleted_user_name,
    }