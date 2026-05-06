from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import time as time_module
from datetime import date

from database import get_db
from models import Position, Student, StudentPosition
from schemas.schemas_position import (
    PositionCreateRequest,
    PositionUpdateRequest,
    PositionResponse,
    PositionMessageResponse,
    StudentPositionCreateRequest,
    StudentPositionUpdateRequest,
    StudentPositionMessageResponse,
    StudentPositionListResponse,
)

router = APIRouter(prefix="/position/v1", tags=["Position"])


def get_unix_time() -> int:
    return int(time_module.time())


def build_student_position_response(item: StudentPosition):
    return {
        "student_position_id": item.student_position_id,
        "student_id": item.student_id,
        "position_id": item.position_id,
        "position_name": item.position.position_name if item.position else None,
        "is_current": item.is_current,
        "start_date": item.start_date,
        "end_date": item.end_date,
    }


# =========================
# Position CRUD
# =========================

@router.post("/create", response_model=PositionMessageResponse)
def create_position(body: PositionCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(Position).filter(
        Position.position_name == body.position_name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="มีตำแหน่งนี้อยู่แล้ว")

    now = get_unix_time()

    position = Position(
        position_name=body.position_name,
        created_at=now,
        updated_at=now,
    )

    db.add(position)
    db.commit()
    db.refresh(position)

    return {
        "detail": "สร้างตำแหน่งสำเร็จ",
        "data": position
    }


@router.get("/get-all", response_model=list[PositionResponse])
def get_all_positions(db: Session = Depends(get_db)):
    return db.query(Position).order_by(Position.position_id.asc()).all()


@router.get("/get-one/{position_id}", response_model=PositionResponse)
def get_position_by_id(position_id: int, db: Session = Depends(get_db)):
    position = db.query(Position).filter(Position.position_id == position_id).first()

    if not position:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่ง")

    return position


@router.patch("/update/{position_id}", response_model=PositionMessageResponse)
def update_position(
    position_id: int,
    body: PositionUpdateRequest,
    db: Session = Depends(get_db)
):
    if position_id != body.position_id:
        raise HTTPException(status_code=400, detail="position_id ไม่ตรงกัน")

    position = db.query(Position).filter(Position.position_id == position_id).first()

    if not position:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่ง")

    update_data = body.model_dump(exclude_unset=True)

    if "position_name" in update_data:
        duplicate = db.query(Position).filter(
            Position.position_name == update_data["position_name"],
            Position.position_id != position_id
        ).first()

        if duplicate:
            raise HTTPException(status_code=400, detail="มีชื่อตำแหน่งนี้อยู่แล้ว")

    for key, value in update_data.items():
        if key != "position_id":
            setattr(position, key, value)

    position.updated_at = get_unix_time()

    db.commit()
    db.refresh(position)

    return {
        "detail": "แก้ไขตำแหน่งสำเร็จ",
        "data": position
    }


@router.delete("/delete/{position_id}")
def delete_position(position_id: int, db: Session = Depends(get_db)):
    position = db.query(Position).filter(Position.position_id == position_id).first()

    if not position:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่ง")

    used = db.query(StudentPosition).filter(
        StudentPosition.position_id == position_id
    ).first()

    if used:
        raise HTTPException(
            status_code=400,
            detail="ไม่สามารถลบตำแหน่งนี้ได้ เพราะมีนิสิตใช้งานอยู่"
        )

    db.delete(position)
    db.commit()

    return {
        "detail": "ลบตำแหน่งสำเร็จ",
        "position_id": position_id
    }


# =========================
# Student Position CRUD
# =========================

@router.post("/student-position/create", response_model=StudentPositionMessageResponse)
def create_student_position(
    body: StudentPositionCreateRequest,
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.student_id == body.student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนิสิต")

    position = db.query(Position).filter(Position.position_id == body.position_id).first()

    if not position:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่ง")

    if body.end_date is not None and body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="end_date ต้องมากกว่า start_date")

    now = get_unix_time()

    # ปิดตำแหน่งปัจจุบันเก่าก่อน
    current_items = db.query(StudentPosition).filter(
        StudentPosition.student_id == body.student_id,
        StudentPosition.is_current == True
    ).all()

    for item in current_items:
        item.is_current = False
        item.end_date = body.start_date
        item.updated_at = now

    new_item = StudentPosition(
        student_id=body.student_id,
        position_id=body.position_id,
        is_current=True if body.end_date is None else False,
        start_date=body.start_date,
        end_date=body.end_date,
        created_at=now,
        updated_at=now,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    new_item = (
        db.query(StudentPosition)
        .options(joinedload(StudentPosition.position))
        .filter(StudentPosition.student_position_id == new_item.student_position_id)
        .first()
    )

    return {
        "detail": "เพิ่มตำแหน่งให้นิสิตสำเร็จ",
        "data": build_student_position_response(new_item)
    }


@router.get("/student-position/student/{student_id}", response_model=StudentPositionListResponse)
def get_student_positions(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนิสิต")

    items = (
        db.query(StudentPosition)
        .options(joinedload(StudentPosition.position))
        .filter(StudentPosition.student_id == student_id)
        .order_by(StudentPosition.is_current.desc(), StudentPosition.start_date.desc())
        .all()
    )

    return {
        "detail": "ดึงข้อมูลตำแหน่งนิสิตสำเร็จ",
        "data": [build_student_position_response(item) for item in items]
    }


@router.patch("/student-position/update/{student_position_id}", response_model=StudentPositionMessageResponse)
def update_student_position(
    student_position_id: int,
    body: StudentPositionUpdateRequest,
    db: Session = Depends(get_db)
):
    if student_position_id != body.student_position_id:
        raise HTTPException(status_code=400, detail="student_position_id ไม่ตรงกัน")

    item = (
        db.query(StudentPosition)
        .options(joinedload(StudentPosition.position))
        .filter(StudentPosition.student_position_id == student_position_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่งของนิสิต")

    update_data = body.model_dump(exclude_unset=True)

    if "position_id" in update_data:
        position = db.query(Position).filter(
            Position.position_id == update_data["position_id"]
        ).first()

        if not position:
            raise HTTPException(status_code=404, detail="ไม่พบตำแหน่ง")

    new_start_date = update_data.get("start_date", item.start_date)
    new_end_date = update_data.get("end_date", item.end_date)

    if new_end_date is not None and new_end_date < new_start_date:
        raise HTTPException(status_code=400, detail="end_date ต้องมากกว่า start_date")

    for key, value in update_data.items():
        if key != "student_position_id":
            setattr(item, key, value)

    item.updated_at = get_unix_time()

    db.commit()
    db.refresh(item)

    item = (
        db.query(StudentPosition)
        .options(joinedload(StudentPosition.position))
        .filter(StudentPosition.student_position_id == student_position_id)
        .first()
    )

    return {
        "detail": "แก้ไขตำแหน่งนิสิตสำเร็จ",
        "data": build_student_position_response(item)
    }


@router.delete("/student-position/delete/{student_position_id}")
def delete_student_position(student_position_id: int, db: Session = Depends(get_db)):
    item = db.query(StudentPosition).filter(
        StudentPosition.student_position_id == student_position_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="ไม่พบตำแหน่งของนิสิต")

    db.delete(item)
    db.commit()

    return {
        "detail": "ลบตำแหน่งนิสิตสำเร็จ",
        "student_position_id": student_position_id
    }