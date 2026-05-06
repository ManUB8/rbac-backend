from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from database import SessionLocal
from models import Activity, Student, Faculty, Major, StudentActivity
from schemas.schemas_admin_dashboard import (
    AdminStudentMessageResponse,
    StudentDashboardMessageResponse,
)

router = APIRouter(prefix="/dashboard/v1", tags=["Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


YEAR_MAP = {
    "69": "ปี 1",
    "68": "ปี 2",
    "67": "ปี 3",
    "66": "ปี 4",
}


def count_students(
    db: Session,
    activity_id: int,
    faculty_id: int | None = None,
    major_id: int | None = None,
    year_prefix: str | None = None,
    attendance_status: str | None = None,
):
    is_all = activity_id == 0

    q = db.query(func.count(distinct(Student.student_id)))

    if not is_all or attendance_status:
        q = q.join(
            StudentActivity,
            StudentActivity.student_id == Student.student_id
        )

    if not is_all:
        q = q.filter(StudentActivity.activity_id == activity_id)

    if attendance_status:
        q = q.filter(StudentActivity.attendance_status == attendance_status)

    if faculty_id:
        q = q.filter(Student.faculty_id == faculty_id)

    if major_id:
        q = q.filter(Student.major_id == major_id)

    if year_prefix:
        q = q.filter(Student.student_code.like(f"{year_prefix}%"))

    return q.scalar() or 0


@router.get("/admin/{activity_id}", response_model=AdminStudentMessageResponse)
def get_admin_dashboard(activity_id: int, db: Session = Depends(get_db)):
    is_all = activity_id == 0

    if not is_all:
        activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    student_count_all = count_students(db, activity_id)

    activity_count = (
        db.query(func.count(Activity.activity_id)).scalar() or 0
        if is_all
        else 1
    )

    joined_count = count_students(
        db,
        activity_id,
        attendance_status="เข้าร่วม"
    )

    not_joined_count = count_students(
        db,
        activity_id,
        attendance_status="ไม่เข้าร่วม"
    )

    year_count = []

    for prefix, year_name in YEAR_MAP.items():
        year_count.append({
            "name": year_name,
            "count_student": count_students(
                db,
                activity_id,
                year_prefix=prefix
            ),
            "joined_count": count_students(
                db,
                activity_id,
                year_prefix=prefix,
                attendance_status="เข้าร่วม"
            ),
            "not_joined_count": count_students(
                db,
                activity_id,
                year_prefix=prefix,
                attendance_status="ไม่เข้าร่วม"
            ),
        })

    faculties = (
        db.query(Faculty)
        .order_by(Faculty.faculty_id.asc())
        .all()
    )

    faculty_result = []

    for faculty in faculties:
        majors = (
            db.query(Major)
            .filter(Major.faculty_id == faculty.faculty_id)
            .order_by(Major.major_id.asc())
            .all()
        )

        major_result = []

        for major in majors:
            major_result.append({
                "major_id": major.major_id,
                "major_name": major.major_name,
                "count_student": count_students(
                    db,
                    activity_id,
                    major_id=major.major_id
                ),
                "joined_count": count_students(
                    db,
                    activity_id,
                    major_id=major.major_id,
                    attendance_status="เข้าร่วม"
                ),
                "not_joined_count": count_students(
                    db,
                    activity_id,
                    major_id=major.major_id,
                    attendance_status="ไม่เข้าร่วม"
                ),
            })

        faculty_result.append({
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            "count_student": count_students(
                db,
                activity_id,
                faculty_id=faculty.faculty_id
            ),
            "joined_count": count_students(
                db,
                activity_id,
                faculty_id=faculty.faculty_id,
                attendance_status="เข้าร่วม"
            ),
            "not_joined_count": count_students(
                db,
                activity_id,
                faculty_id=faculty.faculty_id,
                attendance_status="ไม่เข้าร่วม"
            ),
            "major": major_result,
        })

    return {
        "detail": "success",
        "data": {
            "student_count_all": student_count_all,
            "activity_count": activity_count,
            "joined_count": joined_count,
            "not_joined_count": not_joined_count,
            "year_count": year_count,
            "faculty": faculty_result,
        }
    }
    
@router.get("/student/{student_id}", response_model=StudentDashboardMessageResponse)
def get_student_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนักศึกษา")

    # 🔥 ดึงกิจกรรมทั้งหมด + join สถานะของ student
    rows = (
        db.query(Activity, StudentActivity)
        .outerjoin(
            StudentActivity,
            (StudentActivity.activity_id == Activity.activity_id) &
            (StudentActivity.student_id == student_id)
        )
        .filter(Activity.activity_status == True)  # 👈 เพิ่มตรงนี้
        .order_by(Activity.activity_date.desc())
        .all()
    )

    joined_count = 0
    not_joined_count = 0
    total_hours = 0.0
    activities = []

    for activity, student_activity in rows:
        # ถ้าไม่มี record = ไม่เข้าร่วม
        attendance_status = (
            student_activity.attendance_status
            if student_activity
            else "ไม่เข้าร่วม"
        )

        is_joined = attendance_status == "เข้าร่วม"

        if is_joined:
            joined_count += 1
            total_hours += float(activity.hours or 0)
        else:
            not_joined_count += 1

        activities.append({
            "activity_id": activity.activity_id,
            "activity_name": activity.activity_name,
            "activity_date": activity.activity_date.isoformat(),
            "start_time": activity.start_time.strftime("%H.%M"),
            "end_time": activity.end_time.strftime("%H.%M"),
            "hours": float(activity.hours or 0),
            "location": activity.location,
            "description": activity.description,
            "activity_img": activity.activity_img,
            "activity_status": activity.activity_status,
            "attendance_status": attendance_status,
        })

    return {
        "detail": "success",
        "data": {
            "joined_count": joined_count,
            "not_joined_count": not_joined_count,
            "total_hours": total_hours,
            "total_activity_count": len(rows),  # 👈 จำนวนกิจกรรมทั้งหมดในระบบ
            "activities": activities,
        }
    }