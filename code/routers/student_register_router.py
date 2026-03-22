from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import time as time_module

from database import SessionLocal
from models import Student, User, Faculty, Major
from schemas.schemas_student import (
    StudentRegisterRequest,
    StudentAdminCreateRequest,
    StudentUpdateRequest,
    StudentResponse,
    StudentMessageResponse,
    StudentDeleteRequest,
    StudentDeleteResponse,
    FacultyStudentSummaryResponse,
    MajorStudentSummaryItemResponse,
    StudentMajorListResponse,
    StudentAdminUpdateWithUserRequest,
    StudentDetailWithUserResponse,
)

router = APIRouter(prefix="/student/v1", tags=["Student Register"])


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


def resolve_faculty_and_major(db: Session, faculty_id=None, faculty_name=None, major_id=None, major_name=None):
    faculty = None
    major = None

    if faculty_id is not None:
        faculty = db.query(Faculty).filter(Faculty.faculty_id == faculty_id).first()
        if not faculty:
            raise HTTPException(status_code=500, detail="ไม่พบเลขรหัสคณะ")

    if faculty_name:
        faculty_by_name = db.query(Faculty).filter(Faculty.faculty_name == faculty_name).first()
        if not faculty_by_name:
            raise HTTPException(status_code=500, detail="ไม่พบชื่อคณะ")
        if faculty and faculty.faculty_id != faculty_by_name.faculty_id:
            raise HTTPException(status_code=500, detail="เลขรหัสคณะและชื่อคณะไม่ตรงกัน")
        faculty = faculty_by_name

    if major_id is not None:
        major = db.query(Major).filter(Major.major_id == major_id).first()
        if not major:
            raise HTTPException(status_code=500, detail="ไม่พบเลขรหัสสาขา")

    if major_name:
        major_by_name = db.query(Major).filter(Major.major_name == major_name).first()
        if not major_by_name:
            raise HTTPException(status_code=500, detail="ไม่พบชื่อสาขา")
        if major and major.major_id != major_by_name.major_id:
            raise HTTPException(status_code=500, detail="เลขรหัสสาขาและชื่อสาขาไม่ตรงกัน")
        major = major_by_name

    if faculty and major:
        if major.faculty_id != faculty.faculty_id:
            raise HTTPException(status_code=500, detail="สาขาที่เลือกไม่ตรงกับคณะที่มีอยู่")

    return faculty, major


@router.post("/register", response_model=StudentMessageResponse)
def register_student(data: StudentRegisterRequest, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.student_code == data.student_code).first()
    if existing_student:
        raise HTTPException(status_code=500, detail=f"รหัสนิสิตลงทะเบียนแล้ว: {data.student_code}")

    existing_user = db.query(User).filter(User.username == data.user.username).first()
    if existing_user:
        raise HTTPException(status_code=500, detail=f"ชื่อผู้ใช้นี้ถูกลงทะเบียนแล้ว: {data.user.username}")

    faculty, major = resolve_faculty_and_major(
        db=db,
        faculty_id=data.faculty_id,
        faculty_name=data.faculty_name,
        major_id=data.major_id,
        major_name=data.major_name,
    )

    if not faculty:
        raise HTTPException(status_code=500, detail="โปรดระบุเลขรหัสคณะหรือชื่อคณะ")
    if not major:
        raise HTTPException(status_code=500, detail="โปรดระบุเลขรหัสสาขาหรือชื่อสาขา")

    full_name = f"{data.first_name} {data.last_name}".strip()
    now = get_unix_time()

    user = User(
        username=data.user.username,
        password=data.user.password,
        role="student",
        name=full_name,
        is_active=True,
        created_by_name=full_name,
        updated_by_name=full_name,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.flush()

    student = Student(
        student_code=data.student_code,
        prefix=data.prefix,
        first_name=data.first_name,
        last_name=data.last_name,
        gender=data.gender,
        faculty_id=faculty.faculty_id,
        major_id=major.major_id,
        user_id=user.user_id,
        img_stu=data.img_stu,
        created_by_id=user.user_id,
        created_by_name=full_name,
        updated_by_id=user.user_id,
        updated_by_name=full_name,
        created_at=now,
        updated_at=now,
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return {"detail": "สร้างนักศึกษาสำเร็จ", "data": student}


@router.post("/admin/create", response_model=StudentMessageResponse)
def admin_create_student(data: StudentAdminCreateRequest, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.student_code == data.student_code).first()
    if existing_student:
        raise HTTPException(status_code=500, detail=f"รหัสนิสิตลงทะเบียนแล้ว: {data.student_code}")

    existing_user = db.query(User).filter(User.username == data.user.username).first()
    if existing_user:
        raise HTTPException(status_code=500, detail=f"ชื่อผู้ใช้นี้ถูกลงทะเบียนแล้ว: {data.user.username}")

    faculty, major = resolve_faculty_and_major(
        db=db,
        faculty_id=data.faculty_id,
        faculty_name=data.faculty_name,
        major_id=data.major_id,
        major_name=data.major_name,
    )

    if not faculty:
        raise HTTPException(status_code=500, detail="โปรดระบุเลขรหัสคณะหรือชื่อคณะ")
    if not major:
        raise HTTPException(status_code=500, detail="โปรดระบุเลขรหัสสาขาหรือชื่อสาขา")

    admin = get_admin_by_name(db, data.created_by_name)
    full_name = f"{data.first_name} {data.last_name}".strip()
    now = get_unix_time()

    user = User(
        username=data.user.username,
        password=data.user.password,
        role="student",
        name=full_name,
        is_active=True,
        created_by_id=admin.user_id,
        created_by_name=admin.name,
        updated_by_id=admin.user_id,
        updated_by_name=admin.name,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.flush()

    student = Student(
        student_code=data.student_code,
        prefix=data.prefix,
        first_name=data.first_name,
        last_name=data.last_name,
        gender=data.gender,
        faculty_id=faculty.faculty_id,
        major_id=major.major_id,
        user_id=user.user_id,
        img_stu=data.img_stu,
        created_by_id=admin.user_id,
        created_by_name=admin.name,
        updated_by_id=admin.user_id,
        updated_by_name=admin.name,
        created_at=now,
        updated_at=now,
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return {"detail": "แอดมินสร้างนักศึกษาสำเร็จ", "data": student}


@router.patch("/update/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, data: StudentUpdateRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=500, detail="ไม่พบนิสิต")

    update_data = data.model_dump(exclude_unset=True)

    if "faculty_id" in update_data or "faculty_name" in update_data:
        faculty = None

        if update_data.get("faculty_id") is not None:
            faculty = db.query(Faculty).filter(Faculty.faculty_id == update_data["faculty_id"]).first()
            if not faculty:
                raise HTTPException(status_code=500, detail="ไม่พบเลขรหัสคณะ")

        if update_data.get("faculty_name"):
            faculty_by_name = db.query(Faculty).filter(Faculty.faculty_name == update_data["faculty_name"]).first()
            if not faculty_by_name:
                raise HTTPException(status_code=500, detail="ไม่พบชื่อคณะ")
            if faculty and faculty.faculty_id != faculty_by_name.faculty_id:
                raise HTTPException(status_code=500, detail="เลขรหัสคณะและชื่อคณะไม่ตรงกัน")
            faculty = faculty_by_name

        if faculty:
            student.faculty_id = faculty.faculty_id

    if "major_id" in update_data or "major_name" in update_data:
        major = None

        if update_data.get("major_id") is not None:
            major = db.query(Major).filter(Major.major_id == update_data["major_id"]).first()
            if not major:
                raise HTTPException(status_code=500, detail="ไม่พบเลขรหัสสาขา")

        if update_data.get("major_name"):
            major_by_name = db.query(Major).filter(Major.major_name == update_data["major_name"]).first()
            if not major_by_name:
                raise HTTPException(status_code=500, detail="ไม่พบชื่อสาขา")
            if major and major.major_id != major_by_name.major_id:
                raise HTTPException(status_code=500, detail="เลขรหัสสาขาและชื่อสาขาไม่ตรงกัน")
            major = major_by_name

        if major:
            student.major_id = major.major_id

    if student.major_id and student.faculty_id:
        major_check = db.query(Major).filter(Major.major_id == student.major_id).first()
        if major_check and major_check.faculty_id != student.faculty_id:
            raise HTTPException(status_code=500, detail="สาขาที่เลือกไม่ตรงกับคณะที่มีอยู่")

    for key, value in update_data.items():
        if key not in ["faculty_id", "faculty_name", "major_id", "major_name"]:
            setattr(student, key, value)

    student.updated_at = get_unix_time()

    db.commit()
    db.refresh(student)
    return student


@router.patch("/admin/update-stu/{student_id}", response_model=StudentDetailWithUserResponse)
def admin_update_student_with_user(student_id: int, data: StudentAdminUpdateWithUserRequest, db: Session = Depends(get_db)):
    student = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
        )
        .filter(Student.student_id == student_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=500, detail="ไม่พบนิสิต")

    admin = get_admin_by_name(db, data.updated_by_name)
    update_data = data.model_dump(exclude_unset=True)

    if "faculty_id" in update_data or "faculty_name" in update_data:
        faculty = None
        if update_data.get("faculty_id") is not None:
            faculty = db.query(Faculty).filter(Faculty.faculty_id == update_data["faculty_id"]).first()
            if not faculty:
                raise HTTPException(status_code=500, detail="ไม่พบเลขรหัสคณะ")

        if update_data.get("faculty_name") is not None:
            faculty_by_name = db.query(Faculty).filter(Faculty.faculty_name == update_data["faculty_name"]).first()
            if not faculty_by_name:
                raise HTTPException(status_code=500, detail="ไม่พบชื่อคณะ")
            if faculty and faculty.faculty_id != faculty_by_name.faculty_id:
                raise HTTPException(status_code=500, detail="เลขรหัสคณะและชื่อคณะไม่ตรงกัน")
            faculty = faculty_by_name

        if faculty:
            student.faculty_id = faculty.faculty_id

    if "major_id" in update_data or "major_name" in update_data:
        major = None
        if update_data.get("major_id") is not None:
            major = db.query(Major).filter(Major.major_id == update_data["major_id"]).first()
            if not major:
                raise HTTPException(status_code=500, detail="ไม่พบเลขรหัสสาขา")

        if update_data.get("major_name") is not None:
            major_by_name = db.query(Major).filter(Major.major_name == update_data["major_name"]).first()
            if not major_by_name:
                raise HTTPException(status_code=500, detail="ไม่พบชื่อสาขา")
            if major and major.major_id != major_by_name.major_id:
                raise HTTPException(status_code=500, detail="เลขรหัสสาขาและชื่อสาขาไม่ตรงกัน")
            major = major_by_name

        if major:
            student.major_id = major.major_id

    if student.major_id and student.faculty_id:
        major_check = db.query(Major).filter(Major.major_id == student.major_id).first()
        if major_check and major_check.faculty_id != student.faculty_id:
            raise HTTPException(status_code=500, detail="สาขาที่เลือกไม่ตรงกับคณะที่มีอยู่")

    ignore_fields = {"faculty_id", "faculty_name", "major_id", "major_name", "updated_by_name", "user"}
    for key, value in update_data.items():
        if key not in ignore_fields:
            setattr(student, key, value)

    user_data = update_data.get("user")
    user = db.query(User).filter(User.user_id == student.user_id).first()

    if user and user_data:
        new_username = user_data.get("username")
        new_password = user_data.get("password")

        if new_username is not None:
            existing_user = db.query(User).filter(
                User.username == new_username,
                User.user_id != user.user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=500, detail=f"ชื่อผู้ใช้ถูกใช้งานไปแล้ว: {new_username}")
            user.username = new_username

        if new_password is not None:
            user.password = new_password

        full_name = f"{student.first_name or ''} {student.last_name or ''}".strip()
        user.name = full_name
        user.updated_by_id = admin.user_id
        user.updated_by_name = admin.name
        user.updated_at = get_unix_time()

    student.updated_by_id = admin.user_id
    student.updated_by_name = admin.name
    student.updated_at = get_unix_time()

    try:
        db.commit()
        db.refresh(student)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"อัปเดตข้อมูลไม่สำเร็จ: {str(e.orig)}")

    student = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
        )
        .filter(Student.student_id == student_id)
        .first()
    )

    return {
        "student_id": student.student_id,
        "student_code": student.student_code,
        "prefix": student.prefix,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "gender": student.gender,
        "faculty_id": student.faculty_id,
        "major_id": student.major_id,
        "user_id": student.user_id,
        "faculty_name": student.faculty.faculty_name if student.faculty else None,
        "major_name": student.major.major_name if student.major else None,
        "img_stu": student.img_stu,
        "created_by_id": student.created_by_id,
        "created_by_name": student.created_by_name,
        "updated_by_id": student.updated_by_id,
        "updated_by_name": student.updated_by_name,
        "created_at": student.created_at,
        "updated_at": student.updated_at,
        "user": {
            "username": student.user.username if student.user else None,
            "password": student.user.password if student.user else None,
        }
    }


@router.delete("/delete/{student_id}", response_model=StudentDeleteResponse)
def delete_student(student_id: int, data: StudentDeleteRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=500, detail="ไม่พบนิสิต")

    admin = db.query(User).filter(
        User.name == data.updated_by_name,
        User.role == "admin",
        User.is_active == True
    ).first()

    if not admin:
        raise HTTPException(status_code=403, detail="ผู้ลบต้องเป็นแอดมินเท่านั้น")

    student.updated_by_id = admin.user_id
    student.updated_by_name = admin.name
    student.updated_at = get_unix_time()

    user = db.query(User).filter(User.user_id == student.user_id).first()
    if user:
        db.delete(user)

    db.delete(student)
    db.commit()

    return {"detail": f"ลบนักศึกษาสำเร็จ รหัสนิสิต: {student.student_code}"}


@router.get("/get-all/faculties-student", response_model=list[FacultyStudentSummaryResponse])
def get_all_faculties_student(db: Session = Depends(get_db)):
    faculties = db.query(Faculty).options(joinedload(Faculty.majors)).all()

    results = []
    for faculty in faculties:
        count_major = db.query(Major).filter(Major.faculty_id == faculty.faculty_id).count()
        count_student = db.query(Student).filter(Student.faculty_id == faculty.faculty_id).count()

        results.append({
            "faculty_name": faculty.faculty_name,
            "faculty_id": faculty.faculty_id,
            "count_major": count_major,
            "count_student": count_student
        })

    return results


@router.get("/all-students", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    students = (
        db.query(Student)
        .options(joinedload(Student.faculty), joinedload(Student.major))
        .all()
    )

    return [
        {
            "student_id": student.student_id,
            "student_code": student.student_code,
            "prefix": student.prefix,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "gender": student.gender,
            "faculty_id": student.faculty_id,
            "faculty_name": student.faculty.faculty_name if student.faculty else "",
            "major_id": student.major_id,
            "major_name": student.major.major_name if student.major else "",
            "user_id": student.user_id,
            "img_stu": student.img_stu,
            "created_by_id": student.created_by_id,
            "created_by_name": student.created_by_name,
            "updated_by_id": student.updated_by_id,
            "updated_by_name": student.updated_by_name,
            "created_at": student.created_at,
            "updated_at": student.updated_at,
        }
        for student in students
    ]


@router.get("/get-one/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=500, detail="ไม่พบนิสิต")
    return student


@router.get("/get-all/major/{faculty_id}", response_model=list[MajorStudentSummaryItemResponse])
def get_all_major_by_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.faculty_id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=500, detail="ไม่พบคณะ")

    majors = db.query(Major).filter(Major.faculty_id == faculty_id).all()

    results = []
    for major in majors:
        count_student = db.query(Student).filter(Student.major_id == major.major_id).count()
        results.append({
            "major_name": major.major_name,
            "major_id": major.major_id,
            "count_student": count_student
        })

    return results


@router.get("/get-all/student-major/{major_id}", response_model=StudentMajorListResponse)
def get_all_student_by_major(major_id: int, db: Session = Depends(get_db)):
    major = db.query(Major).filter(Major.major_id == major_id).first()
    if not major:
        raise HTTPException(status_code=500, detail="ไม่พบสาขา")

    students = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
        )
        .filter(Student.major_id == major_id)
        .all()
    )

    return {
        "detail": "ดึงข้อมูลนิสิตตามสาขาสำเร็จ",
        "major_id": major.major_id,
        "major_name": major.major_name,
        "count_student": len(students),
        "student": [
            {
                "student_id": student.student_id,
                "student_code": student.student_code,
                "prefix": student.prefix,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "gender": student.gender,
                "faculty_id": student.faculty_id,
                "major_id": student.major_id,
                "user_id": student.user_id,
                "faculty_name": student.faculty.faculty_name if student.faculty else None,
                "major_name": student.major.major_name if student.major else None,
                "img_stu": student.img_stu,
                "created_by_id": student.created_by_id,
                "created_by_name": student.created_by_name,
                "updated_by_id": student.updated_by_id,
                "updated_by_name": student.updated_by_name,
                "created_at": student.created_at,
                "updated_at": student.updated_at,
                "user": {
                    "username": student.user.username if student.user else None,
                    "password": student.user.password if student.user else None
                }
            }
            for student in students
        ]
    }