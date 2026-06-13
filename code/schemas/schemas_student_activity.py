# schemas_student_activity.py

from pydantic import BaseModel, field_serializer
from typing import Optional, List
from datetime import date, time


# =========================
# REQUEST
# =========================

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


class StudentActivityCreateRequest(BaseModel):
    student_code: str
    activity_id: int
    created_by_name: str


class StudentActivityGetOneRequest(BaseModel):
    student_activity_id: int


class StudentActivityUpdateRequest(BaseModel):
    student_activity_id: int
    activity_id: Optional[int] = None
    attendance_status: Optional[str] = None
    updated_by_name: str


class StudentActivityDeleteRequest(BaseModel):
    student_activity_id: int
    updated_by_name: str


class StudentActivityFilterRequest(BaseModel):
    activity_id: int
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    updated_by_name: str


class StudentActivityAdminSearchRequest(BaseModel):
    activity_id: str = ""
    search: str = ""
    student_code: str = ""

    page: int = 1
    limit: int = 20

    year_status: str = ""
    faculty_id: str = ""
    major_id: str = ""


class StudentActivityAllInOneSearchRequest(BaseModel):
    search: str = ""
    student_code: str = ""

    year_status: str = ""

    faculty_id: str = ""
    major_id: str = ""

    hour_type: str = ""


# =========================
# CHECK DETAIL
# =========================

class CheckInDettail(BaseModel):
    checkin_at: Optional[int] = None

    checkin_status: Optional[str] = None
    checkin_status_text: Optional[str] = None

    checkin_lat: Optional[float] = None
    checkin_lng: Optional[float] = None


class CheckOutDettail(BaseModel):
    checkout_at: Optional[int] = None

    checkout_status: Optional[str] = None
    checkout_status_text: Optional[str] = None

    checkout_lat: Optional[float] = None
    checkout_lng: Optional[float] = None


class CheckDettail(BaseModel):
    attendance_status: str

    registered_at: Optional[int] = None

    # ชั่วโมงจิตอาสาที่ได้จริง
    earned_hours: float = 0

    # ชั่วโมงจิตอาสาของกิจกรรม
    volunteer_hours: float = 0

    checkin: Optional[CheckInDettail] = None
    checkout: Optional[CheckOutDettail] = None


# =========================
# MAIN RESPONSE ITEM
# =========================

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

    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    year_status: Optional[str] = None

    prefix: Optional[str] = None

    check_type: str
    target_group: str = "all"

    require_registration: bool

    max_participants: Optional[int] = None

    # เวลากิจกรรมจริง
    hours: float = 0

    # ชั่วโมงจิตอาสาของกิจกรรม
    volunteer_hours: float = 0

    # 👇 ย้ายข้อมูล attendance มารวมตรงนี้
    check_detail: Optional[CheckDettail] = None

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None

    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


# =========================
# COMMON RESPONSE
# =========================

class StudentActivityResponse(BaseModel):
    detail: str
    data: StudentActivityViewItemResponse


class StudentActivityDeleteResponse(BaseModel):
    detail: str

    student_activity_id: int

    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None


class StudentActivityListResponse(BaseModel):
    detail: str
    data: List[StudentActivityViewItemResponse]


class StudentActivityFilterResponse(BaseModel):
    detail: str

    activity_id: int

    count_student: int

    data: List[StudentActivityViewItemResponse]


class StudentActivityAdminListResponse(BaseModel):
    detail: str

    total_all: int

    page: int
    limit: int

    data: List[StudentActivityViewItemResponse]


# =========================
# AVAILABLE ACTIVITY
# =========================

class StudentActivityAvailableItemResponse(BaseModel):
    activity_id: int

    activity_name: str

    activity_date: date
    activity_time_text: str

    location: Optional[str] = None
    activity_img: Optional[str] = None

    check_type: str
    target_group: str = "all"

    require_registration: bool

    max_participants: Optional[int] = None

    # เวลากิจกรรมจริง
    hours: float = 0

    # ชั่วโมงจิตอาสาของกิจกรรม
    volunteer_hours: float = 0


    # checkin time
    checkin_open_time: Optional[time] = None
    checkin_close_time: Optional[time] = None

    # checkout time
    checkout_open_time: Optional[time] = None
    checkout_close_time: Optional[time] = None

    registered_count: int = 0

    register_text: Optional[str] = None

    is_registered: bool = False
    is_full: bool = False

    button_text: str
    button_status: str

    @field_serializer(
        "checkin_open_time",
        "checkin_close_time",
        "checkout_open_time",
        "checkout_close_time"
    )
    def serialize_time(
        self,
        value: Optional[time]
    ):
        if value is None:
            return None

        return value.strftime("%H.%M")

    model_config = {
        "from_attributes": True
    }


class StudentActivityAvailableListResponse(BaseModel):
    detail: str
    student_code: str
    data: List[StudentActivityAvailableItemResponse]


# =========================
# ALL IN ONE
# =========================

class StudentActivityAllInOneActivityItem(BaseModel):
    student_activity_id: int

    activity_id: int

    activity_name: str

    activity_date: date
    activity_time_text: str

    location: Optional[str] = None
    activity_img: Optional[str] = None
    description: Optional[str] = None
    start_time: str
    end_time: str

    # เวลากิจกรรมจริง
    hours: Optional[float] = None

    # ชั่วโมงจิตอาสา
    volunteer_hours: Optional[float] = None

    hour_type_id: Optional[str] = None

    check_type: str
    target_group: str = "all"

    require_registration: bool

    max_participants: Optional[int] = None

    check_detail: Optional[CheckDettail] = None

class StudentActivityAllInOneStudentItem(BaseModel):
    student_id: int
    student_code: str
    prefix: Optional[str] = None
    position_id: Optional[int] = None
    position_name: Optional[str] = None
    student_position_id: Optional[int] = None
    position_start_date: Optional[date] = None
    position_end_date: Optional[date] = None
    full_name: str
    first_name: str
    last_name: str
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    year_status: Optional[str] = None
    total_activity: int
    # เวลากิจกรรมรวม
    total_hours: float = 0
    # ชั่วโมงจิตอาสารวม
    total_volunteer_hours: float = 0
    # ชั่วโมงจิตอาสาที่ได้จริงรวม
    total_earned_hours: float = 0
    activity: List[StudentActivityAllInOneActivityItem]
    

class StudentActivityAllInOneResponse(BaseModel):
    detail: str
    data: Optional[StudentActivityAllInOneStudentItem] = None
