from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import   datetime


# =========================
# Student
# =========================
class StudentUserCreate(BaseModel):
    username: str
    password: str
    name: Optional[str] = None


class StudentRegisterRequest(BaseModel):
    student_id: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    citizen_id: Optional[str] = None
    gender: Optional[str] = None
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    img_stu: Optional[str] = None
    user: StudentUserCreate


class StudentAdminCreateRequest(StudentRegisterRequest):
    created_by_name: str


class StudentAdminUpdateRequest(BaseModel):
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    citizen_id: Optional[str] = None
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
    citizen_id: Optional[str] = None
    gender: Optional[str] = None
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None


class StudentUserResponse(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
    id: int
    student_id: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    citizen_id: Optional[str] = None
    gender: Optional[str] = None
    faculty_id: int
    major_id: int
    user_id: int
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    deleted_by_id: Optional[int] = None
    deleted_by_name: Optional[str] = None
    deleted_at: Optional[datetime] = None
    is_deleted: Optional[bool] = False
    user: Optional[StudentUserResponse] = None

    class Config:
        from_attributes = True


class StudentMessageResponse(BaseModel):
    detail: str
    data: StudentResponse


class StudentDeleteRequest(BaseModel):
    updated_by_name: str


class StudentDeleteResponse(BaseModel):
    detail: str


class FacultyStudentSummaryResponse(BaseModel):
    faculties_name: str
    faculties_id: int
    count_major: int
    count_student: int


class MajorStudentSummaryResponse(BaseModel):
    major_name: str
    major_id: int
    count_student: int


class StudentUserInfoResponse(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True


class StudentDetailWithUserResponse(BaseModel):
    id: int
    student_id: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    citizen_id: Optional[str] = None
    gender: Optional[str] = None
    faculty_id: int
    major_id: int
    user_id: int
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    user: StudentUserInfoResponse

    class Config:
        from_attributes = True


class StudentMajorListResponse(BaseModel):
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
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    citizen_id: Optional[str] = None
    gender: Optional[str] = None
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    img_stu: Optional[str] = None
    updated_by_name: str
    user: Optional[StudentUserUpdateRequest] = None

    @field_validator(
        "citizen_id",
        "img_stu",
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