"""Read-only aggregations and safe updates for Admin Student Management."""
from __future__ import annotations

from math import ceil

from fastapi import HTTPException
from sqlalchemy import case, func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.attendance import Attendance
from app.models.course_result import CourseResult
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.student_cgpa import StudentCGPA
from app.models.user import User
from app.services.student_ai_context import (
    get_assignments_context,
    get_attendance_context,
    get_cgpa_and_results_context,
    get_current_courses_context,
    get_fee_status_context,
    get_timetable_context,
)


SORT_COLUMNS = {
    "name": (Student.first_name, Student.last_name),
    "roll_number": (Student.roll_number,),
    "registration_number": (Student.registration_number,),
    "program": (Student.program,),
    "semester": (Student.semester,),
    "batch_year": (Student.batch_year,),
    "status": (Student.status,),
}


def student_item(row: Student) -> dict:
    return {
        "student_id": row.student_id,
        "roll_number": row.roll_number,
        "registration_number": row.registration_number,
        "name": f"{row.first_name} {row.last_name}".strip(),
        "first_name": row.first_name,
        "last_name": row.last_name,
        "profile_photo": row.profile_photo,
        "department_id": row.department_id,
        "department": row.department.department_name if row.department else None,
        "program": row.program,
        "semester": row.semester,
        "section": row.section,
        "batch_year": row.batch_year,
        "email": row.user.email if row.user else None,
        "phone": row.phone,
        "student_status": row.status,
        "account_active": bool(row.user.is_active) if row.user else False,
        "account_verified": bool(row.user.is_verified) if row.user else False,
    }


def list_students(
    db: Session, *, search: str = "", department_id: int | None = None,
    program: str = "", semester: int | None = None, section: str = "",
    student_status: str = "", sort_by: str = "name", sort_order: str = "asc",
    page: int = 1, page_size: int = 20,
) -> dict:
    query = db.query(Student).join(User, Student.user_id == User.user_id).options(
        joinedload(Student.user), joinedload(Student.department)
    )
    search = search.strip()
    if search:
        value = f"%{search.casefold()}%"
        query = query.filter(or_(
            func.lower(Student.first_name + " " + Student.last_name).like(value),
            func.lower(Student.roll_number).like(value),
            func.lower(Student.registration_number).like(value),
            func.lower(User.email).like(value),
        ))
    if department_id is not None:
        query = query.filter(Student.department_id == department_id)
    if program.strip():
        query = query.filter(func.lower(Student.program) == program.strip().casefold())
    if semester is not None:
        query = query.filter(Student.semester == semester)
    if section.strip():
        query = query.filter(func.lower(Student.section) == section.strip().casefold())
    if student_status.strip():
        query = query.filter(Student.status == student_status.strip())

    total = query.count()
    columns = SORT_COLUMNS.get(sort_by, SORT_COLUMNS["name"])
    ordering = [column.desc() if sort_order == "desc" else column.asc() for column in columns]
    rows = query.order_by(*ordering, Student.student_id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    enrollment_counts = dict(db.query(Enrollment.student_id, func.count(Enrollment.enrollment_id)).filter(
        Enrollment.student_id.in_([row.student_id for row in rows]),
        Enrollment.enrollment_status == "Enrolled",
    ).group_by(Enrollment.student_id).all()) if rows else {}
    items = []
    for row in rows:
        item = student_item(row)
        item["active_enrollments"] = enrollment_counts.get(row.student_id, 0)
        items.append(item)
    return {
        "items": items,
        "pagination": {
            "page": page, "page_size": page_size, "total": total,
            "total_pages": ceil(total / page_size) if total else 0,
        },
    }


def student_management_overview(db: Session) -> dict:
    total = db.query(func.count(Student.student_id)).scalar() or 0
    active = db.query(func.count(Student.student_id)).filter(Student.status == "Active").scalar() or 0
    account_active = db.query(func.count(Student.student_id)).join(User).filter(User.is_active == 1).scalar() or 0
    departments = [
        {"id": dep_id, "name": name, "count": count}
        for dep_id, name, count in db.query(
            Department.department_id, Department.department_name, func.count(Student.student_id)
        ).outerjoin(Student).group_by(Department.department_id, Department.department_name).order_by(Department.department_name).all()
    ]
    programs = [
        {"name": name, "count": count}
        for name, count in db.query(Student.program, func.count(Student.student_id)).group_by(Student.program).order_by(func.count(Student.student_id).desc(), Student.program).all()
    ]
    semesters = [
        {"semester": number, "count": count}
        for number, count in db.query(Student.semester, func.count(Student.student_id)).group_by(Student.semester).order_by(Student.semester).all()
    ]
    sections = [row[0] for row in db.query(Student.section).filter(Student.section.isnot(None), Student.section != "").distinct().order_by(Student.section).all()]
    statuses = [row[0] for row in db.query(Student.status).distinct().order_by(Student.status).all()]

    cgpa_risk_ids = {row[0] for row in db.query(StudentCGPA.student_id).filter(StudentCGPA.overall_cgpa < 2.0).all()}
    attendance_rows = db.query(
        Attendance.student_id,
        func.count(Attendance.attendance_id),
        func.sum(case((Attendance.status.in_(["Present", "Late"]), 1), else_=0)),
    ).group_by(Attendance.student_id).all()
    attendance_risk_ids = {student_id for student_id, total_rows, attended in attendance_rows if total_rows and ((attended or 0) / total_rows * 100) < 75}

    scholarship_count = db.execute(text(
        "SELECT COUNT(DISTINCT student_id) FROM Fee_Records WHERE COALESCE(scholarship_amount, 0) > 0"
    )).scalar() or 0
    avg_cgpa = db.query(func.avg(StudentCGPA.overall_cgpa)).scalar()
    result_total, result_passed = db.query(
        func.count(CourseResult.result_id),
        func.sum(case((CourseResult.result_status == "Pass", 1), else_=0)),
    ).filter(CourseResult.published == 1).one()

    return {
        "stats": {
            "total_students": total,
            "active_students": active,
            "active_accounts": account_active,
            "at_risk_students": len(cgpa_risk_ids | attendance_risk_ids),
            "scholarship_students": scholarship_count,
            "average_cgpa": round(float(avg_cgpa), 2) if avg_cgpa is not None else None,
            "published_result_pass_rate": round((result_passed or 0) / result_total * 100, 1) if result_total else None,
        },
        "distributions": {"departments": departments, "programs": programs, "semesters": semesters},
        "filters": {
            "departments": [{"id": item["id"], "name": item["name"]} for item in departments],
            "programs": [item["name"] for item in programs],
            "semesters": [item["semester"] for item in semesters],
            "sections": sections,
            "statuses": statuses,
        },
        "risk_definition": "Students with a recorded CGPA below 2.00 or recorded attendance below 75%. Students without those records are not classified.",
    }


def get_student_detail(db: Session, student_id: int) -> dict:
    student = db.query(Student).options(joinedload(Student.user), joinedload(Student.department)).filter(Student.student_id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    notifications = db.execute(text("""
        SELECT notification_id, title, message, notification_type, priority, sender, is_read, action_url, created_at
        FROM Notifications WHERE recipient_type = 'Student' AND recipient_id = :student_id
        ORDER BY created_at DESC LIMIT 50
    """), {"student_id": student_id}).mappings().all()
    academics = get_cgpa_and_results_context(student, db)
    if db.query(StudentCGPA).filter(StudentCGPA.student_id == student_id).first() is None:
        academics.update({
            "has_cgpa_record": False,
            "overall_cgpa": None,
            "total_completed_credits": None,
            "academic_status": None,
        })
    else:
        academics["has_cgpa_record"] = True
    return {
        "profile": {
            **student_item(student), "gender": student.gender, "date_of_birth": student.date_of_birth,
            "emergency_contact": student.emergency_contact, "address": student.address,
            "admission_date": student.admission_date, "expected_graduation": student.expected_graduation,
            "credits_completed_profile": student.credits_completed,
            "last_login": student.user.last_login if student.user else None,
        },
        "academics": academics,
        "enrollments": get_current_courses_context(student, db),
        "attendance": get_attendance_context(student, db),
        "fees": get_fee_status_context(student, db),
        "assignments": get_assignments_context(student, db),
        "timetable": get_timetable_context(student, db),
        "notifications": [dict(row) for row in notifications],
    }


def update_student(db: Session, student_id: int, values: dict) -> dict:
    student = db.query(Student).options(joinedload(Student.user), joinedload(Student.department)).filter(Student.student_id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    values = {key: value for key, value in values.items() if value is not None}
    if "department_id" in values and db.get(Department, values["department_id"]) is None:
        raise HTTPException(status_code=422, detail="Department not found")
    if "email" in values:
        email = values.pop("email").strip().casefold()
        if db.query(User).filter(func.lower(User.email) == email, User.user_id != student.user_id).first():
            raise HTTPException(status_code=409, detail="Email is already in use")
        student.user.email = email
    if "account_active" in values:
        student.user.is_active = 1 if values.pop("account_active") else 0
    for key, value in values.items():
        if key in {"first_name", "last_name", "phone", "emergency_contact", "address", "program", "semester", "section", "batch_year", "department_id", "status"}:
            setattr(student, key, value.strip() or None if isinstance(value, str) else value)
    try:
        db.commit()
        db.refresh(student)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="The update conflicts with an existing student or account value") from error
    except Exception:
        db.rollback()
        raise
    return student_item(student)
