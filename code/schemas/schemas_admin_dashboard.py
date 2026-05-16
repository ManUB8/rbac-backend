from pydantic import BaseModel
from typing import List, Optional


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
    hours: float
    location: Optional[str] = None
    check_type: str
    require_registration:bool

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
    hours_count_all: float
    join_rate_percent: float
    checkout_rate_percent: float

    top_activity: Optional[ActivityDashboardSummary] = None
    selected_activity: Optional[ActivityDashboardSummary] = None

    activity_rank: List[ActivityDashboardSummary]
    faculty_rank: List[FacultyRankItem]
    major_rank: List[MajorRankItem]

    year_count: List[YearCount]
    faculty: List[FacultyWithMajorCount]


class AdminStudentMessageResponse(BaseModel):
    detail: str
    data: AdminStudentItem


class StudentDashboardActivityItem(BaseModel):
    activity_id: int
    activity_name: str
    activity_date: str
    start_time: str
    end_time: str
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool
    attendance_status: str
    checkin_at: Optional[int] = None
    checkout_at: Optional[int] = None


class StudentDashboardItem(BaseModel):
    joined_count: int
    not_joined_count: int
    checkin_count: int
    checkout_count: int
    total_hours: float
    total_activity_count: int
    join_rate_percent: float
    checkout_rate_percent: float
    activities: List[StudentDashboardActivityItem]


class StudentDashboardMessageResponse(BaseModel):
    detail: str
    data: StudentDashboardItem