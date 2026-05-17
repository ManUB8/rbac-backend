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


YEAR_STATUS_LIST = ["ปี 1", "ปี 2", "ปี 3", "ปี 4", "บัณฑิต"]


def calc_percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def format_time_dot(value):
    if value is None:
        return ""
    return value.strftime("%H.%M")


def count_all_students(
    db: Session,
    faculty_id: int | None = None,
    major_id: int | None = None,
    year_status: str | None = None,
):
    q = db.query(func.count(Student.student_id))

    if faculty_id is not None:
        q = q.filter(Student.faculty_id == faculty_id)

    if major_id is not None:
        q = q.filter(Student.major_id == major_id)

    if year_status is not None and year_status.strip() != "":
        q = q.filter(Student.year_status == year_status)

    return q.scalar() or 0


def count_students(
    db: Session,
    activity_id: int,
    faculty_id: int | None = None,
    major_id: int | None = None,
    year_status: str | None = None,
    attendance_status: str | None = None,
):
    is_all_activity = activity_id == 0

    q = db.query(func.count(distinct(Student.student_id)))

    if not is_all_activity or attendance_status is not None:
        q = q.join(
            StudentActivity,
            StudentActivity.student_id == Student.student_id
        )

    if not is_all_activity:
        q = q.filter(StudentActivity.activity_id == activity_id)

    if attendance_status is not None:
        q = q.filter(StudentActivity.attendance_status == attendance_status)

    if faculty_id is not None:
        q = q.filter(Student.faculty_id == faculty_id)

    if major_id is not None:
        q = q.filter(Student.major_id == major_id)

    if year_status is not None and year_status.strip() != "":
        q = q.filter(Student.year_status == year_status)

    return q.scalar() or 0


def count_checkin(
    db: Session,
    activity_id: int,
    faculty_id: int | None = None,
    major_id: int | None = None,
    year_status: str | None = None,
):
    is_all_activity = activity_id == 0

    q = (
        db.query(func.count(distinct(Student.student_id)))
        .join(StudentActivity, StudentActivity.student_id == Student.student_id)
        .filter(StudentActivity.checkin_at.isnot(None))
    )

    if not is_all_activity:
        q = q.filter(StudentActivity.activity_id == activity_id)

    if faculty_id is not None:
        q = q.filter(Student.faculty_id == faculty_id)

    if major_id is not None:
        q = q.filter(Student.major_id == major_id)

    if year_status is not None and year_status.strip() != "":
        q = q.filter(Student.year_status == year_status)

    return q.scalar() or 0


def count_checkout(
    db: Session,
    activity_id: int,
    faculty_id: int | None = None,
    major_id: int | None = None,
    year_status: str | None = None,
):
    is_all_activity = activity_id == 0

    q = (
        db.query(func.count(distinct(Student.student_id)))
        .join(StudentActivity, StudentActivity.student_id == Student.student_id)
        .filter(StudentActivity.checkout_at.isnot(None))
    )

    if not is_all_activity:
        q = q.filter(StudentActivity.activity_id == activity_id)

    if faculty_id is not None:
        q = q.filter(Student.faculty_id == faculty_id)

    if major_id is not None:
        q = q.filter(Student.major_id == major_id)

    if year_status is not None and year_status.strip() != "":
        q = q.filter(Student.year_status == year_status)

    return q.scalar() or 0


def build_activity_summary(db: Session, activity: Activity):
    joined_count = count_students(
        db=db,
        activity_id=activity.activity_id,
        attendance_status="เข้าร่วม"
    )

    not_joined_count = count_students(
        db=db,
        activity_id=activity.activity_id,
        attendance_status="ไม่เข้าร่วม"
    )

    checkin_count = count_checkin(
        db=db,
        activity_id=activity.activity_id
    )

    checkout_count = count_checkout(
        db=db,
        activity_id=activity.activity_id
    )

    total_count = joined_count + not_joined_count

    return {
        "activity_id": activity.activity_id,
        "activity_name": activity.activity_name,
        "activity_date": activity.activity_date.isoformat(),
        "start_time": format_time_dot(activity.start_time),
        "end_time": format_time_dot(activity.end_time),
        "hours": float(activity.hours or 0),
        "location": activity.location,
        "check_type": activity.check_type,
        "require_registration": activity.require_registration,
        "joined_count": joined_count,
        "not_joined_count": not_joined_count,
        "checkin_count": checkin_count,
        "checkout_count": checkout_count,
        "total_count": total_count,
        "join_rate_percent": calc_percent(joined_count, total_count),
        "checkout_rate_percent": calc_percent(checkout_count, checkin_count),
    }


def build_faculty_rank_item(db: Session, faculty: Faculty, activity_id: int):
    joined_count = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty.faculty_id,
        attendance_status="เข้าร่วม"
    )

    not_joined_count = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty.faculty_id,
        attendance_status="ไม่เข้าร่วม"
    )

    checkin_count = count_checkin(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty.faculty_id
    )

    checkout_count = count_checkout(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty.faculty_id
    )

    total_student = count_all_students(
        db=db,
        faculty_id=faculty.faculty_id
    )

    total_count = joined_count + not_joined_count

    return {
        "faculty_id": faculty.faculty_id,
        "faculty_name": faculty.faculty_name,
        "total_student": total_student,
        "joined_count": joined_count,
        "not_joined_count": not_joined_count,
        "checkin_count": checkin_count,
        "checkout_count": checkout_count,
        "join_rate_percent": calc_percent(joined_count, total_count),
    }


def build_major_rank_item(db: Session, major: Major, faculty: Faculty, activity_id: int):
    joined_count = count_students(
        db=db,
        activity_id=activity_id,
        major_id=major.major_id,
        attendance_status="เข้าร่วม"
    )

    not_joined_count = count_students(
        db=db,
        activity_id=activity_id,
        major_id=major.major_id,
        attendance_status="ไม่เข้าร่วม"
    )

    checkin_count = count_checkin(
        db=db,
        activity_id=activity_id,
        major_id=major.major_id
    )

    checkout_count = count_checkout(
        db=db,
        activity_id=activity_id,
        major_id=major.major_id
    )

    total_student = count_all_students(
        db=db,
        major_id=major.major_id
    )

    total_count = joined_count + not_joined_count

    return {
        "major_id": major.major_id,
        "major_name": major.major_name,
        "faculty_id": faculty.faculty_id,
        "faculty_name": faculty.faculty_name,
        "total_student": total_student,
        "joined_count": joined_count,
        "not_joined_count": not_joined_count,
        "checkin_count": checkin_count,
        "checkout_count": checkout_count,
        "join_rate_percent": calc_percent(joined_count, total_count),
    }


@router.get("/admin/{activity_id}", response_model=AdminStudentMessageResponse)
def get_admin_dashboard(activity_id: int, db: Session = Depends(get_db)):
    is_all_activity = activity_id == 0
    activity = None

    if not is_all_activity:
        activity = (
            db.query(Activity)
            .filter(Activity.activity_id == activity_id)
            .first()
        )

        if not activity:
            raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    hours_count_all = (
        db.query(func.sum(Activity.hours))
        .filter(Activity.activity_status == True)
        .scalar()
        or 0
        if is_all_activity
        else activity.hours
    )

    activity_count = (
        db.query(func.count(Activity.activity_id))
        .filter(Activity.activity_status == True)
        .scalar()
        or 0
        if is_all_activity
        else 1
    )

    joined_count = count_students(
        db=db,
        activity_id=activity_id,
        attendance_status="เข้าร่วม"
    )

    not_joined_count = count_students(
        db=db,
        activity_id=activity_id,
        attendance_status="ไม่เข้าร่วม"
    )

    checkin_count = count_checkin(
        db=db,
        activity_id=activity_id
    )

    checkout_count = count_checkout(
        db=db,
        activity_id=activity_id
    )

    student_count_all = count_students(
        db=db,
        activity_id=activity_id
    )

    total_join_status = joined_count + not_joined_count

    join_rate_percent = calc_percent(
        joined_count,
        total_join_status
    )

    checkout_rate_percent = calc_percent(
        checkout_count,
        checkin_count
    )

    top_activity = None
    selected_activity = None
    activity_rank = []

    if is_all_activity:
        activities = (
            db.query(Activity)
            .filter(Activity.activity_status == True)
            .all()
        )

        activity_rank = [
            build_activity_summary(db, item)
            for item in activities
        ]

        activity_rank = sorted(
            activity_rank,
            key=lambda x: x["joined_count"],
            reverse=True
        )[:10]

        if activity_rank:
            top_activity = activity_rank[0]
    else:
        selected_activity = build_activity_summary(db, activity)
        top_activity = selected_activity
        activity_rank = [selected_activity]

    year_count = []

    for year in YEAR_STATUS_LIST:
        year_joined_count = count_students(
            db=db,
            activity_id=activity_id,
            year_status=year,
            attendance_status="เข้าร่วม"
        )

        year_not_joined_count = count_students(
            db=db,
            activity_id=activity_id,
            year_status=year,
            attendance_status="ไม่เข้าร่วม"
        )

        year_checkin_count = count_checkin(
            db=db,
            activity_id=activity_id,
            year_status=year
        )

        year_checkout_count = count_checkout(
            db=db,
            activity_id=activity_id,
            year_status=year
        )

        year_count.append({
            "name": year,
            "total_student": count_all_students(
                db=db,
                year_status=year
            ),
            "count_student": count_students(
                db=db,
                activity_id=activity_id,
                year_status=year
            ),
            "joined_count": year_joined_count,
            "not_joined_count": year_not_joined_count,
            "checkin_count": year_checkin_count,
            "checkout_count": year_checkout_count,
            "join_rate_percent": calc_percent(
                year_joined_count,
                year_joined_count + year_not_joined_count
            ),
        })

    faculties = (
        db.query(Faculty)
        .order_by(Faculty.faculty_id.asc())
        .all()
    )

    faculty_result = []
    faculty_rank = []
    major_rank = []

    faculty_result = []
    faculty_rank = []
    major_rank = []

    for faculty in faculties:
        faculty_rank_item = build_faculty_rank_item(
            db=db,
            faculty=faculty,
            activity_id=activity_id
        )

        faculty_rank.append(faculty_rank_item)

        majors = (
            db.query(Major)
            .filter(Major.faculty_id == faculty.faculty_id)
            .order_by(Major.major_id.asc())
            .all()
        )

        major_result = []

        for major in majors:
            major_rank_item = build_major_rank_item(
                db=db,
                major=major,
                faculty=faculty,
                activity_id=activity_id
            )

            # major_rank เอาไว้ดูละเอียด มี checkin checkout percent
            major_rank.append(major_rank_item)

            # faculty.major เอาไว้แสดงแบบง่าย
            major_result.append({
                "major_id": major.major_id,
                "major_name": major.major_name,
                "total_student": major_rank_item["total_student"],
                "joined_count": major_rank_item["joined_count"],
                "not_joined_count": major_rank_item["not_joined_count"],
            })

        # เรียงสาขาในคณะ จากเข้าร่วมมาก -> น้อย
        major_result = sorted(
            major_result,
            key=lambda x: x["joined_count"],
            reverse=True
        )

        # faculty เอาไว้แสดงแบบง่าย ไม่มี checkin checkout
        faculty_result.append({
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            "total_student": faculty_rank_item["total_student"],
            "joined_count": faculty_rank_item["joined_count"],
            "not_joined_count": faculty_rank_item["not_joined_count"],
            "major": major_result,
        })

    # faculty เรียงจากเข้าร่วมมาก -> น้อย
    faculty_result = sorted(
        faculty_result,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    # faculty_rank เรียงทั้งหมด ไม่ตัด top 10
    faculty_rank = sorted(
        faculty_rank,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    # major_rank เรียงทั้งหมด ไม่ตัด top 10
    major_rank = sorted(
        major_rank,
        key=lambda x: x["joined_count"],
        reverse=True
    )
    return {
        "detail": "success",
        "data": {
            "hours_count_all": float(hours_count_all or 0),
            "activity_count": activity_count,

            "joined_count": joined_count,
            "not_joined_count": not_joined_count,
            "checkin_count": checkin_count,
            "checkout_count": checkout_count,

            "student_count_all": student_count_all,
            "join_rate_percent": join_rate_percent,
            "checkout_rate_percent": checkout_rate_percent,

            "top_activity": top_activity,
            "selected_activity": selected_activity,

            "activity_rank": activity_rank,
            "faculty_rank": faculty_rank,
            "major_rank": major_rank,

            "year_count": year_count,
            "faculty": faculty_result,
        }
    }


@router.get("/student/{student_id}", response_model=StudentDashboardMessageResponse)
def get_student_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.student_id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="ไม่พบนักศึกษา")

    rows = (
        db.query(Activity, StudentActivity)
        .outerjoin(
            StudentActivity,
            (StudentActivity.activity_id == Activity.activity_id) &
            (StudentActivity.student_id == student_id)
        )
        .filter(Activity.activity_status == True)
        .order_by(Activity.activity_date.desc())
        .all()
    )

    joined_count = 0
    not_joined_count = 0
    checkin_count = 0
    checkout_count = 0
    total_hours = 0.0
    activities = []

    for activity, student_activity in rows:
        attendance_status = (
            student_activity.attendance_status
            if student_activity
            else "ไม่เข้าร่วม"
        )

        checkin_at = student_activity.checkin_at if student_activity else None
        checkout_at = student_activity.checkout_at if student_activity else None

        if attendance_status == "เข้าร่วม":
            joined_count += 1
            total_hours += float(activity.hours or 0)
        else:
            not_joined_count += 1

        if checkin_at is not None:
            checkin_count += 1

        if checkout_at is not None:
            checkout_count += 1

        activities.append({
            "activity_id": activity.activity_id,
            "activity_name": activity.activity_name,
            "activity_date": activity.activity_date.isoformat(),
            "start_time": format_time_dot(activity.start_time),
            "end_time": format_time_dot(activity.end_time),
            "hours": float(activity.hours or 0),
            "location": activity.location,
            "description": activity.description,
            "activity_img": activity.activity_img,
            "activity_status": activity.activity_status,
            "attendance_status": attendance_status,
            "checkin_at": checkin_at,
            "checkout_at": checkout_at,
        })

    total_activity_count = len(rows)

    return {
        "detail": "success",
        "data": {
            "joined_count": joined_count,
            "not_joined_count": not_joined_count,
            "checkin_count": checkin_count,
            "checkout_count": checkout_count,
            "total_hours": total_hours,
            "total_activity_count": total_activity_count,
            "join_rate_percent": calc_percent(joined_count, total_activity_count),
            "checkout_rate_percent": calc_percent(checkout_count, checkin_count),
            "activities": activities,
        }
    }