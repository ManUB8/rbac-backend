from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

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
    """
    เปิด/ปิด database session ให้แต่ละ request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


# =========================
# CREATE FACULTY    
# =========================
@router.post("/faculties", response_model=FacultyResponse)
def create_faculty(data: FacultyCreate, db: Session = Depends(get_db)):
    admin = get_admin_by_name(db, data.created_by_name)

    existing = db.query(Faculty).filter(Faculty.faculty_name == data.faculty_name).first()
    if existing:
        raise HTTPException(
            status_code=500,
            detail=f"คณะนี้ถูกลงทะเบียนแล้ว: {data.faculty_name}"
        )

    faculty = Faculty(
        faculty_name=data.faculty_name,
        created_by_id=admin.id,
        created_by_name=admin.name,
        updated_by_id=admin.id,
        updated_by_name=admin.name,
    )

    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


# =========================
# GET ALL FACULTIES
# =========================
@router.get("/faculties-all", response_model=list[FacultyWithMajorsResponse])
def get_all_faculties_with_majors(db: Session = Depends(get_db)):
    faculties = db.query(Faculty).options(joinedload(Faculty.majors)).all()
    return faculties


# =========================
# GET FACULTY BY ID
# =========================
@router.get("/get-one/faculties/{faculty_id}", response_model=FacultyWithMajorsResponse)
def get_faculty_with_majors(faculty_id: int, db: Session = Depends(get_db)):
    faculty = (
        db.query(Faculty)
        .options(joinedload(Faculty.majors))
        .filter(Faculty.id == faculty_id)
        .first()
    )

    if not faculty:
        raise HTTPException(status_code=500, detail="ไม่พบคณะ")

    return faculty


# =========================
# UPDATE FACULTY
# =========================
@router.patch("/update/faculties/{faculty_id}", response_model=FacultyResponse)
def update_faculty(
    faculty_id: int,
    data: FacultyUpdate,
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail="ไม่พบคณะ")

    admin = get_admin_by_name(db, data.updated_by_name)

    if data.faculty_name and data.faculty_name != faculty.faculty_name:
        existing = db.query(Faculty).filter(Faculty.faculty_name == data.faculty_name).first()
        if existing:
            raise HTTPException(
                status_code=500,
                detail=f"คณะนี้มีอยู่แล้ว: {data.faculty_name}"
            )
        faculty.faculty_name = data.faculty_name

    faculty.updated_by_id = admin.id
    faculty.updated_by_name = admin.name

    db.commit()
    db.refresh(faculty)

    return faculty


# =========================
# DELETE FACULTY
# =========================

@router.delete("/delete/faculties/{faculty_id}")
def delete_faculty(
    faculty_id: int,
    data: DeleteByAdminRequest,
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail="ไม่พบคณะ")

    admin = get_admin_by_name(db, data.updated_by_name)

    faculty_name = faculty.faculty_name

    faculty.updated_by_id = admin.id
    faculty.updated_by_name = admin.name
    db.flush()

    db.delete(faculty)
    db.commit()

    return {
        "detail": f"แอดมิน {admin.name} ลบคณะสำเร็จ: {faculty_name}"
    }

# =========================
# CREATE MAJOR
# =========================
@router.post("/majors", response_model=MajorResponse)
def create_major(data: MajorCreate, db: Session = Depends(get_db)):
    admin = get_admin_by_name(db, data.created_by_name)

    faculty = db.query(Faculty).filter(Faculty.id == data.faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail=f"ไม่พบคณะ id: {data.faculty_id}")

    existing_major = db.query(Major).filter(
        Major.major_name == data.major_name,
        Major.faculty_id == data.faculty_id
    ).first()

    if existing_major:
        raise HTTPException(
            status_code=500,
            detail=f"สาขานี้มีการลงทะเบียนแล้วในคณะนี้: {data.major_name}"
        )

    major = Major(
        major_name=data.major_name,
        faculty_id=data.faculty_id,
        created_by_id=admin.id,
        created_by_name=admin.name,
        updated_by_id=admin.id,
        updated_by_name=admin.name,
    )

    db.add(major)
    db.commit()
    db.refresh(major)
    return major


# =========================
# GET ALL MAJORS
# =========================
@router.get("/majors-all", response_model=list[MajorResponse])
def get_all_majors(db: Session = Depends(get_db)):
    majors = db.query(Major).all()
    return majors


# =========================
# GET MAJOR BY ID
# =========================
@router.get("/get-one/majors/{major_id}", response_model=MajorResponse)
def get_major(major_id: int, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=500, detail="ไม่พบสาขา")
    return major


# =========================
# UPDATE MAJOR
# =========================
@router.patch("/majors/{major_id}", response_model=MajorResponse)
def update_major(major_id: int, data: MajorUpdate, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=500, detail="ไม่พบสาขา")

    admin = get_admin_by_name(db, data.updated_by_name)

    new_major_name = data.major_name if data.major_name is not None else major.major_name
    new_faculty_id = data.faculty_id if data.faculty_id is not None else major.faculty_id

    faculty = db.query(Faculty).filter(Faculty.id == new_faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail=f"ไม่พบคณะ id: {new_faculty_id}")

    existing_major = (
        db.query(Major)
        .filter(
            Major.major_name == new_major_name,
            Major.faculty_id == new_faculty_id,
            Major.id != major_id
        )
        .first()
    )
    if existing_major:
        raise HTTPException(
            status_code=500,
            detail=f"สาขานี้มีอยู่แล้วในคณะนี้: {new_major_name}"
        )

    if data.major_name is not None:
        major.major_name = data.major_name

    if data.faculty_id is not None:
        major.faculty_id = data.faculty_id

    major.updated_by_id = admin.id
    major.updated_by_name = admin.name

    db.commit()
    db.refresh(major)
    return major


# =========================
# DELETE MAJOR
# =========================
@router.delete("/delete/majors/{major_id}")
def delete_major(
    major_id: int,
    data: DeleteByAdminRequest,
    db: Session = Depends(get_db)
):
    major = db.query(Major).filter(Major.id == major_id).first()
    if not major:
        raise HTTPException(status_code=500, detail="ไม่พบสาขา")

    admin = get_admin_by_name(db, data.updated_by_name)

    major_name = major.major_name

    # อัปเดต audit ก่อนลบ
    major.updated_by_id = admin.id
    major.updated_by_name = admin.name
    db.flush()

    db.delete(major)
    db.commit()

    return {
        "detail": f"แอดมิน {admin.name} ลบสาขาสำเร็จ: {major_name}"
    }

# =========================
# BULK CREATE FACULTIES WITH MAJORS
# =========================
@router.post("/bulk", response_model=list[FacultyWithMajorsResponse])
def create_faculties_with_majors(
    data: list[FacultyWithMajorsCreate],
    db: Session = Depends(get_db)
):
    results = []

    for item in data:
        admin = get_admin_by_name(db, item.created_by_name)

        faculty = db.query(Faculty).filter(Faculty.faculty_name == item.faculty_name).first()

        if not faculty:
            faculty = Faculty(
                faculty_name=item.faculty_name,
                created_by_id=admin.id,
                created_by_name=admin.name,
                updated_by_id=admin.id,
                updated_by_name=admin.name,
            )
            db.add(faculty)
            db.flush()
        else:
            faculty.updated_by_id = admin.id
            faculty.updated_by_name = admin.name

        for major_name in item.majors:
            existing_major = db.query(Major).filter(
                Major.major_name == major_name,
                Major.faculty_id == faculty.id
            ).first()

            if not existing_major:
                major = Major(
                    major_name=major_name,
                    faculty_id=faculty.id,
                    created_by_id=admin.id,
                    created_by_name=admin.name,
                    updated_by_id=admin.id,
                    updated_by_name=admin.name,
                )
                db.add(major)

        db.commit()

        faculty_with_majors = (
            db.query(Faculty)
            .options(joinedload(Faculty.majors))
            .filter(Faculty.id == faculty.id)
            .first()
        )

        results.append(faculty_with_majors)

    return results