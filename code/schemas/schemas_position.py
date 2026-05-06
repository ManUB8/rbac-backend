from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class PositionCreateRequest(BaseModel):
    position_name: str


class PositionUpdateRequest(BaseModel):
    position_id: int
    position_name: Optional[str] = None


class PositionResponse(BaseModel):
    position_id: int
    position_name: str
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = {"from_attributes": True}


class PositionMessageResponse(BaseModel):
    detail: str
    data: PositionResponse


class StudentPositionCreateRequest(BaseModel):
    student_id: int
    position_id: int
    start_date: date
    end_date: Optional[date] = None


class StudentPositionUpdateRequest(BaseModel):
    student_position_id: int
    position_id: Optional[int] = None
    is_current: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class StudentPositionResponse(BaseModel):
    student_position_id: int
    student_id: int
    position_id: int
    position_name: Optional[str] = None
    is_current: bool
    start_date: date
    end_date: Optional[date] = None

    model_config = {"from_attributes": True}


class StudentPositionMessageResponse(BaseModel):
    detail: str
    data: StudentPositionResponse


class StudentPositionListResponse(BaseModel):
    detail: str
    data: List[StudentPositionResponse]