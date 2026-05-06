from pydantic import BaseModel
from typing import Optional, List
from datetime import date



class StudentActivityRegisterRequest(BaseModel):
    student_code: str
    activity_id: int


class StudentActivityCheckinRequest(BaseModel):
    student_code: str
    activity_id: int
    checkin_lat: float
    checkin_lng: float
    created_by_name: str


class StudentActivityCheckoutRequest(BaseModel):
    student_code: str
    activity_id: int
    checkout_lat: float
    checkout_lng: float
    updated_by_name: str


class StudentActivityViewItemResponse(BaseModel):
    student_activity_id: int
    student_id: int
    activity_id: int
    student_code: str
    full_name: str
    activity_name: str
    activity_date: date
    activity_time_text: str
    location: Optional[str] = None

    check_type: str
    require_registration: bool
    max_participants: Optional[int] = None

    attendance_status: str
    registered_at: Optional[int] = None
    checkin_at: Optional[int] = None
    checkout_at: Optional[int] = None

    checkin_lat: Optional[float] = None
    checkin_lng: Optional[float] = None
    checkout_lat: Optional[float] = None
    checkout_lng: Optional[float] = None

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class StudentActivityResponse(BaseModel):
    detail: str
    data: StudentActivityViewItemResponse

class StudentActivityCreateRequest(BaseModel):
    student_code: str
    activity_id: int
    created_by_name: str


class StudentActivityGetOneRequest(BaseModel):
    student_activity_id: int


class StudentActivityUpdateRequest(BaseModel):
    student_activity_id: int
    student_id: Optional[int] = None
    activity_id: Optional[int] = None
    attendance_status: Optional[str] = None
    checkin_at: Optional[int] = None
    updated_by_name: str


class StudentActivityDeleteRequest(BaseModel):
    student_activity_id: int
    updated_by_name: str


class StudentActivityDeleteResponse(BaseModel):
    detail: str
    student_activity_id: int
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None


class StudentActivityFilterRequest(BaseModel):
    activity_id: int
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    updated_by_name: str



class StudentActivityListResponse(BaseModel):
    detail: str
    data: List[StudentActivityViewItemResponse]


class StudentActivityFilterResponse(BaseModel):
    detail: str
    activity_id: int
    count_student: int
    data: List[StudentActivityViewItemResponse]
    
