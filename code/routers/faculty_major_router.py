from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import SessionLocal
from models import Faculty, Major
from schemas import (
    FacultyCreate,
    FacultyResponse,
    MajorCreate,
    MajorResponse,
    FacultyWithMajorsCreate,
    FacultyWithMajorsResponse,
)

router = APIRouter(prefix="/faculty-majors/v1", tags=["Faculty & Majors"])


def get_db():
    """
    เปิด/ปิด database session ให้แต่ละ request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/faculties", response_model=FacultyResponse)
def create_faculty(data: FacultyCreate, db: Session = Depends(get_db)):
    """
    สร้างคณะเดี่ยว
    """
    existing = db.query(Faculty).filter(Faculty.faculty_name == data.faculty_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="คณะนี้ถูกลงทะเบียนแล้ว")

    faculty = Faculty(faculty_name=data.faculty_name)
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@router.post("/majors", response_model=MajorResponse)
def create_major(data: MajorCreate, db: Session = Depends(get_db)):
    """
    สร้างสาขาเดี่ยว โดยต้องระบุ faculty_id
    """
    faculty = db.query(Faculty).filter(Faculty.id == data.faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="ไม่พบคณะ")

    existing_major = db.query(Major).filter(
        Major.major_name == data.major_name,
        Major.faculty_id == data.faculty_id
    ).first()
    if existing_major:
        raise HTTPException(status_code=400, detail="สาขานี้มีการลงทะเบียนแล้วในคณะนี้แล้ว")

    major = Major(
        major_name=data.major_name,
        faculty_id=data.faculty_id
    )
    db.add(major)
    db.commit()
    db.refresh(major)
    return major


@router.post("/bulk", response_model=list[FacultyWithMajorsResponse])
def create_faculties_with_majors(
    data: list[FacultyWithMajorsCreate],
    db: Session = Depends(get_db)
):
    """
    สร้างหลายคณะพร้อมหลายสาขาในครั้งเดียว
    เหมาะกับข้อมูลชุดใหญ่ที่นายส่งมา
    """
    results = []

    for item in data:
        # ตรวจว่าคณะนี้มีอยู่แล้วหรือยัง
        faculty = db.query(Faculty).filter(Faculty.faculty_name == item.faculty_name).first()

        # ถ้ายังไม่มี -> สร้างใหม่
        if not faculty:
            faculty = Faculty(faculty_name=item.faculty_name)
            db.add(faculty)
            db.flush()  # เพื่อให้ได้ faculty.id ทันที

        # วนเพิ่มสาขา
        for major_name in item.majors:
            existing_major = db.query(Major).filter(
                Major.major_name == major_name,
                Major.faculty_id == faculty.id
            ).first()

            if not existing_major:
                major = Major(
                    major_name=major_name,
                    faculty_id=faculty.id
                )
                db.add(major)

        db.commit()

        # โหลดข้อมูลล่าสุดกลับมา
        faculty_with_majors = (
            db.query(Faculty)
            .options(joinedload(Faculty.majors))
            .filter(Faculty.id == faculty.id)
            .first()
        )

        results.append(faculty_with_majors)

    return results


@router.get("/faculties", response_model=list[FacultyWithMajorsResponse])
def get_all_faculties_with_majors(db: Session = Depends(get_db)):
    """
    ดึงคณะทั้งหมด พร้อมสาขาทั้งหมด
    """
    faculties = db.query(Faculty).options(joinedload(Faculty.majors)).all()
    return faculties


@router.get("/faculties/{faculty_id}", response_model=FacultyWithMajorsResponse)
def get_faculty_with_majors(faculty_id: int, db: Session = Depends(get_db)):
    """
    ดึงคณะตาม id พร้อมสาขา
    """
    faculty = (
        db.query(Faculty)
        .options(joinedload(Faculty.majors))
        .filter(Faculty.id == faculty_id)
        .first()
    )

    if not faculty:
        raise HTTPException(status_code=404, detail="ไม่พบคณะ")

    return faculty


@router.patch("/faculties/{faculty_id}", response_model=FacultyResponse)
def update_faculty(faculty_id: int, data: FacultyCreate, db: Session = Depends(get_db)):
    """
    แก้ชื่อคณะ
    """
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="ไม่พบคณะ")

    faculty.faculty_name = data.faculty_name
    db.commit()
    db.refresh(faculty)
    return faculty


@router.patch("/majors/{major_id}", response_model=MajorResponse)
def update_major(major_id: int, data: MajorCreate, db: Session = Depends(get_db)):
    """
    แก้ชื่อสาขา หรือย้ายสาขาไปอีกคณะ
    """
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=404, detail="ไม่พบสาขา")

    faculty = db.query(Faculty).filter(Faculty.id == data.faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="ไม่พบคณะ")

    major.major_name = data.major_name
    major.faculty_id = data.faculty_id
    db.commit()
    db.refresh(major)
    return major


@router.delete("/faculties/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    """
    ลบคณะ
    ถ้าลบคณะ สาขาในคณะนั้นจะถูกลบตามด้วย
    """
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="ไม่พบคณะ")

    db.delete(faculty)
    db.commit()
    return {"message": "Faculty deleted"}


@router.delete("/majors/{major_id}")
def delete_major(major_id: int, db: Session = Depends(get_db)):
    """
    ลบสาขาเดี่ยว
    """
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=404, detail="ไม่พบสาขา")

    db.delete(major)
    db.commit()
    return {"message": "Major deleted"}