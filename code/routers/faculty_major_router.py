from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import time as time_module

from database import SessionLocal
from models import Faculty, Major, User
from schemas.schemas_faculty_major import (
    FacultyCreate,
    FacultyUpdate,
    FacultyResponse,
    MajorCreate,
    MajorUpdate,
    MajorResponse,
    FacultyWithMajorsCreate,
    FacultyWithMajorsResponse,
    DeleteByAdminRequest,
)

router = APIRouter(prefix="/faculty-majors/v1", tags=["Faculty & Majors"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_unix_time() -> int:
    return int(time_module.time())


def get_admin_by_name(db: Session, admin_name: str) -> User:
    admin = (
        db.query(User)
        .filter(
            User.name == admin_name,
            User.role == "admin",
            User.is_active == True
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=403,
            detail=f"ผู้ใช้นี้ไม่มีสิทธิ์แอดมินหรือไม่พบในระบบ: {admin_name}"
        )
    return admin


@router.post("/faculties", response_model=FacultyResponse)
def create_faculty(data: FacultyCreate, db: Session = Depends(get_db)):
    admin = get_admin_by_name(db, data.created_by_name)

    existing = db.query(Faculty).filter(Faculty.faculty_name == data.faculty_name).first()
    if existing:
        raise HTTPException(status_code=500, detail=f"คณะนี้ถูกลงทะเบียนแล้ว: {data.faculty_name}")

    now = get_unix_time()

    faculty = Faculty(
        faculty_name=data.faculty_name,
        created_by_id=admin.user_id,
        created_by_name=admin.name,
        updated_by_id=admin.user_id,
        updated_by_name=admin.name,
        created_at=now,
        updated_at=now,
    )

    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@router.get("/faculties-all", response_model=list[FacultyWithMajorsResponse])
def get_all_faculties_with_majors(db: Session = Depends(get_db)):
    return db.query(Faculty).options(joinedload(Faculty.majors)).all()


@router.get("/get-one/faculties/{faculty_id}", response_model=FacultyWithMajorsResponse)
def get_faculty_with_majors(faculty_id: int, db: Session = Depends(get_db)):
    faculty = (
        db.query(Faculty)
        .options(joinedload(Faculty.majors))
        .filter(Faculty.faculty_id == faculty_id)
        .first()
    )

    if not faculty:
        raise HTTPException(status_code=500, detail="ไม่พบคณะ")

    return faculty


@router.patch("/update/faculties/{faculty_id}", response_model=FacultyResponse)
def update_faculty(faculty_id: int, data: FacultyUpdate, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.faculty_id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail="ไม่พบคณะ")

    admin = get_admin_by_name(db, data.updated_by_name)

    if data.faculty_name and data.faculty_name != faculty.faculty_name:
        existing = db.query(Faculty).filter(Faculty.faculty_name == data.faculty_name).first()
        if existing:
            raise HTTPException(status_code=500, detail=f"คณะนี้มีอยู่แล้ว: {data.faculty_name}")
        faculty.faculty_name = data.faculty_name

    faculty.updated_by_id = admin.user_id
    faculty.updated_by_name = admin.name
    faculty.updated_at = get_unix_time()

    db.commit()
    db.refresh(faculty)

    return faculty


@router.delete("/delete/faculties/{faculty_id}")
def delete_faculty(faculty_id: int, data: DeleteByAdminRequest, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.faculty_id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail="ไม่พบคณะ")

    admin = get_admin_by_name(db, data.updated_by_name)
    faculty_name = faculty.faculty_name

    faculty.updated_by_id = admin.user_id
    faculty.updated_by_name = admin.name
    faculty.updated_at = get_unix_time()
    db.flush()

    db.delete(faculty)
    db.commit()

    return {"detail": f"ลบคณะสำเร็จ: {faculty_name}"}


@router.post("/majors", response_model=MajorResponse)
def create_major(data: MajorCreate, db: Session = Depends(get_db)):
    admin = get_admin_by_name(db, data.created_by_name)

    faculty = db.query(Faculty).filter(Faculty.faculty_id == data.faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail=f"ไม่พบคณะ id: {data.faculty_id}")

    existing_major = db.query(Major).filter(
        Major.major_name == data.major_name,
        Major.faculty_id == data.faculty_id
    ).first()

    if existing_major:
        raise HTTPException(status_code=500, detail=f"สาขานี้มีการลงทะเบียนแล้วในคณะนี้: {data.major_name}")

    now = get_unix_time()

    major = Major(
        major_name=data.major_name,
        faculty_id=data.faculty_id,
        created_by_id=admin.user_id,
        created_by_name=admin.name,
        updated_by_id=admin.user_id,
        updated_by_name=admin.name,
        created_at=now,
        updated_at=now,
    )

    db.add(major)
    db.commit()
    db.refresh(major)
    return major


@router.get("/majors-all", response_model=list[MajorResponse])
def get_all_majors(db: Session = Depends(get_db)):
    return db.query(Major).all()


@router.get("/get-one/majors/{major_id}", response_model=MajorResponse)
def get_major(major_id: int, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.major_id == major_id).first()
    if not major:
        raise HTTPException(status_code=500, detail="ไม่พบสาขา")
    return major


@router.patch("/majors/{major_id}", response_model=MajorResponse)
def update_major(major_id: int, data: MajorUpdate, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.major_id == major_id).first()
    if not major:
        raise HTTPException(status_code=500, detail="ไม่พบสาขา")

    admin = get_admin_by_name(db, data.updated_by_name)

    new_major_name = data.major_name if data.major_name is not None else major.major_name
    new_faculty_id = data.faculty_id if data.faculty_id is not None else major.faculty_id

    faculty = db.query(Faculty).filter(Faculty.faculty_id == new_faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail=f"ไม่พบคณะ id: {new_faculty_id}")

    existing_major = (
        db.query(Major)
        .filter(
            Major.major_name == new_major_name,
            Major.faculty_id == new_faculty_id,
            Major.major_id != major_id
        )
        .first()
    )
    if existing_major:
        raise HTTPException(status_code=500, detail=f"สาขานี้มีอยู่แล้วในคณะนี้: {new_major_name}")

    if data.major_name is not None:
        major.major_name = data.major_name

    if data.faculty_id is not None:
        major.faculty_id = data.faculty_id

    major.updated_by_id = admin.user_id
    major.updated_by_name = admin.name
    major.updated_at = get_unix_time()

    db.commit()
    db.refresh(major)
    return major


@router.delete("/delete/majors/{major_id}")
def delete_major(major_id: int, data: DeleteByAdminRequest, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.major_id == major_id).first()
    if not major:
        raise HTTPException(status_code=500, detail="ไม่พบสาขา")

    admin = get_admin_by_name(db, data.updated_by_name)
    major_name = major.major_name

    major.updated_by_id = admin.user_id
    major.updated_by_name = admin.name
    major.updated_at = get_unix_time()
    db.flush()

    db.delete(major)
    db.commit()

    return {"detail": f"ลบสาขาสำเร็จ: {major_name}"}


@router.post("/bulk", response_model=list[FacultyWithMajorsResponse])
def create_faculties_with_majors(data: list[FacultyWithMajorsCreate], db: Session = Depends(get_db)):
    results = []

    for item in data:
        admin = get_admin_by_name(db, item.created_by_name)
        now = get_unix_time()

        faculty = db.query(Faculty).filter(Faculty.faculty_name == item.faculty_name).first()

        if not faculty:
            faculty = Faculty(
                faculty_name=item.faculty_name,
                created_by_id=admin.user_id,
                created_by_name=admin.name,
                updated_by_id=admin.user_id,
                updated_by_name=admin.name,
                created_at=now,
                updated_at=now,
            )
            db.add(faculty)
            db.flush()
        else:
            faculty.updated_by_id = admin.user_id
            faculty.updated_by_name = admin.name
            faculty.updated_at = now

        for major_name in item.majors:
            existing_major = db.query(Major).filter(
                Major.major_name == major_name,
                Major.faculty_id == faculty.faculty_id
            ).first()

            if not existing_major:
                major = Major(
                    major_name=major_name,
                    faculty_id=faculty.faculty_id,
                    created_by_id=admin.user_id,
                    created_by_name=admin.name,
                    updated_by_id=admin.user_id,
                    updated_by_name=admin.name,
                    created_at=now,
                    updated_at=now,
                )
                db.add(major)

        db.commit()

        faculty_with_majors = (
            db.query(Faculty)
            .options(joinedload(Faculty.majors))
            .filter(Faculty.faculty_id == faculty.faculty_id)
            .first()
        )

        results.append(faculty_with_majors)

    return results