from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal
from datetime import date, time, datetime


# =========================
# Faculty
# =========================

class FacultyCreate(BaseModel):
    faculty_name: str
    created_by_name: str


class FacultyUpdate(BaseModel):
    faculty_name: Optional[str] = None
    updated_by_name: str


class FacultyResponse(BaseModel):
    id: int
    faculty_name: str

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
class DeleteByAdminRequest(BaseModel):
    updated_by_name: str

# =========================
# Major
# =========================

class MajorCreate(BaseModel):
    major_name: str
    faculty_id: int
    created_by_name: str


class MajorUpdate(BaseModel):
    major_name: Optional[str] = None
    faculty_id: Optional[int] = None
    updated_by_name: str


class MajorResponse(BaseModel):
    id: int
    major_name: str
    faculty_id: int

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================
# Faculty + majors
# =========================

class MajorInFacultyResponse(BaseModel):
    id: int
    major_name: str

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class FacultyWithMajorsCreate(BaseModel):
    faculty_name: str
    majors: List[str]
    created_by_name: str


class FacultyWithMajorsResponse(BaseModel):
    id: int
    faculty_name: str
    majors: List[MajorInFacultyResponse]

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    class Config:
        from_attributes = True

# =========================
# Student
# =========================

class StudentUserInfoResponse(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True

class FacultyStudentSummaryResponse(BaseModel):
    faculties_name: str
    faculties_id: int
    count_major: int
    count_student: int


class MajorStudentSummaryResponse(BaseModel):
    major_name: str
    major_id: int
    count_student: int


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

class StudentUserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

    @field_validator("username", "password", mode="before")
    @classmethod
    def empty_user_string_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    

class StudentMajorListResponse(BaseModel):
    count_student: int
    student: List[StudentDetailWithUserResponse]


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

# =========================
# Activity
# =========================
class ActivityCreateRequest(BaseModel):
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool
    created_by_name: str


class ActivityUpdateRequest(BaseModel):
    activity_id: int
    activity_name: Optional[str] = None
    activity_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    updated_by_name: str
    activity_status: bool


class ActivityDeleteRequest(BaseModel):
    activity_id: int
    updated_by_name: str


class ActivityResponse(BaseModel):
    id: int
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None
    activity_img: Optional[str] = None
    activity_status: bool

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ActivityMessageResponse(BaseModel):
    detail: str
    data: ActivityResponse

class ActivityDeleteResponse(BaseModel):
    detail: str
    activity_id: int
    activity_status: bool
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    
# =========================
# User
# =========================

class UserDeleteRequest(BaseModel):
    deleted_by_name: str
    deleted_user_id: int

class UserDeleteResponse(BaseModel):
    detail: str
    deleted_by: str
    deleted_user: str

class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: Literal["admin", "student"]
    name: str

    created_by_name: Optional[str] = None
    updated_by_name: Optional[str] = None


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Literal["admin", "student"]] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None

    updated_by_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    name: Optional[str] = None
    is_active: bool

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserMessageResponse(BaseModel):
    detail: str
    data: UserResponse

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    id: int
    username: str
    name: Optional[str] = None

    class Config:
        from_attributes = True

class UserLoginRequest(BaseModel):
    username: str
    password: str

class StudentDeleteRequest(BaseModel):
    updated_by_name: str

class StudentDeleteResponse(BaseModel):
    detail: str

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