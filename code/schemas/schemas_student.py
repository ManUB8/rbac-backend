from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date

YEAR_STATUS_LIST = ["ปี 1", "ปี 2", "ปี 3", "ปี 4", "บัณฑิต"]


def validate_year_status(value):
    if value is None:
        return None

    if value not in YEAR_STATUS_LIST:
        raise ValueError("year_status ต้องเป็น ปี 1, ปี 2, ปี 3, ปี 4 หรือ บัณฑิต")

    return value
    
class StudentPositionBody(BaseModel):
    position_id: Optional[int] = None
    position_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
class AdminActionRequest(BaseModel):
    updated_by_name: str


class StudentUserCreate(BaseModel):
    username: str
    password: str
    name: Optional[str] = None


class StudentRegisterRequest(BaseModel):
    student_code: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    gender: Optional[str] = None
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None
    position: Optional[StudentPositionBody] = None
    year_status: Optional[str] = None

    @field_validator("year_status")
    @classmethod
    def validate_year_status_field(cls, value):
        return validate_year_status(value)
    user: StudentUserCreate


class StudentAdminCreateRequest(StudentRegisterRequest):
    created_by_name: str


class StudentAdminUpdateRequest(BaseModel):
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None
    updated_by_name: str


class StudentUpdateRequest(BaseModel):
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None


class StudentUserResponse(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class StudentCurrentPositionResponse(BaseModel):
    position_id: Optional[int] = None
    position_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class StudentResponse(BaseModel):
    student_id: int
    student_code: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    gender: Optional[str] = None
    year_status: Optional[str] = None

    faculty_id: int
    major_id: int
    user_id: int
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None

    position: Optional[StudentCurrentPositionResponse] = None

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    user: Optional[StudentUserResponse] = None

    model_config = {
        "from_attributes": True
    }

class StudentMessageResponse(BaseModel):
    detail: str
    data: StudentResponse


class StudentDeleteRequest(BaseModel):
    student_id: int
    updated_by_name: str


class StudentDeleteResponse(BaseModel):
    detail: str


class MajorStudentSummaryRequest(BaseModel):
    faculty_id: int
    updated_by_name: str


class MajorStudentSummaryItemResponse(BaseModel):
    major_name: str
    major_id: int
    count_student: int


class FacultyStudentSummaryRequest(BaseModel):
    updated_by_name: str


class FacultyStudentSummaryResponse(BaseModel):
    faculty_name: str
    faculty_id: int
    count_major: int
    count_student: int


class MajorStudentSummaryResponse(BaseModel):
    detail: str
    faculty_id: int
    faculty_name: str
    data: List[MajorStudentSummaryItemResponse]


class StudentUserInfoResponse(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class StudentDetailWithUserResponse(BaseModel):
    student_id: int
    student_code: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    gender: Optional[str] = None
    faculty_id: int
    major_id: int
    user_id: int
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None
    position: Optional[StudentCurrentPositionResponse] = None
    year_status: Optional[str] = None

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    user: StudentUserInfoResponse

    model_config = {
        "from_attributes": True
    }


class StudentMajorListRequest(BaseModel):
    major_id: int
    updated_by_name: str


class StudentMajorListResponse(BaseModel):
    detail: str
    major_id: int
    major_name: str
    count_student: int
    student: List[StudentDetailWithUserResponse]


class StudentUserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    @field_validator("username", "password", mode="before")
    @classmethod
    def empty_user_string_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class StudentAdminUpdateWithUserRequest(BaseModel):
    student_id: int
    student_code: Optional[str] = None
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None
    updated_by_name: str
    position: Optional[StudentPositionBody] = None
    user: Optional[StudentUserUpdateRequest] = None
    year_status: Optional[str] = None

    @field_validator("year_status")
    @classmethod
    def validate_year_status_field(cls, value):
        return validate_year_status(value)

    @field_validator(
        "prefix",
        "first_name",
        "last_name",
        "gender",
        "faculty_name",
        "major_name",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class StudentFilterRequest(BaseModel):
    search: Optional[str] = None
    page: int = 1
    limit: int = 10
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    year_status: Optional[str] = None
    position_id: Optional[int] = None

    @field_validator("year_status")
    @classmethod
    def validate_year_status_field(cls, value):
        return validate_year_status(value)


class StudentFilterResponse(BaseModel):
    detail: str
    page: int
    limit: int
    total_all: int
    total_page: int
    data: List[StudentDetailWithUserResponse]
    
    
class AdminDeleteRequest(BaseModel):
    updated_by_name: str