from pydantic import BaseModel, field_validator
from typing import  Optional
from datetime import datetime


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


class StudentActivityResponse(BaseModel):
    detail: str
    data: dict


class StudentActivityListResponse(BaseModel):
    detail: str
    data: list


class StudentActivityDeleteResponse(BaseModel):
    detail: str
    student_activity_id: int
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None