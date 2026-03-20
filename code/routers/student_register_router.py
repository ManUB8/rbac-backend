from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Student, User, Faculty, Major
from schemas import StudentRegisterRequest,StudentRegisterResponse

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


@router.post("/register", response_model=StudentRegisterResponse)
def register_student(data: StudentRegisterRequest, db: Session = Depends(get_db)):
    """
    สมัครนิสิตใหม่
    - รับได้ทั้ง faculty_name / major_name
    - และ faculty_id / major_id
    - ถ้าส่งมาทั้งชื่อและ id จะตรวจว่าตรงกันจริงไหม
    """

    # -----------------------------
    # 1) ตรวจซ้ำ student_id
    # -----------------------------
    existing_student = db.query(Student).filter(Student.student_id == data.student_id).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Student ID already exists")

    # -----------------------------
    # 2) ตรวจซ้ำ username
    # -----------------------------
    existing_user = db.query(User).filter(User.username == data.user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # -----------------------------
    # 3) ตรวจซ้ำ citizen_id
    # -----------------------------
    if data.citizen_id:
        existing_citizen = db.query(Student).filter(Student.citizen_id == data.citizen_id).first()
        if existing_citizen:
            raise HTTPException(status_code=400, detail="Citizen ID already exists")

    # -----------------------------
    # 4) หา faculty
    # -----------------------------
    faculty = None

    if data.faculty_id is not None:
        faculty = db.query(Faculty).filter(Faculty.id == data.faculty_id).first()
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty ID not found")

    if data.faculty_name:
        faculty_by_name = db.query(Faculty).filter(Faculty.faculty_name == data.faculty_name).first()
        if not faculty_by_name:
            raise HTTPException(status_code=404, detail="Faculty name not found")

        # ถ้าส่งมาทั้ง faculty_id และ faculty_name ต้องตรงกัน
        if faculty and faculty.id != faculty_by_name.id:
            raise HTTPException(
                status_code=400,
                detail="faculty_id and faculty_name do not match"
            )

        faculty = faculty_by_name

    if not faculty:
        raise HTTPException(
            status_code=400,
            detail="Please provide faculty_id or faculty_name"
        )

    # -----------------------------
    # 5) หา major
    # -----------------------------
    major = None

    if data.major_id is not None:
        major = db.query(Major).filter(Major.id == data.major_id).first()
        if not major:
            raise HTTPException(status_code=404, detail="Major ID not found")

    if data.major_name:
        major_by_name = db.query(Major).filter(Major.major_name == data.major_name).first()
        if not major_by_name:
            raise HTTPException(status_code=404, detail="Major name not found")

        # ถ้าส่งมาทั้ง major_id และ major_name ต้องตรงกัน
        if major and major.id != major_by_name.id:
            raise HTTPException(
                status_code=400,
                detail="major_id and major_name do not match"
            )

        major = major_by_name

    if not major:
        raise HTTPException(
            status_code=400,
            detail="Please provide major_id or major_name"
        )

    # -----------------------------
    # 6) ตรวจว่า major ต้องอยู่ใน faculty เดียวกัน
    # -----------------------------
    if major.faculty_id != faculty.id:
        raise HTTPException(
            status_code=400,
            detail="Selected major does not belong to selected faculty"
        )

    # -----------------------------
    # 7) สร้าง user สำหรับ login
    # -----------------------------
    user = User(
        username=data.user.username,
        password=data.user.password,
        role="student",
        is_active=True
    )
    db.add(user)
    db.flush()  # เพื่อให้ได้ user.id ก่อน commit

    # -----------------------------
    # 8) สร้าง student profile
    # -----------------------------
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