from pydantic import BaseModel
from typing import List, Optional


class DeleteByAdminRequest(BaseModel):
    updated_by_name: str


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
    faculty_id: int
    faculty_name: str

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


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
    major_id: int
    major_name: str
    faculty_id: int

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


# =========================
# Faculty + majors
# =========================
class MajorInFacultyResponse(BaseModel):
    major_id: int
    major_name: str

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class FacultyWithMajorsCreate(BaseModel):
    faculty_name: str
    majors: List[str]
    created_by_name: str


class FacultyWithMajorsResponse(BaseModel):
    faculty_id: int
    faculty_name: str
    majors: List[MajorInFacultyResponse]

    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_by_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }