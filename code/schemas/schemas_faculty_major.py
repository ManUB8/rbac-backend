from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import  datetime

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
