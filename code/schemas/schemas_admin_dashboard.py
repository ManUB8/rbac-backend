from pydantic import BaseModel
from typing import List, Optional


# =========================
# ADMIN DASHBOARD
# =========================

class SimpleCountSummary(BaseModel):
    total_student: int
    joined_count: int
    not_joined_count: int


class SimpleMajorInFacultyCount(SimpleCountSummary):
    major_id: int
    major_name: str


class SimpleFacultyWithMajorCount(SimpleCountSummary):
    faculty_id: int
    faculty_name: str
    major: List[SimpleMajorInFacultyCount]


class CountSummary(BaseModel):
    count_student: int
    joined_count: int
    not_joined_count: int
    checkin_count: int
    checkout_count: int
    total_student: int
    join_rate_percent: float


class YearCount(CountSummary):
    name: str


class MajorInFacultyCount(CountSummary):
    major_id: int
    major_name: str


class FacultyWithMajorCount(CountSummary):
    faculty_id: int
    faculty_name: str
    major: List[MajorInFacultyCount]


class ActivityDashboardSummary(BaseModel):
    activity_id: int
    activity_name: str
    activity_date: str

    start_time: str
    end_time: str

    # เวลากิจกรรมจริง
    hours: float

    # ชั่วโมงจิตอาสาของกิจกรรม
    volunteer_hours: float

    location: Optional[str] = None

    check_type: str
    require_registration: bool

    joined_count: int
    not_joined_count: int

    checkin_count: int
    checkout_count: int

    total_count: int

    join_rate_percent: float
    checkout_rate_percent: float


class FacultyRankItem(BaseModel):
    faculty_id: int
    faculty_name: str

    total_student: int

    joined_count: int
    not_joined_count: int

    checkin_count: int
    checkout_count: int

    join_rate_percent: float


class MajorRankItem(BaseModel):
    major_id: int
    major_name: str

    faculty_id: int
    faculty_name: str

    total_student: int

    joined_count: int
    not_joined_count: int

    checkin_count: int
    checkout_count: int

    join_rate_percent: float


class AdminStudentItem(BaseModel):
    activity_count: int

    joined_count: int
    not_joined_count: int

    checkin_count: int
    checkout_count: int

    student_count_all: int

    # ชั่วโมงกิจกรรมรวม
    hours_count_all: float

    # ชั่วโมงจิตอาสารวม
    volunteer_hours_count_all: float

    join_rate_percent: float
    checkout_rate_percent: float

    top_activity: Optional[ActivityDashboardSummary] = None
    selected_activity: Optional[ActivityDashboardSummary] = None

    activity_rank: List[ActivityDashboardSummary]
    faculty_rank: List[FacultyRankItem]
    major_rank: List[MajorRankItem]

    year_count: List[YearCount]

    faculty: List[SimpleFacultyWithMajorCount]


class AdminStudentMessageResponse(BaseModel):
    detail: str
    data: AdminStudentItem


class DashboardMajorActivityBreakdown(BaseModel):
    major_id: int
    major_name: str
    total_student: int
    count_student: int
    joined_count: int
    not_joined_count: int
    checkin_count: int
    checkout_count: int
    join_rate_percent: float
    checkout_rate_percent: float


class DashboardFacultyActivityBreakdown(BaseModel):
    faculty_id: int
    faculty_name: str
    total_student: int
    count_student: int
    joined_count: int
    not_joined_count: int
    checkin_count: int
    checkout_count: int
    join_rate_percent: float
    checkout_rate_percent: float
    major: List[DashboardMajorActivityBreakdown]


class DashboardYearActivityBreakdown(BaseModel):
    year_status: str
    total_student: int
    count_student: int
    joined_count: int
    not_joined_count: int
    checkin_count: int
    checkout_count: int
    join_rate_percent: float
    checkout_rate_percent: float
    faculty: List[DashboardFacultyActivityBreakdown]


class DashboardActivityYearBreakdownData(BaseModel):
    activity: ActivityDashboardSummary
    year: List[DashboardYearActivityBreakdown]


class DashboardActivityYearBreakdownResponse(BaseModel):
    detail: str
    data: DashboardActivityYearBreakdownData


# =========================
# STUDENT DASHBOARD
# =========================

class StudentCheckPointItem(BaseModel):
    checkin_at: Optional[int] = None
    checkin_status: Optional[str] = None
    checkin_status_text: Optional[str] = None
    checkin_lat: Optional[float] = None
    checkin_lng: Optional[float] = None


class StudentCheckoutPointItem(BaseModel):
    checkout_at: Optional[int] = None
    checkout_status: Optional[str] = None
    checkout_status_text: Optional[str] = None
    checkout_lat: Optional[float] = None
    checkout_lng: Optional[float] = None


class StudentCheckDetailItem(BaseModel):
    attendance_status: str

    registered_at: Optional[int] = None

    # ชั่วโมงจิตอาสาที่ได้จริง
    earned_hours: float

    # ชั่วโมงจิตอาสาของกิจกรรม
    volunteer_hours: float

    # เวลากิจกรรมจริง
    activity_hours: float

    checkin: StudentCheckPointItem
    checkout: StudentCheckoutPointItem


class StudentDashboardActivityItem(BaseModel):
    activity_id: int
    activity_name: str

    activity_date: Optional[str] = None

    start_time: str
    end_time: str

    # เวลากิจกรรมจริง
    hours: float

    # ชั่วโมงจิตอาสาของกิจกรรม
    volunteer_hours: float

    # ชั่วโมงจิตอาสาที่ได้จริง
    earned_hours: float

    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None

    activity_status: bool

    attendance_status: str

    check_detail: Optional[StudentCheckDetailItem] = None

    checkin_at: Optional[int] = None
    checkout_at: Optional[int] = None


class StudentDashboardItem(BaseModel):
    joined_count: int
    not_joined_count: int

    checkin_count: int
    checkout_count: int

    # เวลากิจกรรมรวม
    total_activity_hours: float

    # ชั่วโมงจิตอาสารวมของกิจกรรม
    total_volunteer_hours: float

    # ชั่วโมงจิตอาสาที่ได้จริงรวม
    total_earned_hours: float

    total_activity_count: int

    join_rate_percent: float
    checkout_rate_percent: float

    activities: List[StudentDashboardActivityItem]


class StudentDashboardMessageResponse(BaseModel):
    detail: str
    data: StudentDashboardItem
