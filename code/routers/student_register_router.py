from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import SessionLocal
from models import Student, User, Faculty, Major
from schemas import (
    StudentRegisterRequest,
    StudentUpdateRequest,
    StudentResponse,
    StudentMessageResponse,
    StudentDeleteResponse,
)

router = APIRouter(prefix="/student", tags=["Student Register"])


def get_db():
    """
    เปิด/ปิด database session ให้แต่ละ request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_faculty_and_major(db: Session, faculty_id=None, faculty_name=None, major_id=None, major_name=None):
    """
    helper function สำหรับหา faculty / major
    รองรับทั้ง id และ name
    และตรวจว่าข้อมูลตรงกันจริงไหม
    """
    faculty = None
    major = None

    # -----------------------------
    # หา faculty
    # -----------------------------
    if faculty_id is not None:
        faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty ID not found")

    if faculty_name:
        faculty_by_name = db.query(Faculty).filter(Faculty.faculty_name == faculty_name).first()
        if not faculty_by_name:
            raise HTTPException(status_code=404, detail="Faculty name not found")

        if faculty and faculty.id != faculty_by_name.id:
            raise HTTPException(
                status_code=400,
                detail="faculty_id and faculty_name do not match"
            )

        faculty = faculty_by_name

    # -----------------------------
    # หา major
    # -----------------------------
    if major_id is not None:
        major = db.query(Major).filter(Major.id == major_id).first()
        if not major:
            raise HTTPException(status_code=404, detail="Major ID not found")

    if major_name:
        major_by_name = db.query(Major).filter(Major.major_name == major_name).first()
        if not major_by_name:
            raise HTTPException(status_code=404, detail="Major name not found")

        if major and major.id != major_by_name.id:
            raise HTTPException(
                status_code=400,
                detail="major_id and major_name do not match"
            )

        major = major_by_name

    # ถ้าระบุทั้ง faculty กับ major แล้วต้องเป็นคู่กัน
    if faculty and major:
        if major.faculty_id != faculty.id:
            raise HTTPException(
                status_code=400,
                detail="Selected major does not belong to selected faculty"
            )

    return faculty, major


@router.post("/register", response_model=StudentMessageResponse)
def register_student(data: StudentRegisterRequest, db: Session = Depends(get_db)):
    """
    สมัครนิสิตใหม่
    - รับได้ทั้ง faculty_name / major_name
    - และ faculty_id / major_id
    - ถ้าส่งมาทั้งชื่อและ id จะตรวจว่าตรงกันจริงไหม
    """

    # 1) ตรวจซ้ำ student_id
    existing_student = db.query(Student).filter(Student.student_id == data.student_id).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Student ID already exists")

    # 2) ตรวจซ้ำ username
    existing_user = db.query(User).filter(User.username == data.user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # 3) ตรวจซ้ำ citizen_id
    if data.citizen_id:
        existing_citizen = db.query(Student).filter(Student.citizen_id == data.citizen_id).first()
        if existing_citizen:
            raise HTTPException(status_code=400, detail="Citizen ID already exists")

    # 4) หา faculty / major
    faculty, major = resolve_faculty_and_major(
        db=db,
        faculty_id=data.faculty_id,
        faculty_name=data.faculty_name,
        major_id=data.major_id,
        major_name=data.major_name,
    )

    if not faculty:
        raise HTTPException(status_code=400, detail="Please provide faculty_id or faculty_name")

    if not major:
        raise HTTPException(status_code=400, detail="Please provide major_id or major_name")

    # 5) สร้าง user สำหรับ login
    user = User(
        username=data.user.username,
        password=data.user.password,
        role="student",
        is_active=True
    )
    db.add(user)
    db.flush()

    # 6) สร้าง student profile
    student = Student(
        student_id=data.student_id,
        prefix=data.prefix,
        first_name=data.first_name,
        last_name=data.last_name,
        citizen_id=data.citizen_id,
        gender=data.gender,
        faculty_id=faculty.id,
        major_id=major.id,
        user_id=user.id,
        img_stu=data.img_stu
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return {
        "msg": "สร้างนักศึกษาสำเร็จ",
        "data": student
    }


@router.get("/all-students", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    """
    ดึงรายการนักศึกษาทั้งหมด
    พร้อมชื่อคณะ และชื่อสาขา
    """
    students = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major)
        )
        .all()
    )

    return [
        {
            "id": student.id,
            "student_id": student.student_id,
            "prefix": student.prefix,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "citizen_id": student.citizen_id,
            "gender": student.gender,
            "faculty_id": student.faculty_id,
            "faculty_name": student.faculty.faculty_name if student.faculty else "",
            "major_id": student.major_id,
            "major_name": student.major.major_name if student.major else "",
            "user_id": student.user_id,
            "img_stu": student.img_stu,
        }
        for student in students
    ]


@router.get("/{student_db_id}", response_model=StudentResponse)
def get_student(student_db_id: int, db: Session = Depends(get_db)):
    """
    ดึงข้อมูลนักศึกษาตาม id ใน database
    """
    student = db.query(Student).filter(Student.id == student_db_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_db_id}", response_model=StudentMessageResponse)
def update_student(student_db_id: int, data: StudentUpdateRequest, db: Session = Depends(get_db)):
    """
    แก้ไขข้อมูลนักศึกษา
    รองรับแก้คณะ/สาขาทั้งแบบ id และ name
    """
    student = db.query(Student).filter(Student.id == student_db_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # ตรวจ citizen_id ซ้ำ ถ้ามีการส่งมาแก้
    if data.citizen_id:
        existing_citizen = db.query(Student).filter(
            Student.citizen_id == data.citizen_id,
            Student.id != student_db_id
        ).first()
        if existing_citizen:
            raise HTTPException(status_code=400, detail="Citizen ID already exists")

    # อัปเดตข้อมูลพื้นฐาน
    update_data = data.model_dump(exclude_unset=True)

    for field in ["prefix", "first_name", "last_name", "citizen_id", "gender", "img_stu"]:
        if field in update_data:
            setattr(student, field, update_data[field])

    # ถ้ามีการส่งข้อมูล faculty/major มา ให้ resolve ใหม่
    has_faculty_or_major_update = any([
        data.faculty_id is not None,
        data.faculty_name is not None,
        data.major_id is not None,
        data.major_name is not None
    ])

    if has_faculty_or_major_update:
        # ถ้าไม่ได้ส่ง faculty/major มาครบ จะใช้ค่าปัจจุบันเติมให้
        current_faculty = db.query(Faculty).filter(Faculty.id == student.faculty_id).first()
        current_major = db.query(Major).filter(Major.id == student.major_id).first()

        faculty, major = resolve_faculty_and_major(
            db=db,
            faculty_id=data.faculty_id if data.faculty_id is not None else current_faculty.id,
            faculty_name=data.faculty_name,
            major_id=data.major_id if data.major_id is not None else current_major.id,
            major_name=data.major_name,
        )

        if faculty:
            student.faculty_id = faculty.id
        if major:
            student.major_id = major.id

    db.commit()
    db.refresh(student)

    return {
        "msg": "แก้ไขข้อมูลนักศึกษาสำเร็จ",
        "data": student
    }


@router.delete("/{student_db_id}", response_model=StudentDeleteResponse)
def delete_student(student_db_id: int, db: Session = Depends(get_db)):
    """
    ลบนักศึกษา
    และลบ user ที่ผูกอยู่ด้วย
    """
    student = db.query(Student).filter(Student.id == student_db_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    user = db.query(User).filter(User.id == student.user_id).first()

    db.delete(student)

    # ถ้ามี user ผูกอยู่ก็ลบด้วย
    if user:
        db.delete(user)

    db.commit()

    return {
        "msg": "ลบนักศึกษาสำเร็จ"
    }