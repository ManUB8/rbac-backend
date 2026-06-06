from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
import time as time_module
from typing import Optional
from sqlalchemy import func, or_
from models import Student, User, Faculty, Major, Position, StudentPosition, StudentActivity
from . import repository
from .constants import DELETE_ALLOWED_ADMIN_NAMES
from .interfaces import (
    AdminDeleteRequest,
    StudentAdminCreateRequest,
    StudentAdminUpdateWithUserRequest,
    StudentDeleteRequest,
    StudentFilterRequest,
    StudentRegisterRequest,
    YEAR_STATUS_LIST,
)
from .serializers import build_student_response


def get_unix_time() -> int:
    return int(time_module.time())


def get_admin_by_name(db: Session, admin_name: str) -> User:
    admin = repository.get_active_admin_by_name(db, admin_name)

    if not admin:
        raise HTTPException(
            status_code=403,
            detail=f"ผู้ใช้นี้ไม่มีสิทธิ์แอดมินหรือไม่พบในระบบ: {admin_name}"
        )

    return admin


def get_delete_admin_by_name(db: Session, admin_name: str) -> User:
    admin = get_admin_by_name(db, admin_name)

    if admin.name not in DELETE_ALLOWED_ADMIN_NAMES:
        raise HTTPException(
            status_code=403,
            detail="แอดมินนี้ไม่มีสิทธิ์ลบนิสิต"
        )

    return admin


def get_student_with_relations(db: Session, student_id: int):
    return repository.get_student_with_relations(db, student_id)
    
    
def resolve_faculty_and_major(
    db: Session,
    faculty_id=None,
    faculty_name=None,
    major_id=None,
    major_name=None
):
    faculty = None
    major = None

    if faculty_id is not None:
        faculty = repository.get_faculty_by_id(db, faculty_id)
        if not faculty:
            raise HTTPException(status_code=404, detail="ไม่พบเลขรหัสคณะ")

    if faculty_name:
        faculty_by_name = repository.get_faculty_by_name(db, faculty_name)
        if not faculty_by_name:
            raise HTTPException(status_code=404, detail="ไม่พบชื่อคณะ")

        if faculty and faculty.faculty_id != faculty_by_name.faculty_id:
            raise HTTPException(status_code=400, detail="เลขรหัสคณะและชื่อคณะไม่ตรงกัน")

        faculty = faculty_by_name

    if major_id is not None:
        major = repository.get_major_by_id(db, major_id)
        if not major:
            raise HTTPException(status_code=404, detail="ไม่พบเลขรหัสสาขา")

    if major_name:
        major_by_name = repository.get_major_by_name(db, major_name)
        if not major_by_name:
            raise HTTPException(status_code=404, detail="ไม่พบชื่อสาขา")

        if major and major.major_id != major_by_name.major_id:
            raise HTTPException(status_code=400, detail="เลขรหัสสาขาและชื่อสาขาไม่ตรงกัน")

        major = major_by_name

    if faculty and major and major.faculty_id != faculty.faculty_id:
        raise HTTPException(status_code=400, detail="สาขาที่เลือกไม่ตรงกับคณะที่มีอยู่")

    return faculty, major

def assign_student_position(db: Session, student_id: int, position_body, now: int):
    if position_body is None or position_body.position_id is None:
        return None

    position = repository.get_position_by_id(db, position_body.position_id)

    if not position:
        raise HTTPException(status_code=400, detail="ไม่พบตำแหน่ง")

    if position_body.start_date is None:
        raise HTTPException(status_code=400, detail="กรุณาระบุ start_date ของตำแหน่ง")

    if position_body.end_date is not None and position_body.end_date < position_body.start_date:
        raise HTTPException(status_code=400, detail="end_date ต้องมากกว่า start_date")

    current_position = repository.get_current_student_position(db, student_id)

    # ถ้าตำแหน่งเดิมเหมือนเดิม ให้ update วันที่เฉย ๆ
    if current_position and current_position.position_id == position_body.position_id:
        current_position.start_date = position_body.start_date
        current_position.end_date = position_body.end_date
        current_position.is_current = True if position_body.end_date is None else False
        current_position.updated_at = now
        db.flush()
        return current_position

    # ถ้าเปลี่ยนตำแหน่งใหม่ ให้ปิดตำแหน่งเก่า
    if current_position:
        current_position.is_current = False
        current_position.end_date = position_body.start_date
        current_position.updated_at = now

    new_position = StudentPosition(
        student_id=student_id,
        position_id=position_body.position_id,
        is_current=True if position_body.end_date is None else False,
        start_date=position_body.start_date,
        end_date=position_body.end_date,
        created_at=now,
        updated_at=now,
    )

    db.add(new_position)
    db.flush()

    return new_position

# ==========================================================
# Register: Student สมัครเอง
# POST /student/v2/register
# ==========================================================
def register_student(data: StudentRegisterRequest, db: Session):
    existing_student = (
        db.query(Student)
        .filter(Student.student_code == data.student_code)
        .first()
    )
    if existing_student:
        raise HTTPException(status_code=400, detail=f"รหัสนิสิตลงทะเบียนแล้ว: {data.student_code}")

    existing_user = (
        db.query(User)
        .filter(User.username == data.user.username)
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail=f"ชื่อผู้ใช้นี้ถูกลงทะเบียนแล้ว: {data.user.username}")

    faculty, major = resolve_faculty_and_major(
        db=db,
        faculty_id=data.faculty_id,
        faculty_name=data.faculty_name,
        major_id=data.major_id,
        major_name=data.major_name,
    )

    if not faculty:
        raise HTTPException(status_code=400, detail="โปรดระบุเลขรหัสคณะหรือชื่อคณะ")
    if not major:
        raise HTTPException(status_code=400, detail="โปรดระบุเลขรหัสสาขาหรือชื่อสาขา")

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
        year_status=data.year_status,
        created_by_id=user.user_id,
        created_by_name=full_name,
        updated_by_id=user.user_id,
        updated_by_name=full_name,
        created_at=now,
        updated_at=now,
    )

    db.add(student)
    db.flush()

    assign_student_position(
        db=db,
        student_id=student.student_id,
        position_body=data.position,
        now=now
    )

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"สร้างนิสิตไม่สำเร็จ: {str(e.orig)}")

    student = get_student_with_relations(db, student.student_id)

    return {
        "detail": "สร้างนักศึกษาสำเร็จ",
        "data": build_student_response(student)
    }


# ==========================================================
# Admin Create
# POST /student/v2/admin/create
# ==========================================================
def admin_create_student(data: StudentAdminCreateRequest, db: Session):
    admin = get_admin_by_name(db, data.created_by_name)

    existing_student = (
        db.query(Student)
        .filter(Student.student_code == data.student_code)
        .first()
    )
    if existing_student:
        raise HTTPException(status_code=400, detail=f"รหัสนิสิตลงทะเบียนแล้ว: {data.student_code}")

    existing_user = (
        db.query(User)
        .filter(User.username == data.user.username)
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail=f"ชื่อผู้ใช้นี้ถูกลงทะเบียนแล้ว: {data.user.username}")

    faculty, major = resolve_faculty_and_major(
        db=db,
        faculty_id=data.faculty_id,
        faculty_name=data.faculty_name,
        major_id=data.major_id,
        major_name=data.major_name,
    )

    if not faculty:
        raise HTTPException(status_code=400, detail="โปรดระบุเลขรหัสคณะหรือชื่อคณะ")
    if not major:
        raise HTTPException(status_code=400, detail="โปรดระบุเลขรหัสสาขาหรือชื่อสาขา")

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
        year_status=data.year_status,
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
    db.flush()

    assign_student_position(
        db=db,
        student_id=student.student_id,
        position_body=data.position,
        now=now
    )

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"แอดมินสร้างนิสิตไม่สำเร็จ: {str(e.orig)}")

    student = get_student_with_relations(db, student.student_id)

    return {
        "detail": "แอดมินสร้างนักศึกษาสำเร็จ",
        "data": build_student_response(student)
    }


# ==========================================================
# Admin Update Only
# PATCH /student/v2/admin/update-stu/{student_id}
# ==========================================================
def admin_update_student_with_user(
    student_id: int,
    data: StudentAdminUpdateWithUserRequest,
    db: Session
):
    if student_id != data.student_id:
        raise HTTPException(status_code=400, detail="student_id ใน URL และ body ไม่ตรงกัน")

    student = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
            joinedload(Student.student_positions).joinedload(StudentPosition.position),
        )
        .filter(Student.student_id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนิสิต")

    admin = get_admin_by_name(db, data.updated_by_name)
    update_data = data.model_dump(exclude_unset=True)

    if "student_code" in update_data and update_data["student_code"] is not None:
        duplicate_student = (
            db.query(Student)
            .filter(
                Student.student_code == update_data["student_code"],
                Student.student_id != student_id
            )
            .first()
        )
        if duplicate_student:
            raise HTTPException(status_code=400, detail=f"รหัสนิสิตถูกใช้งานแล้ว: {update_data['student_code']}")

    if "faculty_id" in update_data or "faculty_name" in update_data:
        faculty = None

        if update_data.get("faculty_id") is not None:
            faculty = db.query(Faculty).filter(Faculty.faculty_id == update_data["faculty_id"]).first()
            if not faculty:
                raise HTTPException(status_code=404, detail="ไม่พบเลขรหัสคณะ")

        if update_data.get("faculty_name") is not None:
            faculty_by_name = db.query(Faculty).filter(Faculty.faculty_name == update_data["faculty_name"]).first()
            if not faculty_by_name:
                raise HTTPException(status_code=404, detail="ไม่พบชื่อคณะ")

            if faculty and faculty.faculty_id != faculty_by_name.faculty_id:
                raise HTTPException(status_code=400, detail="เลขรหัสคณะและชื่อคณะไม่ตรงกัน")

            faculty = faculty_by_name

        if faculty:
            student.faculty_id = faculty.faculty_id

    if "major_id" in update_data or "major_name" in update_data:
        major = None

        if update_data.get("major_id") is not None:
            major = db.query(Major).filter(Major.major_id == update_data["major_id"]).first()
            if not major:
                raise HTTPException(status_code=404, detail="ไม่พบเลขรหัสสาขา")

        if update_data.get("major_name") is not None:
            major_by_name = db.query(Major).filter(Major.major_name == update_data["major_name"]).first()
            if not major_by_name:
                raise HTTPException(status_code=404, detail="ไม่พบชื่อสาขา")

            if major and major.major_id != major_by_name.major_id:
                raise HTTPException(status_code=400, detail="เลขรหัสสาขาและชื่อสาขาไม่ตรงกัน")

            major = major_by_name

        if major:
            student.major_id = major.major_id

    if student.major_id and student.faculty_id:
        major_check = db.query(Major).filter(Major.major_id == student.major_id).first()
        if major_check and major_check.faculty_id != student.faculty_id:
            raise HTTPException(status_code=400, detail="สาขาที่เลือกไม่ตรงกับคณะที่มีอยู่")

    ignore_fields = {
        "student_id",
        "faculty_id",
        "faculty_name",
        "major_id",
        "major_name",
        "updated_by_name",
        "user",
        "position",
    }

    for key, value in update_data.items():
        if key not in ignore_fields:
            setattr(student, key, value)

    user_data = update_data.get("user")
    user = db.query(User).filter(User.user_id == student.user_id).first()

    if user and user_data:
        new_username = user_data.get("username")
        new_password = user_data.get("password")

        if new_username is not None:
            existing_user = (
                db.query(User)
                .filter(
                    User.username == new_username,
                    User.user_id != user.user_id
                )
                .first()
            )

            if existing_user:
                raise HTTPException(status_code=400, detail=f"ชื่อผู้ใช้ถูกใช้งานไปแล้ว: {new_username}")

            user.username = new_username

        if new_password is not None:
            user.password = new_password

        full_name = f"{student.first_name or ''} {student.last_name or ''}".strip()
        user.name = full_name
        user.updated_by_id = admin.user_id
        user.updated_by_name = admin.name
        user.updated_at = get_unix_time()

    now = get_unix_time()

    if data.position is not None:
        assign_student_position(
            db=db,
            student_id=student.student_id,
            position_body=data.position,
            now=now
        )

    student.updated_by_id = admin.user_id
    student.updated_by_name = admin.name
    student.updated_at = now

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"อัปเดตข้อมูลไม่สำเร็จ: {str(e.orig)}")

    student = get_student_with_relations(db, student_id)

    return build_student_response(student)


# ==========================================================
# Delete เฉพาะ admin: mangpo, first, soda
# DELETE /student/v2/delete/{student_id}
# ==========================================================
def delete_student(
    student_id: int,
    data: StudentDeleteRequest,
    db: Session
):
    if student_id != data.student_id:
        raise HTTPException(
            status_code=400,
            detail="student_id ใน URL และ body ไม่ตรงกัน"
        )

    student = (
        db.query(Student)
        .options(joinedload(Student.user))
        .filter(Student.student_id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบนิสิต"
        )

    admin = get_delete_admin_by_name(db, data.updated_by_name)

    student_code = student.student_code

    # หา user จาก username = student_code
    user = (
        db.query(User)
        .filter(User.username == student_code)
        .first()
    )

    # ลบข้อมูลกิจกรรมของนิสิตก่อน
    db.query(StudentActivity).filter(
        StudentActivity.student_id == student.student_id
    ).delete()

    # ลบนิสิต
    db.delete(student)

    # ลบ user ถ้ามี
    if user:
        db.delete(user)

    db.commit()

    return {
        "detail": f"แอดมิน {admin.name} ลบนักศึกษาสำเร็จ รหัสนิสิต: {student_code}",
        "student_id": student_id,
        "updated_by_id": admin.user_id,
        "updated_by_name": admin.name,
    }
    
# ==========================================================
# Get All Students
# GET /student/v2/all-students
# ==========================================================
def get_students(db: Session):
    students = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
            joinedload(Student.student_positions).joinedload(StudentPosition.position),
        )
        .order_by(Student.student_id.desc())
        .all()
    )

    return [build_student_response(student) for student in students]


# ==========================================================
# Get One Student
# GET /student/v2/get-one/{student_id}
# ==========================================================
def get_student(student_id: int, db: Session):
    student = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
            joinedload(Student.student_positions).joinedload(StudentPosition.position),
        )
        .filter(Student.student_id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(status_code=500, detail="ไม่พบนิสิต")

    return build_student_response(student)


# ==========================================================
# Summary: Faculties Student
# GET /student/v2/get-all/faculties-student
# ==========================================================
def get_all_faculties_student(db: Session):
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


# ==========================================================
# Get Majors By Faculty
# GET /student/v2/get-all/major/{faculty_id}
# ==========================================================
def get_all_major_by_faculty(faculty_id: int, db: Session):
    faculty = repository.get_faculty_by_id(db, faculty_id)

    if not faculty:
        raise HTTPException(status_code=404, detail="ไม่พบคณะ")

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


# ==========================================================
# Get Students By Major
# GET /student/v2/get-all/student-major/{major_id}
# ==========================================================
def get_all_student_by_major(major_id: int, db: Session):
    major = repository.get_major_by_id(db, major_id)

    if not major:
        raise HTTPException(status_code=404, detail="ไม่พบสาขา")

    students = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
            joinedload(Student.student_positions).joinedload(StudentPosition.position),
        )
        .filter(Student.major_id == major_id)
        .all()
    )

    return {
        "detail": "ดึงข้อมูลนิสิตตามสาขาสำเร็จ",
        "major_id": major.major_id,
        "major_name": major.major_name,
        "count_student": len(students),
        "student": [build_student_response(student) for student in students]
    }
    

def get_year_status_summary(db: Session):
    counts = dict(
        db.query(Student.year_status, func.count(Student.student_id))
        .group_by(Student.year_status)
        .all()
    )

    return [
        {
            "year_status": year_status,
            "count_student": counts.get(year_status, 0),
        }
        for year_status in YEAR_STATUS_LIST
    ]


def filter_students_by_body(
    body: StudentFilterRequest,
    db: Session
):
    page = body.page if body.page > 0 else 1
    limit = body.limit if body.limit > 0 else 10
    offset = (page - 1) * limit

    query = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
            joinedload(Student.student_positions).joinedload(StudentPosition.position),
        )
    )

    if body.search:
        search_text = f"%{body.search.strip()}%"
        query = query.filter(
            or_(
                Student.student_code.ilike(search_text),
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
            )
        )

    if body.faculty_id is not None:
        query = query.filter(Student.faculty_id == body.faculty_id)

    if body.major_id is not None:
        query = query.filter(Student.major_id == body.major_id)

    if body.year_status is not None:
        query = query.filter(Student.year_status == body.year_status)

    if body.position_id is not None:
        query = (
            query
            .join(StudentPosition, StudentPosition.student_id == Student.student_id)
            .filter(
                StudentPosition.position_id == body.position_id,
                StudentPosition.is_current == True
            )
        )

    total_all = query.count()

    students = (
        query
        .order_by(Student.student_id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_page = (total_all + limit - 1) // limit

    return {
        "detail": "ดึงข้อมูลนิสิตสำเร็จ",
        "page": page,
        "limit": limit,
        "total_all": total_all,
        "total_page": total_page,
        "year_status_summary": get_year_status_summary(db),
        "data": [build_student_response(student) for student in students],
    }
    
    
def filter_students_by_query(
    db: Session,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    faculty_id: int = 0,
    major_id: int = 0,
    position_id: int = 0,
    year_status: Optional[str] = None,
):
    query = db.query(Student)

    if search is not None and search.strip() != "":
        search_text = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Student.student_code.ilike(search_text),
                Student.first_name.ilike(search_text),
                Student.last_name.ilike(search_text),
            )
        )

    if faculty_id != 0:
        query = query.filter(Student.faculty_id == faculty_id)

    if major_id != 0:
        query = query.filter(Student.major_id == major_id)

    if position_id != 0:
        query = (
            query
            .join(StudentPosition, StudentPosition.student_id == Student.student_id)
            .filter(
                StudentPosition.position_id == position_id,
                StudentPosition.is_current == True
            )
        )

    if year_status is not None and year_status.strip() != "":
        query = query.filter(Student.year_status == year_status)

    total_all = query.count()

    page = page if page > 0 else 1
    limit = limit if limit > 0 else 10
    offset = (page - 1) * limit

    students = (
        query
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            joinedload(Student.user),
            joinedload(Student.student_positions).joinedload(StudentPosition.position),
        )
        .order_by(Student.student_id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_page = (total_all + limit - 1) // limit

    return {
        "detail": "ดึงข้อมูลนิสิตสำเร็จ",
        "page": page,
        "limit": limit,
        "total_all": total_all,
        "total_page": total_page,
        "year_status_summary": get_year_status_summary(db),
        "data": [build_student_response(student) for student in students],
    }
    
def delete_all_students(
    body: AdminDeleteRequest,
    db: Session
):
    # =========================
    # นับข้อมูลก่อนลบ
    # =========================
    total_student_activity = db.query(StudentActivity).count()
    total_students = db.query(Student).count()

    # =========================
    # ดึง user_id ของ student
    # =========================
    student_user_ids = (
        db.query(Student.user_id)
        .filter(Student.user_id.isnot(None))
        .all()
    )

    user_ids = [item[0] for item in student_user_ids]

    # =========================
    # ลบ student activities ก่อน
    # =========================
    db.query(StudentActivity).delete()

    # =========================
    # ลบ students
    # =========================
    db.query(Student).delete()

    # =========================
    # ลบเฉพาะ user role student
    # กัน admin หาย
    # =========================
    deleted_users = 0

    if len(user_ids) > 0:
        deleted_users = (
            db.query(User)
            .filter(
                User.user_id.in_(user_ids),
                User.role == "student"
            )
            .delete(synchronize_session=False)
        )

    # =========================
    # commit
    # =========================
    db.commit()

    return {
        "detail": "ลบนิสิตและบัญชีผู้ใช้ทั้งหมดสำเร็จ",
        "total_deleted_student_activity": total_student_activity,
        "total_deleted_students": total_students,
        "total_deleted_users": deleted_users
    }


def get_student_summary_by_year(year_status: str, db: Session):
    students = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
        )
        .filter(Student.year_status == year_status)
        .all()
    )

    faculty_map = {}

    for student in students:
        faculty_id = student.faculty_id
        faculty_name = student.faculty.faculty_name if student.faculty else "ไม่ระบุคณะ"

        major_id = student.major_id
        major_name = student.major.major_name if student.major else "ไม่ระบุสาขา"

        if faculty_id not in faculty_map:
            faculty_map[faculty_id] = {
                "faculty_id": faculty_id,
                "faculty_name": faculty_name,
                "count_student": 0,
                "majors": {}
            }

        faculty_map[faculty_id]["count_student"] += 1

        if major_id not in faculty_map[faculty_id]["majors"]:
            faculty_map[faculty_id]["majors"][major_id] = {
                "major_id": major_id,
                "major_name": major_name,
                "count_student": 0
            }

        faculty_map[faculty_id]["majors"][major_id]["count_student"] += 1

    return {
        "detail": f"สรุปจำนวนนิสิต {year_status} สำเร็จ",
        "year_status": year_status,
        "count_student": len(students),
        "faculty": [
            {
                **faculty,
                "majors": list(faculty["majors"].values())
            }
            for faculty in faculty_map.values()
        ]
    }
    
    
def get_student_summary_by_year_and_code_prefix(
    year_status: str,
    student_code_prefix: str,
    db: Session
):
    # กันส่งมาไม่ครบ / ไม่ใช่ 4 ตัว
    if len(student_code_prefix) != 4 or not student_code_prefix.isdigit():
        raise HTTPException(
            status_code=400,
            detail="กรุณาส่งเลขรหัสนิสิตด้านหน้า 4 ตัว เช่น 6901"
        )

    students = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
        )
        .filter(
            Student.year_status == year_status,
            Student.student_code.like(f"{student_code_prefix}%")
        )
        .all()
    )

    faculty_map = {}

    for student in students:
        faculty_id = student.faculty_id
        faculty_name = student.faculty.faculty_name if student.faculty else "ไม่ระบุคณะ"

        major_id = student.major_id
        major_name = student.major.major_name if student.major else "ไม่ระบุสาขา"

        if faculty_id not in faculty_map:
            faculty_map[faculty_id] = {
                "faculty_id": faculty_id,
                "faculty_name": faculty_name,
                "count_student": 0,
                "majors": {}
            }

        faculty_map[faculty_id]["count_student"] += 1

        if major_id not in faculty_map[faculty_id]["majors"]:
            faculty_map[faculty_id]["majors"][major_id] = {
                "major_id": major_id,
                "major_name": major_name,
                "count_student": 0
            }

        faculty_map[faculty_id]["majors"][major_id]["count_student"] += 1

    return {
        "detail": f"สรุปจำนวนนิสิต {year_status} รหัสขึ้นต้น {student_code_prefix} สำเร็จ",
        "year_status": year_status,
        "student_code_prefix": student_code_prefix,
        "count_student": len(students),
        "faculty": [
            {
                **faculty,
                "majors": list(faculty["majors"].values())
            }
            for faculty in faculty_map.values()
        ]
    }
    
    
def get_student_summary_by_code_prefix(
    student_code_prefix: str,
    db: Session
):
    # ตรวจสอบ 4 หลัก
    if len(student_code_prefix) != 4 or not student_code_prefix.isdigit():
        raise HTTPException(
            status_code=400,
            detail="กรุณาส่งเลขรหัสนิสิตด้านหน้า 4 ตัว เช่น 6901"
        )

    students = (
        db.query(Student)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
        )
        .filter(
            Student.student_code.like(f"{student_code_prefix}%")
        )
        .all()
    )

    faculty_map = {}

    for student in students:
        faculty_id = student.faculty_id
        faculty_name = student.faculty.faculty_name if student.faculty else "ไม่ระบุคณะ"

        major_id = student.major_id
        major_name = student.major.major_name if student.major else "ไม่ระบุสาขา"

        if faculty_id not in faculty_map:
            faculty_map[faculty_id] = {
                "faculty_id": faculty_id,
                "faculty_name": faculty_name,
                "count_student": 0,
                "majors": {}
            }

        faculty_map[faculty_id]["count_student"] += 1

        if major_id not in faculty_map[faculty_id]["majors"]:
            faculty_map[faculty_id]["majors"][major_id] = {
                "major_id": major_id,
                "major_name": major_name,
                "count_student": 0
            }

        faculty_map[faculty_id]["majors"][major_id]["count_student"] += 1

    return {
        "detail": f"สรุปจำนวนนิสิตรหัสขึ้นต้น {student_code_prefix} สำเร็จ",
        "student_code_prefix": student_code_prefix,
        "count_student": len(students),
        "faculty": [
            {
                **faculty,
                "majors": list(faculty["majors"].values())
            }
            for faculty in faculty_map.values()
        ]
    }
