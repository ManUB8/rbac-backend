from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import case, func, distinct
from typing import Optional

from database import SessionLocal
from models import Activity, Student, Faculty, Major, StudentActivity
from schemas.schemas_admin_dashboard import (
    AdminStudentMessageResponse,
    DashboardActivityYearBreakdownResponse,
    StudentDashboardMessageResponse,
)

router = APIRouter(prefix="/dashboard/v1", tags=["Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


YEAR_STATUS_LIST = ["ปี 1", "ปี 2", "ปี 3", "ปี 4"]


def get_scan_status_text(status, valid_text: str, manual_text: str):
    if status == "valid":
        return valid_text

    if status == "manual":
        return manual_text

    return None


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
    faculty_id: Optional[int] = None,
    major_id: Optional[int] = None,
    year_status: Optional[str] = None,
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
    faculty_id: Optional[int] = None,
    major_id: Optional[int] = None,
    year_status: Optional[str] = None,
    attendance_status: Optional[str] = None,
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
    faculty_id: Optional[int] = None,
    major_id: Optional[int] = None,
    year_status: Optional[str] = None,
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
    faculty_id: Optional[int] = None,
    major_id: Optional[int] = None,
    year_status: Optional[str] = None,
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
        "activity_date": activity.activity_date.isoformat() if activity.activity_date else "",
        "start_time": format_time_dot(activity.start_time),
        "end_time": format_time_dot(activity.end_time),

        "hours": float(activity.hours or 0),
        "volunteer_hours": float(activity.volunteer_hours or 0),

        "location": activity.location,
        "check_type": activity.check_type,
        "require_registration": bool(activity.require_registration),

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


def build_activity_count_summary(
    db: Session,
    activity_id: int,
    faculty_id: Optional[int] = None,
    major_id: Optional[int] = None,
    year_status: Optional[str] = None,
):
    joined_count = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
        attendance_status="เข้าร่วม"
    )

    not_joined_count = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
        attendance_status="ไม่เข้าร่วม"
    )

    checkin_count = count_checkin(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status
    )

    checkout_count = count_checkout(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status
    )

    count_student = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status
    )

    total_student = count_all_students(
        db=db,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status
    )

    return {
        "total_student": total_student,
        "count_student": count_student,
        "joined_count": joined_count,
        "not_joined_count": not_joined_count,
        "checkin_count": checkin_count,
        "checkout_count": checkout_count,
        "join_rate_percent": calc_percent(
            joined_count,
            joined_count + not_joined_count
        ),
        "checkout_rate_percent": calc_percent(checkout_count, checkin_count),
    }


def get_dashboard_year_statuses(db: Session):
    year_rows = (
        db.query(Student.year_status)
        .filter(Student.year_status.isnot(None))
        .distinct()
        .all()
    )

    existing_years = [
        row[0]
        for row in year_rows
        if row[0] is not None and str(row[0]).strip() != ""
    ]

    result = []
    for year in YEAR_STATUS_LIST + sorted(existing_years):
        if year not in result:
            result.append(year)

    return result


def empty_activity_summary():
    return {
        "total_student": 0,
        "count_student": 0,
        "joined_count": 0,
        "not_joined_count": 0,
        "checkin_count": 0,
        "checkout_count": 0,
        "join_rate_percent": 0.0,
        "checkout_rate_percent": 0.0,
    }


def finalize_activity_summary(summary: dict):
    summary["join_rate_percent"] = calc_percent(
        summary["joined_count"],
        summary["joined_count"] + summary["not_joined_count"]
    )
    summary["checkout_rate_percent"] = calc_percent(
        summary["checkout_count"],
        summary["checkin_count"]
    )
    return summary


def add_activity_summary(target: dict, source: dict):
    for key in [
        "total_student",
        "count_student",
        "joined_count",
        "not_joined_count",
        "checkin_count",
        "checkout_count",
    ]:
        target[key] += source[key]


@router.get(
    "/admin/activity/{activity_id}/year-faculty-major",
    response_model=DashboardActivityYearBreakdownResponse
)
def get_activity_year_faculty_major_dashboard(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    activity = (
        db.query(Activity)
        .filter(Activity.activity_id == activity_id)
        .first()
    )

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    year_filter = (
        year_status.strip()
        if year_status is not None and year_status.strip() != ""
        else None
    )

    faculties = db.query(Faculty).order_by(Faculty.faculty_id.asc()).all()
    majors = db.query(Major).order_by(Major.major_id.asc()).all()

    year_statuses = [year_filter] if year_filter else get_dashboard_year_statuses(db)
    year_set = set(year_statuses)

    major_map = {
        major.major_id: {
            "major_id": major.major_id,
            "major_name": major.major_name,
            "faculty_id": major.faculty_id,
        }
        for major in majors
    }

    faculty_map = {
        faculty.faculty_id: {
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            "major_ids": [
                major.major_id
                for major in majors
                if major.faculty_id == faculty.faculty_id
            ],
        }
        for faculty in faculties
    }

    total_rows_query = (
        db.query(
            Student.year_status,
            Student.faculty_id,
            Student.major_id,
            func.count(Student.student_id).label("total_student"),
        )
        .group_by(Student.year_status, Student.faculty_id, Student.major_id)
    )

    if year_filter:
        total_rows_query = total_rows_query.filter(Student.year_status == year_filter)

    total_rows = total_rows_query.all()

    activity_rows_query = (
        db.query(
            Student.year_status,
            Student.faculty_id,
            Student.major_id,
            func.count(distinct(Student.student_id)).label("count_student"),
            func.count(
                distinct(
                    case(
                        (StudentActivity.attendance_status == "เข้าร่วม", Student.student_id),
                        else_=None
                    )
                )
            ).label("joined_count"),
            func.count(
                distinct(
                    case(
                        (StudentActivity.attendance_status == "ไม่เข้าร่วม", Student.student_id),
                        else_=None
                    )
                )
            ).label("not_joined_count"),
            func.count(
                distinct(
                    case(
                        (StudentActivity.checkin_at.isnot(None), Student.student_id),
                        else_=None
                    )
                )
            ).label("checkin_count"),
            func.count(
                distinct(
                    case(
                        (StudentActivity.checkout_at.isnot(None), Student.student_id),
                        else_=None
                    )
                )
            ).label("checkout_count"),
        )
        .join(StudentActivity, StudentActivity.student_id == Student.student_id)
        .filter(StudentActivity.activity_id == activity_id)
        .group_by(Student.year_status, Student.faculty_id, Student.major_id)
    )

    if year_filter:
        activity_rows_query = activity_rows_query.filter(Student.year_status == year_filter)

    activity_rows = activity_rows_query.all()

    summary_by_major = {}

    for row in total_rows:
        current_year = row.year_status
        if current_year is None or str(current_year).strip() == "":
            continue

        year_set.add(current_year)
        key = (current_year, row.faculty_id, row.major_id)
        summary = summary_by_major.setdefault(key, empty_activity_summary())
        summary["total_student"] = row.total_student or 0

    for row in activity_rows:
        current_year = row.year_status
        if current_year is None or str(current_year).strip() == "":
            continue

        year_set.add(current_year)
        key = (current_year, row.faculty_id, row.major_id)
        summary = summary_by_major.setdefault(key, empty_activity_summary())
        summary["count_student"] = row.count_student or 0
        summary["joined_count"] = row.joined_count or 0
        summary["not_joined_count"] = row.not_joined_count or 0
        summary["checkin_count"] = row.checkin_count or 0
        summary["checkout_count"] = row.checkout_count or 0

    ordered_years = []
    for item in YEAR_STATUS_LIST + sorted(year_set):
        if item in year_set and item not in ordered_years:
            ordered_years.append(item)

    year_result = []

    for current_year in ordered_years:
        year_summary = empty_activity_summary()
        faculty_result = []

        for faculty_id, faculty in faculty_map.items():
            faculty_summary = empty_activity_summary()
            major_result = []

            for major_id in faculty["major_ids"]:
                major = major_map[major_id]
                major_summary = summary_by_major.get(
                    (current_year, faculty_id, major_id),
                    empty_activity_summary()
                ).copy()

                add_activity_summary(faculty_summary, major_summary)

                major_result.append({
                    "major_id": major["major_id"],
                    "major_name": major["major_name"],
                    **finalize_activity_summary(major_summary),
                })

            add_activity_summary(year_summary, faculty_summary)

            faculty_result.append({
                "faculty_id": faculty["faculty_id"],
                "faculty_name": faculty["faculty_name"],
                **finalize_activity_summary(faculty_summary),
                "major": major_result,
            })

        year_result.append({
            "year_status": current_year,
            **finalize_activity_summary(year_summary),
            "faculty": faculty_result,
        })

    return {
        "detail": "ดึงสรุปกิจกรรมตามชั้นปี คณะ และสาขาสำเร็จ",
        "data": {
            "activity": build_activity_summary(db, activity),
            "year": year_result,
        }
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

    volunteer_hours_count_all = (
        db.query(func.sum(Activity.volunteer_hours))
        .filter(Activity.activity_status == True)
        .scalar()
        or 0
        if is_all_activity
        else activity.volunteer_hours
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

    join_rate_percent = calc_percent(joined_count, total_join_status)
    checkout_rate_percent = calc_percent(checkout_count, checkin_count)

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

            major_rank.append(major_rank_item)

            major_result.append({
                "major_id": major.major_id,
                "major_name": major.major_name,
                "total_student": major_rank_item["total_student"],
                "joined_count": major_rank_item["joined_count"],
                "not_joined_count": major_rank_item["not_joined_count"],
            })

        major_result = sorted(
            major_result,
            key=lambda x: x["joined_count"],
            reverse=True
        )

        faculty_result.append({
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            "total_student": faculty_rank_item["total_student"],
            "joined_count": faculty_rank_item["joined_count"],
            "not_joined_count": faculty_rank_item["not_joined_count"],
            "major": major_result,
        })

    faculty_result = sorted(
        faculty_result,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    faculty_rank = sorted(
        faculty_rank,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    major_rank = sorted(
        major_rank,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    return {
        "detail": "success",
        "data": {
            "activity_count": activity_count,

            "joined_count": joined_count,
            "not_joined_count": not_joined_count,
            "checkin_count": checkin_count,
            "checkout_count": checkout_count,

            "student_count_all": student_count_all,

            "hours_count_all": float(hours_count_all or 0),
            "volunteer_hours_count_all": float(volunteer_hours_count_all or 0),

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


@router.get(
    "/student/{student_id}",
    response_model=StudentDashboardMessageResponse
)
def get_student_dashboard(
    student_id: int,
    db: Session = Depends(get_db)
):
    student = (
        db.query(Student)
        .filter(Student.student_id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบนักศึกษา"
        )

    rows = (
        db.query(Activity, StudentActivity)
        .outerjoin(
            StudentActivity,
            (StudentActivity.activity_id == Activity.activity_id)
            & (StudentActivity.student_id == student_id)
        )
        .filter(Activity.activity_status == True)
        .order_by(Activity.activity_date.desc())
        .all()
    )

    joined_count = 0
    not_joined_count = 0
    checkin_count = 0
    checkout_count = 0

    total_activity_hours = 0.0
    total_volunteer_hours = 0.0
    total_earned_hours = 0.0

    activities = []

    for activity, student_activity in rows:
        attendance_status = (
            student_activity.attendance_status
            if student_activity and student_activity.attendance_status
            else "ไม่เข้าร่วม"
        )

        checkin_at = (
            student_activity.checkin_at
            if student_activity
            else None
        )

        checkout_at = (
            student_activity.checkout_at
            if student_activity
            else None
        )

        earned_hours = (
            float(student_activity.earned_hours or 0)
            if student_activity
            else 0.0
        )

        volunteer_hours = float(activity.volunteer_hours or 0)
        activity_hours = float(activity.hours or 0)

        if attendance_status == "เข้าร่วม":
            joined_count += 1
            total_activity_hours += activity_hours
            total_volunteer_hours += volunteer_hours
            total_earned_hours += earned_hours
        else:
            not_joined_count += 1

        if checkin_at is not None:
            checkin_count += 1

        if checkout_at is not None:
            checkout_count += 1

        check_detail = None

        if student_activity:
            check_detail = {
                "attendance_status": attendance_status,
                "registered_at": student_activity.registered_at,

                "earned_hours": earned_hours,
                "volunteer_hours": volunteer_hours,
                "activity_hours": activity_hours,

                "checkin": {
                    "checkin_at": student_activity.checkin_at,
                    "checkin_status": student_activity.checkin_status,
                    "checkin_status_text": get_scan_status_text(
                        student_activity.checkin_status,
                        "ตรงเวลา",
                        "มาสาย"
                    ),
                    "checkin_lat": (
                        float(student_activity.checkin_lat)
                        if student_activity.checkin_lat is not None
                        else None
                    ),
                    "checkin_lng": (
                        float(student_activity.checkin_lng)
                        if student_activity.checkin_lng is not None
                        else None
                    ),
                },

                "checkout": {
                    "checkout_at": student_activity.checkout_at,
                    "checkout_status": student_activity.checkout_status,
                    "checkout_status_text": get_scan_status_text(
                        student_activity.checkout_status,
                        "ตรงเวลา",
                        "เช็คเอาท์นอกเวลา"
                    ),
                    "checkout_lat": (
                        float(student_activity.checkout_lat)
                        if student_activity.checkout_lat is not None
                        else None
                    ),
                    "checkout_lng": (
                        float(student_activity.checkout_lng)
                        if student_activity.checkout_lng is not None
                        else None
                    ),
                },
            }

        activities.append({
            "activity_id": activity.activity_id,
            "activity_name": activity.activity_name,

            "activity_date": (
                activity.activity_date.isoformat()
                if activity.activity_date
                else None
            ),

            "start_time": format_time_dot(activity.start_time),
            "end_time": format_time_dot(activity.end_time),

            "hours": activity_hours,
            "volunteer_hours": volunteer_hours,
            "earned_hours": earned_hours,

            "location": activity.location,
            "description": activity.description,
            "activity_img": activity.activity_img,

            "activity_status": bool(activity.activity_status),
            "attendance_status": attendance_status,

            "check_detail": check_detail,

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

            "total_activity_hours": total_activity_hours,
            "total_volunteer_hours": total_volunteer_hours,
            "total_earned_hours": total_earned_hours,

            "total_activity_count": total_activity_count,

            "join_rate_percent": calc_percent(
                joined_count,
                total_activity_count
            ),

            "checkout_rate_percent": calc_percent(
                checkout_count,
                checkin_count
            ),

            "activities": activities,
        }
    }
    
    

def get_activity_or_404(activity_id: int, db: Session):
    if activity_id == 0:
        return None

    activity = (
        db.query(Activity)
        .filter(Activity.activity_id == activity_id)
        .first()
    )

    if not activity:
        raise HTTPException(status_code=404, detail="ไม่พบกิจกรรม")

    return activity

def get_top_activity(db: Session):
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
    )

    if len(activity_rank) == 0:
        return None

    return activity_rank[0]

@router.get("/admin/sum/{activity_id}", response_model=AdminStudentMessageResponse)
def get_admin_dashboard(activity_id: int, db: Session = Depends(get_db)):
    is_all_activity = activity_id == 0
    activity = get_activity_or_404(activity_id, db)

    hours_count_all = (
        db.query(func.sum(Activity.hours))
        .filter(Activity.activity_status == True)
        .scalar()
        or 0
        if is_all_activity
        else activity.hours
    )

    volunteer_hours_count_all = (
        db.query(func.sum(Activity.volunteer_hours))
        .filter(Activity.activity_status == True)
        .scalar()
        or 0
        if is_all_activity
        else activity.volunteer_hours
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

    selected_activity = None
    top_activity = None

    if not is_all_activity:
        selected_activity = build_activity_summary(db, activity)
        top_activity = selected_activity
    else:
        top_activity = get_top_activity(db)

    return {
        "detail": "success",
        "data": {
            "activity_count": activity_count,

            "joined_count": joined_count,
            "not_joined_count": not_joined_count,
            "checkin_count": checkin_count,
            "checkout_count": checkout_count,

            "student_count_all": student_count_all,

            "hours_count_all": float(hours_count_all or 0),
            "volunteer_hours_count_all": float(volunteer_hours_count_all or 0),

            "join_rate_percent": calc_percent(
                joined_count,
                joined_count + not_joined_count
            ),
            "checkout_rate_percent": calc_percent(
                checkout_count,
                checkin_count
            ),

            "top_activity": top_activity,
            "selected_activity": selected_activity,

            "activity_rank": [],
            "faculty_rank": [],
            "major_rank": [],
            "year_count": [],
            "faculty": [],
        }
    }


@router.get("/admin/{activity_id}/activity-rank")
def get_admin_activity_rank(activity_id: int, db: Session = Depends(get_db)):
    activity = get_activity_or_404(activity_id, db)

    if activity_id == 0:
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

    else:
        activity_rank = [
            build_activity_summary(db, activity)
        ]

    return {
        "detail": "success",
        "data": activity_rank
    }


@router.get("/admin/{activity_id}/year-count")
def get_admin_year_count(activity_id: int, db: Session = Depends(get_db)):
    get_activity_or_404(activity_id, db)

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

    return {
        "detail": "success",
        "data": year_count
    }


@router.get("/admin/{activity_id}/faculty-rank")
def get_admin_faculty_rank(activity_id: int, db: Session = Depends(get_db)):
    get_activity_or_404(activity_id, db)

    faculties = (
        db.query(Faculty)
        .order_by(Faculty.faculty_id.asc())
        .all()
    )

    faculty_rank = []

    for faculty in faculties:
        faculty_rank.append(
            build_faculty_rank_item(
                db=db,
                faculty=faculty,
                activity_id=activity_id
            )
        )

    faculty_rank = sorted(
        faculty_rank,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    return {
        "detail": "success",
        "data": faculty_rank
    }


@router.get("/admin/{activity_id}/major-rank")
def get_admin_major_rank(activity_id: int, db: Session = Depends(get_db)):
    get_activity_or_404(activity_id, db)

    rows = (
        db.query(Major, Faculty)
        .join(Faculty, Faculty.faculty_id == Major.faculty_id)
        .order_by(Major.major_id.asc())
        .all()
    )

    major_rank = []

    for major, faculty in rows:
        major_rank.append(
            build_major_rank_item(
                db=db,
                major=major,
                faculty=faculty,
                activity_id=activity_id
            )
        )

    major_rank = sorted(
        major_rank,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    return {
        "detail": "success",
        "data": major_rank
    }


@router.get("/admin/{activity_id}/faculty")
def get_admin_faculty(activity_id: int, db: Session = Depends(get_db)):
    get_activity_or_404(activity_id, db)

    faculties = (
        db.query(Faculty)
        .order_by(Faculty.faculty_id.asc())
        .all()
    )

    faculty_result = []

    for faculty in faculties:
        faculty_rank_item = build_faculty_rank_item(
            db=db,
            faculty=faculty,
            activity_id=activity_id
        )

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

            major_result.append({
                "major_id": major.major_id,
                "major_name": major.major_name,
                "total_student": major_rank_item["total_student"],
                "joined_count": major_rank_item["joined_count"],
                "not_joined_count": major_rank_item["not_joined_count"],
            })

        major_result = sorted(
            major_result,
            key=lambda x: x["joined_count"],
            reverse=True
        )

        faculty_result.append({
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            "total_student": faculty_rank_item["total_student"],
            "joined_count": faculty_rank_item["joined_count"],
            "not_joined_count": faculty_rank_item["not_joined_count"],
            "major": major_result,
        })

    faculty_result = sorted(
        faculty_result,
        key=lambda x: x["joined_count"],
        reverse=True
    )

    return {
        "detail": "success",
        "data": faculty_result
    }
