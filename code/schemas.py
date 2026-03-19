from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time, datetime

# -------------------------
# Faculty basic
# -------------------------
class FacultyCreate(BaseModel):
    faculty_name: str


class FacultyResponse(BaseModel):
    id: int
    faculty_name: str

    class Config:
        from_attributes = True


# -------------------------
# Major basic
# -------------------------
class MajorCreate(BaseModel):
    major_name: str
    faculty_id: int


class MajorResponse(BaseModel):
    id: int
    major_name: str
    faculty_id: int

    class Config:
        from_attributes = True


# -------------------------
# Create faculty with majors
# -------------------------
class FacultyWithMajorsCreate(BaseModel):
    faculty_name: str
    majors: List[str]


class MajorInFacultyResponse(BaseModel):
    id: int
    major_name: str

    class Config:
        from_attributes = True


class FacultyWithMajorsResponse(BaseModel):
    id: int
    faculty_name: str
    majors: List[MajorInFacultyResponse]

    class Config:
        from_attributes = True
        
class StudentUserCreate(BaseModel):
    username: str
    password: str


class StudentRegisterRequest(BaseModel):
    student_id: str
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    citizen_id: Optional[str] = None
    gender: Optional[str] = None

    # รับได้ทั้งชื่อและ id
    faculty_name: Optional[str] = None
    major_name: Optional[str] = None
    faculty_id: Optional[int] = None
    major_id: Optional[int] = None

    img_stu: Optional[str] = None

    user: StudentUserCreate

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

class StudentResponse(BaseModel):
    id: int
    student_id: str
    prefix: str
    first_name: str
    last_name: str
    gender: Optional[str]

    faculty_id: int
    major_id: int

    faculty_name: Optional[str]
    major_name: Optional[str]

    img_stu: Optional[str]

class Config:
    from_attributes = True
class Config:
    from_attributes = True

class StudentMessageResponse(BaseModel):
    msg: str
    data: StudentResponse

class StudentDeleteResponse(BaseModel):
    msg: str


class ActivityCreateRequest(BaseModel):
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    location: Optional[str] = None
    description: Optional[str] = None


class ActivityUpdateRequest(BaseModel):
    activity_name: Optional[str] = None
    activity_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hours: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None


class ActivityResponse(BaseModel):
    id: int
    activity_name: str
    activity_date: date
    start_time: time
    end_time: time
    hours: float
    location: Optional[str]
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ActivityMessageResponse(BaseModel):
    msg: str
    data: ActivityResponse


class ActivityDeleteResponse(BaseModel):
    msg: str