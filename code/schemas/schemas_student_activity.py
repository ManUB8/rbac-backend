from pydantic import BaseModel, field_validator
from typing import  Optional,List
from datetime import datetime , date


# =========================
# STUDENT ACTIVITY
# =========================

class StudentActivityCreateRequest(BaseModel):
    student_id: str
    activity_id: int
    created_by_name: str


class StudentActivityGetOneRequest(BaseModel):
    student_activity_id: int


class StudentActivityUpdateRequest(BaseModel):
    student_activity_id: int
    student_id: Optional[str] = None
    activity_id: Optional[int] = None
    attendance_status: Optional[str] = None
    checkin_at: Optional[datetime] = None
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

class StudentActivityItemResponse(BaseModel):
    id: int
    student_id: int
    activity_id: int
    student_code: str
    full_name: str
    faculty_id: int
    faculty_name: Optional[str] = None
    major_id: int
    major_name: Optional[str] = None
    activity_name: str
    attendance_status: str
    checkin_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    class Config:
        from_attributes = True

class StudentActivityViewItemResponse(BaseModel):
    id: int
    student_id: int
    activity_id: int
    student_code: str
    full_name: str
    activity_name: str
    activity_date: date
    activity_time_text: str
    location: Optional[str] = None
    attendance_status: str
    registered_at: Optional[datetime] = None
    registered_at_text: Optional[str] = None
    checkin_at: Optional[datetime] = None

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

class StudentActivityResponse(BaseModel):
    detail: str
    data: StudentActivityViewItemResponse


class StudentActivityListResponse(BaseModel):
    detail: str
    data: List[StudentActivityViewItemResponse]


class StudentActivityFilterResponse(BaseModel):
    detail: str
    activity_id: int
    count_student: int
    data: List[StudentActivityViewItemResponse]