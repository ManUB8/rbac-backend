from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Activity, Faculty, Major
from routers.admin_dashboard import (
    YEAR_STATUS_LIST,
    calc_percent,
    count_all_students,
    count_checkin,
    count_checkout,
    count_students,
    format_time_dot,
)
from schemas.schemas_admin_dashboard import (
    AdminStudentMessageResponse,
    DashboardActivityYearBreakdownResponse,
)


router = APIRouter(prefix="/dashboard/v1", tags=["Dashboard Admin Report"])


def normalize_year_status(year_status: Optional[str]) -> Optional[str]:
    if year_status is None or year_status.strip() == "":
        return None

    value = year_status.strip()
    if value not in YEAR_STATUS_LIST:
        raise HTTPException(
            status_code=400,
            detail=f"year_status ต้องเป็น {', '.join(YEAR_STATUS_LIST)}",
        )

    return value


def get_activity_or_404(activity_id: int, db: Session) -> Optional[Activity]:
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


def build_count_summary(
    db: Session,
    activity_id: int,
    year_status: Optional[str] = None,
    faculty_id: Optional[int] = None,
    major_id: Optional[int] = None,
):
    total_student = count_all_students(
        db=db,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
    )
    count_student = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
    )
    joined_count = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
        attendance_status="เข้าร่วม",
    )
    not_joined_count = count_students(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
        attendance_status="ไม่เข้าร่วม",
    )
    checkin_count = count_checkin(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
    )
    checkout_count = count_checkout(
        db=db,
        activity_id=activity_id,
        faculty_id=faculty_id,
        major_id=major_id,
        year_status=year_status,
    )

    return {
        "total_student": total_student,
        "count_student": count_student,
        "joined_count": joined_count,
        "not_joined_count": not_joined_count,
        "checkin_count": checkin_count,
        "checkout_count": checkout_count,
        "join_rate_percent": calc_percent(count_student, total_student),
        "checkout_rate_percent": calc_percent(checkout_count, checkin_count),
    }


def build_activity_summary(
    db: Session,
    activity: Activity,
    year_status: Optional[str],
):
    summary = build_count_summary(
        db=db,
        activity_id=activity.activity_id,
        year_status=year_status,
    )

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
        "joined_count": summary["joined_count"],
        "not_joined_count": summary["not_joined_count"],
        "checkin_count": summary["checkin_count"],
        "checkout_count": summary["checkout_count"],
        "total_count": summary["count_student"],
        "join_rate_percent": summary["join_rate_percent"],
        "checkout_rate_percent": summary["checkout_rate_percent"],
    }


def get_activity_rank(
    db: Session,
    activity_id: int,
    year_status: Optional[str],
    limit: Optional[int] = None,
):
    selected = get_activity_or_404(activity_id, db)
    activities = (
        db.query(Activity)
        .filter(Activity.activity_status == True)
        .all()
        if activity_id == 0
        else [selected]
    )
    result = [
        build_activity_summary(db, activity, year_status)
        for activity in activities
    ]
    result.sort(key=lambda item: item["joined_count"], reverse=True)
    return result[:limit] if limit is not None else result


@router.get("/admin/sum/{activity_id}", response_model=AdminStudentMessageResponse)
def get_admin_dashboard_summary(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    year_filter = normalize_year_status(year_status)
    activity = get_activity_or_404(activity_id, db)
    is_all_activity = activity_id == 0
    summary = build_count_summary(db, activity_id, year_filter)

    hours_count_all = (
        db.query(func.coalesce(func.sum(Activity.hours), 0))
        .filter(Activity.activity_status == True)
        .scalar()
        if is_all_activity
        else activity.hours
    )
    volunteer_hours_count_all = (
        db.query(func.coalesce(func.sum(Activity.volunteer_hours), 0))
        .filter(Activity.activity_status == True)
        .scalar()
        if is_all_activity
        else activity.volunteer_hours
    )
    activity_count = (
        db.query(func.count(Activity.activity_id))
        .filter(Activity.activity_status == True)
        .scalar()
        if is_all_activity
        else 1
    )
    activity_rank = get_activity_rank(
        db=db,
        activity_id=activity_id,
        year_status=year_filter,
        limit=1,
    )
    selected_activity = (
        build_activity_summary(db, activity, year_filter)
        if activity is not None
        else None
    )

    return {
        "detail": "success",
        "data": {
            "activity_count": activity_count or 0,
            "joined_count": summary["joined_count"],
            "not_joined_count": summary["not_joined_count"],
            "checkin_count": summary["checkin_count"],
            "checkout_count": summary["checkout_count"],
            "student_count_all": summary["count_student"],
            "hours_count_all": float(hours_count_all or 0),
            "volunteer_hours_count_all": float(volunteer_hours_count_all or 0),
            "join_rate_percent": summary["join_rate_percent"],
            "checkout_rate_percent": summary["checkout_rate_percent"],
            "top_activity": selected_activity or (activity_rank[0] if activity_rank else None),
            "selected_activity": selected_activity,
            "activity_rank": [],
            "faculty_rank": [],
            "major_rank": [],
            "year_count": [],
            "faculty": [],
        },
    }


@router.get("/admin/{activity_id}/activity-rank")
def get_admin_activity_rank(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    year_filter = normalize_year_status(year_status)
    return {
        "detail": "success",
        "data": get_activity_rank(db, activity_id, year_filter, limit=10),
    }


@router.get("/admin/{activity_id}/year-count")
def get_admin_year_count(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    get_activity_or_404(activity_id, db)
    year_filter = normalize_year_status(year_status)
    years = [year_filter] if year_filter else YEAR_STATUS_LIST

    return {
        "detail": "success",
        "data": [
            {
                "name": year,
                **build_count_summary(db, activity_id, year_status=year),
            }
            for year in years
        ],
    }


@router.get("/admin/{activity_id}/faculty-rank")
def get_admin_faculty_rank(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    get_activity_or_404(activity_id, db)
    year_filter = normalize_year_status(year_status)
    faculties = db.query(Faculty).order_by(Faculty.faculty_id.asc()).all()
    result = [
        {
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            **build_count_summary(
                db,
                activity_id,
                year_status=year_filter,
                faculty_id=faculty.faculty_id,
            ),
        }
        for faculty in faculties
    ]
    result.sort(key=lambda item: item["joined_count"], reverse=True)
    return {"detail": "success", "data": result}


@router.get("/admin/{activity_id}/major-rank")
def get_admin_major_rank(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    get_activity_or_404(activity_id, db)
    year_filter = normalize_year_status(year_status)
    rows = (
        db.query(Major, Faculty)
        .join(Faculty, Faculty.faculty_id == Major.faculty_id)
        .order_by(Major.major_id.asc())
        .all()
    )
    result = [
        {
            "major_id": major.major_id,
            "major_name": major.major_name,
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            **build_count_summary(
                db,
                activity_id,
                year_status=year_filter,
                major_id=major.major_id,
            ),
        }
        for major, faculty in rows
    ]
    result.sort(key=lambda item: item["joined_count"], reverse=True)
    return {"detail": "success", "data": result}


@router.get("/admin/{activity_id}/faculty")
def get_admin_faculty(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    get_activity_or_404(activity_id, db)
    year_filter = normalize_year_status(year_status)
    faculties = db.query(Faculty).order_by(Faculty.faculty_id.asc()).all()
    result = []

    for faculty in faculties:
        faculty_summary = build_count_summary(
            db,
            activity_id,
            year_status=year_filter,
            faculty_id=faculty.faculty_id,
        )
        majors = (
            db.query(Major)
            .filter(Major.faculty_id == faculty.faculty_id)
            .order_by(Major.major_id.asc())
            .all()
        )
        major_result = [
            {
                "major_id": major.major_id,
                "major_name": major.major_name,
                **build_count_summary(
                    db,
                    activity_id,
                    year_status=year_filter,
                    major_id=major.major_id,
                ),
            }
            for major in majors
        ]
        major_result.sort(key=lambda item: item["joined_count"], reverse=True)
        result.append({
            "faculty_id": faculty.faculty_id,
            "faculty_name": faculty.faculty_name,
            **faculty_summary,
            "major": major_result,
        })

    result.sort(key=lambda item: item["joined_count"], reverse=True)
    return {"detail": "success", "data": result}


@router.get(
    "/admin/activity/{activity_id}/year-faculty-major",
    response_model=DashboardActivityYearBreakdownResponse,
)
def get_activity_year_faculty_major_dashboard(
    activity_id: int,
    year_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    activity = get_activity_or_404(activity_id, db)
    year_filter = normalize_year_status(year_status)
    years = [year_filter] if year_filter else YEAR_STATUS_LIST
    faculties = db.query(Faculty).order_by(Faculty.faculty_id.asc()).all()
    majors = db.query(Major).order_by(Major.major_id.asc()).all()
    majors_by_faculty = {
        faculty.faculty_id: [
            major for major in majors
            if major.faculty_id == faculty.faculty_id
        ]
        for faculty in faculties
    }
    year_result = []

    for year in years:
        faculty_result = []
        for faculty in faculties:
            major_result = [
                {
                    "major_id": major.major_id,
                    "major_name": major.major_name,
                    **build_count_summary(
                        db,
                        activity_id,
                        year_status=year,
                        major_id=major.major_id,
                    ),
                }
                for major in majors_by_faculty[faculty.faculty_id]
            ]
            faculty_result.append({
                "faculty_id": faculty.faculty_id,
                "faculty_name": faculty.faculty_name,
                **build_count_summary(
                    db,
                    activity_id,
                    year_status=year,
                    faculty_id=faculty.faculty_id,
                ),
                "major": major_result,
            })

        year_result.append({
            "year_status": year,
            **build_count_summary(db, activity_id, year_status=year),
            "faculty": faculty_result,
        })

    return {
        "detail": "ดึงสรุปกิจกรรมตามชั้นปี คณะ และสาขาสำเร็จ",
        "data": {
            "activity": build_activity_summary(db, activity, year_filter),
            "year": year_result,
        },
    }
