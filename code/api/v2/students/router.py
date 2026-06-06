from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from . import service
from .dependencies import get_db
from .interfaces import (
    AdminDeleteRequest,
    FacultyStudentSummaryResponse,
    MajorStudentSummaryItemResponse,
    StudentAdminCreateRequest,
    StudentAdminUpdateWithUserRequest,
    StudentDeleteRequest,
    StudentDeleteResponse,
    StudentDetailWithUserResponse,
    StudentFilterRequest,
    StudentFilterResponse,
    StudentMajorListResponse,
    StudentMessageResponse,
    StudentRegisterRequest,
)

router = APIRouter(prefix="/student/v2", tags=["Student V2"])


@router.post("/register", response_model=StudentMessageResponse)
def register_student(data: StudentRegisterRequest, db: Session = Depends(get_db)):
    return service.register_student(data=data, db=db)


@router.post("/admin/create", response_model=StudentMessageResponse)
def admin_create_student(data: StudentAdminCreateRequest, db: Session = Depends(get_db)):
    return service.admin_create_student(data=data, db=db)


@router.patch("/admin/update-stu/{student_id}", response_model=StudentDetailWithUserResponse)
def admin_update_student_with_user(
    student_id: int,
    data: StudentAdminUpdateWithUserRequest,
    db: Session = Depends(get_db),
):
    return service.admin_update_student_with_user(student_id=student_id, data=data, db=db)


@router.delete("/delete/{student_id}", response_model=StudentDeleteResponse)
def delete_student(
    student_id: int,
    data: StudentDeleteRequest,
    db: Session = Depends(get_db),
):
    return service.delete_student(student_id=student_id, data=data, db=db)


@router.get("/all-students", response_model=list[StudentDetailWithUserResponse])
def get_students(db: Session = Depends(get_db)):
    return service.get_students(db=db)


@router.get("/get-one/{student_id}", response_model=StudentDetailWithUserResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return service.get_student(student_id=student_id, db=db)


@router.get("/get-all/faculties-student", response_model=list[FacultyStudentSummaryResponse])
def get_all_faculties_student(db: Session = Depends(get_db)):
    return service.get_all_faculties_student(db=db)


@router.get("/get-all/major/{faculty_id}", response_model=list[MajorStudentSummaryItemResponse])
def get_all_major_by_faculty(faculty_id: int, db: Session = Depends(get_db)):
    return service.get_all_major_by_faculty(faculty_id=faculty_id, db=db)


@router.get("/get-all/student-major/{major_id}", response_model=StudentMajorListResponse)
def get_all_student_by_major(major_id: int, db: Session = Depends(get_db)):
    return service.get_all_student_by_major(major_id=major_id, db=db)


@router.post("/get-all/filter", response_model=StudentFilterResponse)
def filter_students_by_body(body: StudentFilterRequest, db: Session = Depends(get_db)):
    return service.filter_students_by_body(body=body, db=db)


@router.get("/get-all/filter", response_model=StudentFilterResponse)
def filter_students_by_query(
    search: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(10),
    faculty_id: int = Query(0),
    major_id: int = Query(0),
    position_id: int = Query(0),
    year_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return service.filter_students_by_query(
        db=db,
        search=search,
        page=page,
        limit=limit,
        faculty_id=faculty_id,
        major_id=major_id,
        position_id=position_id,
        year_status=year_status,
    )


@router.delete("/admin/delete-all-students")
def delete_all_students(body: AdminDeleteRequest, db: Session = Depends(get_db)):
    return service.delete_all_students(body=body, db=db)


@router.get("/summary/year/{year_status}")
def get_student_summary_by_year(year_status: str, db: Session = Depends(get_db)):
    return service.get_student_summary_by_year(year_status=year_status, db=db)


@router.get("/summary/year-code/{year_status}/{student_code_prefix}")
def get_student_summary_by_year_and_code_prefix(
    year_status: str,
    student_code_prefix: str,
    db: Session = Depends(get_db),
):
    return service.get_student_summary_by_year_and_code_prefix(
        year_status=year_status,
        student_code_prefix=student_code_prefix,
        db=db,
    )


@router.get("/summary/code-prefix/{student_code_prefix}")
def get_student_summary_by_code_prefix(
    student_code_prefix: str,
    db: Session = Depends(get_db),
):
    return service.get_student_summary_by_code_prefix(
        student_code_prefix=student_code_prefix,
        db=db,
    )
