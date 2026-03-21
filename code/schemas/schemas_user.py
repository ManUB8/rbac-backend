from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime

from schemas.schemas_student import (
    StudentRegisterRequest
)

# =========================
# User
# =========================

class UserDeleteRequest(BaseModel):
    deleted_by_name: str
    deleted_user_id: int

class UserDeleteResponse(BaseModel):
    detail: str
    deleted_by: str
    deleted_user: str

class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: Literal["admin", "student"]
    name: str

    created_by_name: Optional[str] = None
    updated_by_name: Optional[str] = None


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Literal["admin", "student"]] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None

    updated_by_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    name: Optional[str] = None
    is_active: bool

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserdetailResponse(BaseModel):
    detail: str
    data: UserResponse

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    id: int
    username: str
    name: Optional[str] = None

    class Config:
        from_attributes = True

class UserLoginRequest(BaseModel):
    username: str
    password: str

class StudentDeleteRequest(BaseModel):
    updated_by_name: str

class StudentDeleteResponse(BaseModel):
    detail: str
    
class UserMessageResponse(BaseModel):
    detail: str
    data: UserResponse
