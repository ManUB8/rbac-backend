from pydantic import BaseModel
from typing import List, Optional


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


class StudentResponse(BaseModel):
    id: int
    student_id: str
    prefix: Optional[str]
    first_name: str
    last_name: str
    citizen_id: Optional[str]
    gender: Optional[str]
    faculty_id: int
    major_id: int
    user_id: int
    img_stu: Optional[str]

    class Config:
        from_attributes = True