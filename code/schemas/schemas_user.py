from pydantic import BaseModel
from typing import Optional, Literal


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


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Literal["admin", "student"]] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    updated_by_name: Optional[str] = None


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    name: Optional[str] = None
    is_active: bool

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class UserDetailResponse(BaseModel):
    detail: str
    data: UserResponse


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    user_id: int
    username: str
    name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserMessageResponse(BaseModel):
    detail: str
    data: UserResponse