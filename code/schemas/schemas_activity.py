from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional
from datetime import date, time


def parse_time_dot(value):
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        value = value.strip().replace(":", ".")
        hh, mm = value.split(".")
        return time(hour=int(hh), minute=int(mm))
    raise ValueError("รูปแบบเวลาไม่ถูกต้อง")


class ActivityCreateRequest(BaseModel):
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool = True
    created_by_name: str

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_time_format(cls, value):
        return parse_time_dot(value)


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
    activity_status: Optional[bool] = None
    updated_by_name: str

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_time_format(cls, value):
        return parse_time_dot(value)


class ActivityDeleteRequest(BaseModel):
    activity_id: int
    updated_by_name: str


class ActivityResponse(BaseModel):
    activity_id: int
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
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time):
        return value.strftime("%H.%M")

    model_config = {
        "from_attributes": True
    }


class ActivityDetailResponse(BaseModel):
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