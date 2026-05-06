from pydantic import BaseModel
from typing import List, Optional


class CountSummary(BaseModel):
    count_student: int
    joined_count: int
    not_joined_count: int


class YearCount(CountSummary):
    name: str


class MajorInFacultyCount(CountSummary):
    major_id: int
    major_name: str


class FacultyWithMajorCount(CountSummary):
    faculty_id: int
    faculty_name: str
    count_student: int
    joined_count: int
    not_joined_count: int
    major: List[MajorInFacultyCount]


class AdminStudentItem(BaseModel):
    activity_count: int
    joined_count: int
    not_joined_count: int
    student_count_all: int
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


class StudentDashboardItem(BaseModel):
    joined_count: int
    not_joined_count: int
    total_hours: float
    total_activity_count: int
    activities: List[StudentDashboardActivityItem]


class StudentDashboardMessageResponse(BaseModel):
    detail: str
    data: StudentDashboardItem