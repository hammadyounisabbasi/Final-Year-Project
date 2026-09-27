"""Database-backed Faculty Management queries for authenticated administrators."""
from __future__ import annotations

from datetime import datetime
from math import ceil

from fastapi import HTTPException
from sqlalchemy import case, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.class_schedule import ClassSchedule
from app.models.course import Course
from app.models.course_result import CourseResult
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.submission import Submission
from app.models.teacher import Teacher
from app.models.user import User


SORT_COLUMNS = {
    "name": (Teacher.first_name, Teacher.last_name),
    "employee_id": (Teacher.employee_id,),
    "department": (Department.department_name,),
    "designation": (Teacher.designation,),
    "joining_date": (Teacher.joining_date,),
    "status": (Teacher.status,),
}


def faculty_item(row: Teacher) -> dict:
    return {
        "teacher_id": row.teacher_id,
        "employee_id": row.employee_id,
        "name": f"{row.first_name} {row.last_name}".strip(),
        "first_name": row.first_name,
        "last_name": row.last_name,
        "profile_photo": row.profile_photo,
        "department_id": row.department_id,
        "department": row.department.department_name if row.department else None,
        "designation": row.designation,
        "employment_type": row.employment_type,
        "qualification": row.qualification,
        "specialization": row.specialization,
        "office_email": row.office_email,
        "account_email": row.user.email if row.user else None,
        "phone": row.phone,
        "office_room": row.office_room,
        "joining_date": row.joining_date,
        "faculty_status": row.status,
        "account_active": bool(row.user.is_active) if row.user else False,
        "account_verified": bool(row.user.is_verified) if row.user else False,
    }


def list_faculty(
    db: Session, *, search: str = "", department_id: int | None = None,
    designation: str = "", employment_type: str = "", faculty_status: str = "",
    account_active: bool | None = None, sort_by: str = "name", sort_order: str = "asc",
    page: int = 1, page_size: int = 20,
) -> dict:
    query = db.query(Teacher).join(User, Teacher.user_id == User.user_id).join(
        Department, Teacher.department_id == Department.department_id
    ).options(
        joinedload(Teacher.user), joinedload(Teacher.department)
    )
    if search.strip():
        value = f"%{search.strip().casefold()}%"
        query = query.filter(or_(
            func.lower(Teacher.first_name + " " + Teacher.last_name).like(value),
            func.lower(Teacher.employee_id).like(value),
            func.lower(Teacher.office_email).like(value),
            func.lower(User.email).like(value),
            func.lower(Department.department_name).like(value),
            func.lower(Teacher.designation).like(value),
        ))
    if department_id is not None:
        query = query.filter(Teacher.department_id == department_id)
    if designation.strip():
        query = query.filter(func.lower(Teacher.designation) == designation.strip().casefold())
    if employment_type.strip():
        query = query.filter(Teacher.employment_type == employment_type.strip())
    if faculty_status.strip():
        query = query.filter(Teacher.status == faculty_status.strip())
    if account_active is not None:
        query = query.filter(User.is_active == (1 if account_active else 0))

    total = query.count()
    columns = SORT_COLUMNS.get(sort_by, SORT_COLUMNS["name"])
    ordering = [column.desc() if sort_order == "desc" else column.asc() for column in columns]
    rows = query.order_by(*ordering, Teacher.teacher_id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    teacher_ids = [row.teacher_id for row in rows]
    course_stats = {
        teacher_id: {"assigned_courses": count, "credit_hours": int(credits or 0)}
        for teacher_id, count, credits in db.query(
            Course.teacher_id, func.count(Course.course_id), func.sum(Course.credit_hours)
        ).filter(Course.teacher_id.in_(teacher_ids)).group_by(Course.teacher_id).all()
    } if teacher_ids else {}
    schedule_counts = dict(db.query(ClassSchedule.teacher_id, func.count(ClassSchedule.schedule_id)).filter(
        ClassSchedule.teacher_id.in_(teacher_ids), ClassSchedule.status == "Active"
    ).group_by(ClassSchedule.teacher_id).all()) if teacher_ids else {}
    items = []
    for row in rows:
        item = faculty_item(row)
        item.update(course_stats.get(row.teacher_id, {"assigned_courses": 0, "credit_hours": 0}))
        item["weekly_classes"] = schedule_counts.get(row.teacher_id, 0)
        items.append(item)
    return {"items": items, "pagination": {
        "page": page, "page_size": page_size, "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }}


def faculty_management_overview(db: Session) -> dict:
    total = db.query(func.count(Teacher.teacher_id)).scalar() or 0
    active = db.query(func.count(Teacher.teacher_id)).filter(Teacher.status == "Active").scalar() or 0
    active_accounts = db.query(func.count(Teacher.teacher_id)).join(User).filter(User.is_active == 1).scalar() or 0
    on_leave = db.query(func.count(Teacher.teacher_id)).filter(Teacher.status == "On Leave").scalar() or 0
    assigned_courses = db.query(func.count(Course.course_id)).filter(Course.teacher_id.isnot(None)).scalar() or 0
    scheduled_faculty = db.query(func.count(func.distinct(ClassSchedule.teacher_id))).filter(ClassSchedule.status == "Active").scalar() or 0
    active_schedules = db.query(func.count(ClassSchedule.schedule_id)).filter(ClassSchedule.status == "Active").scalar() or 0
    total_credit_hours = db.query(func.sum(Course.credit_hours)).filter(Course.teacher_id.isnot(None)).scalar() or 0
    departments = [{"id": did, "name": name, "count": count} for did, name, count in db.query(
        Department.department_id, Department.department_name, func.count(Teacher.teacher_id)
    ).outerjoin(Teacher).group_by(Department.department_id, Department.department_name).order_by(Department.department_name).all()]
    designations = [{"name": name, "count": count} for name, count in db.query(
        Teacher.designation, func.count(Teacher.teacher_id)
    ).group_by(Teacher.designation).order_by(func.count(Teacher.teacher_id).desc(), Teacher.designation).all()]
    statuses = [{"name": name, "count": count} for name, count in db.query(
        Teacher.status, func.count(Teacher.teacher_id)
    ).group_by(Teacher.status).order_by(Teacher.status).all()]
    employment_types = [{"name": name, "count": count} for name, count in db.query(
        Teacher.employment_type, func.count(Teacher.teacher_id)
    ).group_by(Teacher.employment_type).order_by(Teacher.employment_type).all()]
    course_loads = db.query(Course.teacher_id, func.count(Course.course_id), func.sum(Course.credit_hours)).filter(
        Course.teacher_id.isnot(None)
    ).group_by(Course.teacher_id).all()
    no_course_count = total - len(course_loads)
    return {
        "stats": {
            "total_faculty": total, "active_faculty": active, "active_accounts": active_accounts,
            "departments": sum(item["count"] > 0 for item in departments), "on_leave": on_leave,
            "assigned_courses": assigned_courses, "scheduled_faculty": scheduled_faculty,
            "active_schedules": active_schedules, "total_assigned_credit_hours": int(total_credit_hours),
            "faculty_without_courses": no_course_count,
        },
        "distributions": {
            "departments": departments, "designations": designations,
            "statuses": statuses, "employment_types": employment_types,
            "course_loads": [{"teacher_id": tid, "courses": count, "credit_hours": int(credits or 0)} for tid, count, credits in course_loads],
        },
        "filters": {
            "departments": [{"id": row["id"], "name": row["name"]} for row in departments],
            "designations": [row["name"] for row in designations],
            "employment_types": [row["name"] for row in employment_types],
            "statuses": [row["name"] for row in statuses],
        },
        "workload_note": "Numeric workload is derived from assigned courses and active class schedules. No official overload thresholds exist in the current project.",
    }


def _minutes(start: str, end: str) -> int:
    try:
        return int((datetime.strptime(end, "%H:%M") - datetime.strptime(start, "%H:%M")).seconds // 60)
    except (TypeError, ValueError):
        return 0


def get_faculty_detail(db: Session, teacher_id: int) -> dict:
    teacher = db.query(Teacher).options(joinedload(Teacher.user), joinedload(Teacher.department)).filter(Teacher.teacher_id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    courses = db.query(Course).options(joinedload(Course.department)).filter(Course.teacher_id == teacher_id).order_by(Course.semester, Course.course_code).all()
    course_ids = [row.course_id for row in courses]
    enrollment_rows = db.query(
        Enrollment.course_id, Enrollment.academic_year, Enrollment.semester, Enrollment.section,
        func.count(func.distinct(Enrollment.student_id)),
    ).filter(Enrollment.course_id.in_(course_ids), Enrollment.enrollment_status == "Enrolled").group_by(
        Enrollment.course_id, Enrollment.academic_year, Enrollment.semester, Enrollment.section
    ).all() if course_ids else []
    sections_by_course = {}
    unique_students = set()
    if course_ids:
        unique_students = {row[0] for row in db.query(Enrollment.student_id).filter(
            Enrollment.course_id.in_(course_ids), Enrollment.enrollment_status == "Enrolled"
        ).distinct().all()}
    for course_id, year, semester, section, count in enrollment_rows:
        sections_by_course.setdefault(course_id, []).append({
            "academic_year": year, "semester": semester, "section": section, "student_count": count,
        })
    course_items = [{
        "course_id": row.course_id, "course_code": row.course_code, "course_title": row.course_title,
        "semester": row.semester, "credit_hours": row.credit_hours, "course_type": row.course_type,
        "status": row.status, "department": row.department.department_name if row.department else None,
        "sections": sections_by_course.get(row.course_id, []),
        "enrolled_students": sum(item["student_count"] for item in sections_by_course.get(row.course_id, [])),
    } for row in courses]

    schedules = db.query(ClassSchedule).options(joinedload(ClassSchedule.course)).filter(
        ClassSchedule.teacher_id == teacher_id, ClassSchedule.status == "Active"
    ).all()
    day_order = {day: index for index, day in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"))}
    schedules.sort(key=lambda row: (day_order.get(row.day_of_week, 99), row.start_time, row.course_id))
    schedule_items = [{
        "schedule_id": row.schedule_id, "course_id": row.course_id,
        "course_code": row.course.course_code if row.course else None,
        "course_title": row.course.course_title if row.course else None,
        "academic_year": row.academic_year, "semester": row.semester, "section": row.section,
        "day": row.day_of_week, "start_time": row.start_time, "end_time": row.end_time,
        "room": row.room_location, "class_type": row.class_type,
    } for row in schedules]
    assignments = db.query(Assignment).filter(Assignment.teacher_id == teacher_id).all()
    assignment_ids = [row.assignment_id for row in assignments]
    submissions_received = db.query(func.count(Submission.submission_id)).filter(
        Submission.assignment_id.in_(assignment_ids), Submission.submission_status != "Draft"
    ).scalar() or 0 if assignment_ids else 0
    pending_grading = db.query(func.count(Submission.submission_id)).filter(
        Submission.assignment_id.in_(assignment_ids), Submission.submission_status != "Draft", Submission.graded.is_(False)
    ).scalar() or 0 if assignment_ids else 0
    result_total, result_published, result_passed = db.query(
        func.count(CourseResult.result_id),
        func.sum(case((CourseResult.published == 1, 1), else_=0)),
        func.sum(case((CourseResult.result_status == "Pass", 1), else_=0)),
    ).filter(CourseResult.teacher_id == teacher_id).one()
    graded_count = db.query(func.count(Grade.grade_id)).filter(Grade.graded_by == teacher_id).scalar() or 0
    distinct_sections = {(row.course_id, row.academic_year, row.semester, row.section) for row in schedules}
    return {
        "profile": {**faculty_item(teacher), "gender": teacher.gender, "date_of_birth": teacher.date_of_birth,
                    "role": teacher.user.role if teacher.user else None, "last_login": teacher.user.last_login if teacher.user else None},
        "courses": course_items,
        "timetable": schedule_items,
        "workload": {
            "assigned_courses": len(courses), "total_credit_hours": sum(row.credit_hours or 0 for row in courses),
            "scheduled_classes_per_week": len(schedules), "scheduled_minutes_per_week": sum(_minutes(row.start_time, row.end_time) for row in schedules),
            "scheduled_sections": len(distinct_sections), "unique_students_taught": len(unique_students),
        },
        "assignments": {
            "created": len(assignments), "submissions_received": submissions_received,
            "pending_grading": pending_grading,
        },
        "results": {
            "result_records": result_total or 0, "published_results": result_published or 0,
            "passed_results": result_passed or 0, "grade_entries": graded_count,
        },
    }


def update_faculty(db: Session, teacher_id: int, values: dict) -> dict:
    teacher = db.query(Teacher).options(joinedload(Teacher.user), joinedload(Teacher.department)).filter(Teacher.teacher_id == teacher_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    values = {key: value for key, value in values.items() if value is not None}
    if "department_id" in values and db.get(Department, values["department_id"]) is None:
        raise HTTPException(status_code=422, detail="Department not found")
    if "account_email" in values:
        email = values.pop("account_email").strip().casefold()
        if db.query(User).filter(func.lower(User.email) == email, User.user_id != teacher.user_id).first():
            raise HTTPException(status_code=409, detail="Account email is already in use")
        teacher.user.email = email
    if "office_email" in values:
        email = values["office_email"].strip().casefold()
        if db.query(Teacher).filter(func.lower(Teacher.office_email) == email, Teacher.teacher_id != teacher_id).first():
            raise HTTPException(status_code=409, detail="Official email is already in use")
        values["office_email"] = email
    if "account_active" in values:
        teacher.user.is_active = 1 if values.pop("account_active") else 0
    allowed = {"first_name", "last_name", "phone", "office_email", "designation", "qualification", "specialization", "office_room", "employment_type", "department_id", "status"}
    for key, value in values.items():
        if key in allowed:
            setattr(teacher, key, value.strip() or None if isinstance(value, str) else value)
    try:
        db.commit()
        db.refresh(teacher)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="The update conflicts with an existing faculty or account value") from error
    except Exception:
        db.rollback()
        raise
    return faculty_item(teacher)
