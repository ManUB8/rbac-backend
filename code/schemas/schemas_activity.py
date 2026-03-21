
from pydantic import BaseModel, field_validator
from typing import  Optional
from datetime import date, time, datetime

# =========================
# Activity
# =========================

class ActivityCreateRequest(BaseModel):
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool
    created_by_name: str


class ActivityUpdateRequest(BaseModel):
    activity_id: int
    activity_name: Optional[str] = None
    activity_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    updated_by_name: str
    activity_status: bool


class ActivityDeleteRequest(BaseModel):
    activity_id: int
    updated_by_name: str


class ActivityResponse(BaseModel):
    id: int
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ActivitydetailResponse(BaseModel):
    detail: str
    data: ActivityResponse

class ActivityDeleteResponse(BaseModel):
    detail: str
    activity_id: int
    activity_status: bool
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

class ActivityMessageResponse(BaseModel):
    detail: str
    data: ActivityResponse