from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional, List
from datetime import date, time
from decimal import Decimal
from uuid import UUID

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


def validate_check_type(value: str):
    allowed = ["checkin_only", "checkout_only", "checkin_checkout"]
    if value not in allowed:
        raise ValueError("check_type ต้องเป็น checkin_only หรือ checkin_checkout")
    return value

class HourTypeResponse(BaseModel):
    hour_type_id: UUID
    hour_type_name: str

    model_config = {
        "from_attributes": True
    }
    
class ActivityCreateRequest(BaseModel):
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    volunteer_hours: Decimal = Decimal("0")
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool = True
    checkin_open_time: Optional[time] = None
    checkin_close_time: Optional[time] = None
    checkout_open_time: Optional[time] = None
    checkout_close_time: Optional[time] = None
    created_by_name: str
    hour_type_id: UUID

    check_type: str = "checkin_only"
    require_registration: bool = False
    max_participants: Optional[int] = None

    activity_lat: Optional[float] = None
    activity_lng: Optional[float] = None
    activity_radius_meter: int = 100

    @field_validator(
        "start_time",
        "end_time",
        "checkin_open_time",
        "checkin_close_time",
        "checkout_open_time",
        "checkout_close_time",
        mode="before"
    )
    @classmethod
    def validate_time_format(cls, value):
        return parse_time_dot(value)

    @field_validator("check_type")
    @classmethod
    def validate_check_type_field(cls, value):
        return validate_check_type(value)


class ActivityUpdateRequest(BaseModel):
    activity_id: int
    activity_name: Optional[str] = None
    activity_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours: Optional[float] = None
    volunteer_hours: Optional[Decimal] = None
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: Optional[bool] = None
    checkin_open_time: Optional[time] = None
    checkin_close_time: Optional[time] = None
    checkout_open_time: Optional[time] = None
    checkout_close_time: Optional[time] = None
    updated_by_name: str
    hour_type_id: Optional[UUID] = None

    check_type: Optional[str] = None
    require_registration: Optional[bool] = None
    max_participants: Optional[int] = None

    activity_lat: Optional[float] = None
    activity_lng: Optional[float] = None
    activity_radius_meter: Optional[int] = None

    @field_validator(
        "start_time",
        "end_time",
        "checkin_open_time",
        "checkin_close_time",
        "checkout_open_time",
        "checkout_close_time",
        mode="before"
    )
    @classmethod
    def validate_time_format(cls, value):
        return parse_time_dot(value)

    @field_validator("check_type")
    @classmethod
    def validate_check_type_field(cls, value):
        if value is None:
            return value
        return validate_check_type(value)


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
    volunteer_hours: Decimal
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool
    checkin_open_time: Optional[time] = None
    checkin_close_time: Optional[time] = None
    checkout_open_time: Optional[time] = None
    checkout_close_time: Optional[time] = None
    hour_type_id: Optional[UUID] = None
    hour_type: Optional[HourTypeResponse] = None

    check_type: str
    require_registration: bool
    max_participants: Optional[int] = None

    activity_lat: Optional[float] = None
    activity_lng: Optional[float] = None
    activity_radius_meter: int

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    @field_serializer(
        "start_time",
        "end_time",
        "checkin_open_time",
        "checkin_close_time",
        "checkout_open_time",
        "checkout_close_time"
    )
    def serialize_time(self, value: Optional[time]):
        if value is None:
            return None
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

    
class ActivityWithRegisterCountResponse(ActivityResponse):
    registered_count: int = 0
    register_text: Optional[str] = None
    is_full: bool = False


class ActivityListPublicResponse(BaseModel):
    detail: str
    data: List[ActivityWithRegisterCountResponse]

class ActivityMessageResponse(BaseModel):
    detail: str
    data: ActivityResponse
    
    
class AdminActivityFilterInfo(BaseModel):
    id: int
    name: str
    code: str = ""


class ActivityAdminSearchRequest(BaseModel):
    search: str = ""
    page: int = 1
    limit: int = 20
    hour_type_id: str = ""
    activity_status: str = ""
    check_type: str = ""
    require_registration: str = ""


class ActivityAdminListResponse(BaseModel):
    total_activity: int
    total_active_activity: int
    total_inactive_activity: int

    activity: List[ActivityWithRegisterCountResponse]

class FilterOption(BaseModel):
    label: str
    id: str


class ActivityFilterAllResponse(BaseModel):
    hour_type: List[FilterOption]
    check_type: List[FilterOption]
    activity_status: List[FilterOption]
    require_registration: List[FilterOption]
