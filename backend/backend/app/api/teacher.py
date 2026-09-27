import json
import logging
import re
from difflib import SequenceMatcher
from datetime import date, datetime
from pathlib import Path
import shutil
from typing import Optional

logger = logging.getLogger("teacher_api")

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.class_schedule import ClassSchedule
from app.models.timetable import Timetable, TimetableCourse, TimetableSession
from app.models.academic_term import AcademicTerm
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.attendance import Attendance
from app.models.grade import Grade
from app.models.course_result import CourseResult
from app.models.gradebook import GradebookSetting, GradebookComponent
from app.services.academic_results import completed_cgpa_for_student
from app.services.gradebook import calculate_component_marks
from app.services.gradebook_records import (
    CONFLICT,
    build_gradebook_snapshot,
    synchronize_course_result,
)
from app.schemas.teacher import (
    AttendanceEntry, TeacherAssignmentCreate, TeacherAttendanceSave,
    TeacherScheduleCreate, TeacherSubmissionReview, GradebookSettingsSave,
    GradebookMarksSave,
)
from app.schemas.ai_assistant import AIChatRequest, TeacherAIGreetingResponse, TeacherAIChatResponse
from app.services.teacher_ai_assistant import process_teacher_chat, provider_manager
from app.services.timetable_integrity import assert_schedule_is_available, sync_student_timetable


router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"]
)


def _current_academic_year(db: Session) -> str | None:
    """Resolve one university-wide current year; never infer it per course."""
    active = db.query(AcademicTerm.academic_year).filter(
        AcademicTerm.status == "Active"
    ).order_by(AcademicTerm.academic_year.desc()).first()
    if active:
        return active[0]
    started = db.query(AcademicTerm.academic_year).filter(
        AcademicTerm.status == "Upcoming",
        AcademicTerm.start_date.isnot(None),
        AcademicTerm.start_date <= date.today(),
    ).order_by(AcademicTerm.academic_year.desc()).first()
    if started:
        return started[0]
    current_year = str(date.today().year)
    inferred = db.query(AcademicTerm.academic_year).filter(
        AcademicTerm.status != "Completed",
        AcademicTerm.academic_year >= f"{current_year}-0000",
    ).order_by(AcademicTerm.academic_year.asc()).first()
    return inferred[0] if inferred else None


def _owned_gradebook_setting(payload, teacher, db):
    course = db.query(Course).filter(
        Course.course_id == payload.course_id,
        Course.teacher_id == teacher.teacher_id,
    ).first()
    if course is None:
        raise HTTPException(status_code=403, detail="Selected course is not assigned to the authenticated teacher")
    if course.semester != payload.semester:
        raise HTTPException(status_code=422, detail="Semester does not match the selected course")
    has_enrolled_term = db.query(Enrollment.enrollment_id).filter(
        Enrollment.course_id == course.course_id,
        Enrollment.academic_year == payload.academic_year,
        Enrollment.semester == payload.semester,
    ).first()
    if has_enrolled_term is None:
        raise HTTPException(status_code=422, detail="Academic year and semester do not match an enrollment for the selected course")
    return course


def _gradebook_component_json(component):
    return {
        "component_id": component.component_id,
        "category": component.category,
        "name": component.name,
        "item_count": component.item_count,
        "total_marks": component.total_marks,
        "item_total_marks": component.item_total_marks,
        "aggregation": component.aggregation,
    }


@router.get("/gradebook/settings")
def get_gradebook_settings(
    course_id: int,
    academic_year: str,
    semester: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teacher = _teacher_for_gradebook(current_user, db)
    course = db.query(Course).filter(Course.course_id == course_id, Course.teacher_id == teacher.teacher_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found for the authenticated teacher")
    setting = db.query(GradebookSetting).filter_by(
        course_id=course_id, academic_year=academic_year, semester=semester
    ).first()
    return {
        "course_id": course_id,
        "course_code": course.course_code,
        "course_title": course.course_title,
        "academic_year": academic_year,
        "semester": semester,
        "total_marks": setting.total_marks if setting else 100,
        "components": [_gradebook_component_json(item) for item in setting.components] if setting else [],
    }


def _teacher_for_gradebook(current_user, db):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.user_id).first()
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    return teacher


def _owned_gradebook_enrollment(enrollment_id, teacher, db):
    enrollment = (db.query(Enrollment).join(Course, Course.course_id == Enrollment.course_id)
                  .filter(
                      Enrollment.enrollment_id == enrollment_id,
                      Course.teacher_id == teacher.teacher_id,
                  ).first())
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment not found for the authenticated teacher")
    return enrollment


@router.put("/gradebook/settings")
def save_gradebook_settings(
    payload: GradebookSettingsSave,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teacher = _teacher_for_gradebook(current_user, db)
    course = _owned_gradebook_setting(payload, teacher, db)
    if abs(sum(item.total_marks for item in payload.components) - 100) > 0.001:
        raise HTTPException(status_code=422, detail="Component marks must total exactly 100")

    setting = db.query(GradebookSetting).filter_by(
        course_id=course.course_id, academic_year=payload.academic_year, semester=payload.semester
    ).first()
    if setting is None:
        setting = GradebookSetting(
            course_id=course.course_id, teacher_id=teacher.teacher_id,
            academic_year=payload.academic_year, semester=payload.semester,
            total_marks=100,
        )
        db.add(setting)
        db.flush()
    else:
        setting.teacher_id = teacher.teacher_id
        setting.total_marks = 100
        db.query(GradebookComponent).filter_by(setting_id=setting.setting_id).delete()

    for order, item in enumerate(payload.components):
        db.add(GradebookComponent(
            setting_id=setting.setting_id,
            category=item.category,
            name=item.name.strip(),
            item_count=item.item_count,
            total_marks=item.total_marks,
            item_total_marks=item.total_marks / item.item_count,
            aggregation="average",
            sort_order=order,
        ))
    db.commit()
    db.refresh(setting)
    return {"saved": True, "total_marks": 100, "components": [_gradebook_component_json(item) for item in setting.components]}


@router.get("/gradebook/marks")
def get_gradebook_marks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teacher = _teacher_for_gradebook(current_user, db)
    enrollments = (db.query(Enrollment)
                   .join(Course, Course.course_id == Enrollment.course_id)
                   .filter(Course.teacher_id == teacher.teacher_id)
                   .all())
    marks = []
    for enrollment in enrollments:
        snapshot = build_gradebook_snapshot(db, enrollment)
        if not snapshot["components"]:
            continue
        totals = snapshot["category_totals"]
        marks.append({
            "enrollment_id": enrollment.enrollment_id,
            "sessional": totals["Sessional"],
            "midterm": totals["Midterm"],
            "final": totals["Final"],
            "total": snapshot["total"],
            "validation_status": snapshot["status"],
        })
    return {"marks": marks}


@router.get("/gradebook/validate")
def validate_gradebook_record(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teacher = _teacher_for_gradebook(current_user, db)
    enrollment = _owned_gradebook_enrollment(enrollment_id, teacher, db)
    return build_gradebook_snapshot(db, enrollment)


@router.post("/gradebook/marks")
def save_gradebook_marks(
    payload: GradebookMarksSave,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teacher = _teacher_for_gradebook(current_user, db)
    enrollment = _owned_gradebook_enrollment(payload.enrollment_id, teacher, db)
    setting = db.query(GradebookSetting).filter_by(
        course_id=enrollment.course_id, academic_year=enrollment.academic_year,
        semester=enrollment.semester,
    ).first()
    if setting is None:
        raise HTTPException(status_code=409, detail="Configure Grade Book Settings before entering marks")
    component_map = {item.component_id: item for item in setting.components}
    before = build_gradebook_snapshot(db, enrollment, setting)
    if before["status"] == CONFLICT:
        raise HTTPException(status_code=409, detail={
            "code": "GRADE_SOURCE_CONFLICT",
            "message": before["message"],
            "validation": before,
        })
    evidence_by_component = {item["component_id"]: item for item in before["components"]}
    submitted_component_ids = [item.component_id for item in payload.components]
    if len(submitted_component_ids) != len(set(submitted_component_ids)):
        raise HTTPException(status_code=422, detail="Each configured component may be submitted only once")
    unknown = set(submitted_component_ids) - set(component_map)
    if unknown:
        raise HTTPException(status_code=422, detail="Submitted component does not belong to this Grade Book setting")
    required_manual_ids = {
        component_id for component_id, evidence in evidence_by_component.items()
        if evidence["source"] == "manual_gradebook"
    }
    if not required_manual_ids.issubset(set(submitted_component_ids)):
        raise HTTPException(status_code=422, detail="Marks are required for every manual Gradebook component")

    for submitted in payload.components:
        component = component_map[submitted.component_id]
        evidence = evidence_by_component[component.component_id]
        try:
            calculate_component_marks(component, submitted.scores)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        if evidence["source"] == "online_assessment":
            expected = evidence["synchronized_scores"]
            if evidence["status"] != "VERIFIED":
                raise HTTPException(status_code=409, detail={
                    "code": "ONLINE_EVIDENCE_INCOMPLETE",
                    "message": evidence["message"],
                    "component_id": component.component_id,
                })
            if len(expected) != len(submitted.scores) or any(
                abs(left - right) > 0.001 for left, right in zip(expected, submitted.scores)
            ):
                raise HTTPException(status_code=409, detail={
                    "code": "GRADE_SOURCE_CONFLICT",
                    "message": "Submitted marks differ from the authoritative online assessment score",
                    "component_id": component.component_id,
                    "online_scores": expected,
                    "submitted_scores": submitted.scores,
                    "source_ids": [item["attempt_id"] for item in evidence["online_evidence"]],
                })
            db.query(Grade).filter(
                Grade.enrollment_id == enrollment.enrollment_id,
                Grade.title.like(f"Gradebook:{component.component_id}:%"),
            ).delete(synchronize_session=False)
            continue

        assessment_type = component.category if component.category in ("Midterm", "Final") else "Assignment"
        db.query(Grade).filter(
            Grade.enrollment_id == enrollment.enrollment_id,
            Grade.graded_by == teacher.teacher_id,
            Grade.title.like(f"Gradebook:{component.component_id}:%"),
        ).delete(synchronize_session=False)
        for index, score in enumerate(submitted.scores, 1):
            db.add(Grade(
                enrollment_id=enrollment.enrollment_id,
                assessment_type=assessment_type,
                title=f"Gradebook:{component.component_id}:{index}:{component.name}",
                obtained_marks=score,
                total_marks=component.item_total_marks,
                percentage=round(score / component.item_total_marks * 100, 2),
                graded_by=teacher.teacher_id,
                graded_at=datetime.utcnow(),
                published=1,
                academic_year=enrollment.academic_year,
                semester=enrollment.semester,
            ))
    db.flush()
    validation, result = synchronize_course_result(db, enrollment, teacher.teacher_id)
    if validation["status"] == CONFLICT or result is None:
        db.rollback()
        raise HTTPException(status_code=409, detail={
            "code": "GRADE_SOURCE_CONFLICT",
            "message": validation["message"],
            "validation": validation,
        })
    totals = validation["category_totals"]
    db.commit()
    return {
        "saved": True,
        "enrollment_id": enrollment.enrollment_id,
        "sessional": totals["Sessional"],
        "midterm": totals["Midterm"],
        "final": totals["Final"],
        "total": validation["total"],
        "validation": validation,
    }


UPLOAD_ROOT = settings.UPLOAD_DIR
ALLOWED_UPLOAD_SUFFIXES = {".pdf", ".docx", ".zip", ".txt", ".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _save_uploaded_file(upload: UploadFile, directory: str) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only PDF, DOCX, ZIP, and TXT files are allowed")
    destination_dir = UPLOAD_ROOT / directory
    destination_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{suffix}"
    destination = destination_dir / safe_name
    with destination.open("wb") as output:
        shutil.copyfileobj(upload.file, output)
    if destination.stat().st_size > 25 * 1024 * 1024:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds the 25 MB limit")
    return str(destination.relative_to(UPLOAD_ROOT.parent)).replace("\\", "/")


@router.get("/profile")
def get_teacher_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the profile of the currently authenticated teacher.
    """

    # ------------------------------------------------------
    # Make sure the logged-in user is a teacher
    # ------------------------------------------------------

    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )

    # ------------------------------------------------------
    # Find teacher using logged-in user's user_id
    # ------------------------------------------------------

    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.user_id == current_user.user_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Teacher record not found
    # ------------------------------------------------------

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )

    # ------------------------------------------------------
    # Return real database data
    # ------------------------------------------------------

    return {
        "teacher_id": teacher.teacher_id,
        "user_id": teacher.user_id,
        "employee_id": teacher.employee_id,

        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "gender": teacher.gender,
        "date_of_birth": teacher.date_of_birth,

        "phone": teacher.phone,
        "office_email": teacher.office_email,

        "designation": teacher.designation,
        "qualification": teacher.qualification,
        "specialization": teacher.specialization,

        "joining_date": teacher.joining_date,
        "office_room": teacher.office_room,
        "profile_photo": teacher.profile_photo,

        "employment_type": teacher.employment_type,
        "status": teacher.status,

        "department": {
            "department_id": teacher.department.department_id,
            "department_code": teacher.department.department_code,
            "department_name": teacher.department.department_name,
            "department_short_name": (
                teacher.department.department_short_name
            ),
        }
    }


@router.get("/courses")
def get_teacher_courses(
    semester: Optional[int] = None,
    academic_year: Optional[str] = None,
    enrollment_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return courses owned by the authenticated teacher with enrollment counts.

    The teacher identity is derived exclusively from the JWT-backed user record.
    The optional enrollment filters affect roster counts only; they never expand
    the returned course set beyond Courses.teacher_id for this teacher.
    """

    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )

    teacher = (
        db.query(Teacher)
        .filter(Teacher.user_id == current_user.user_id)
        .first()
    )

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )

    academic_year = academic_year or _current_academic_year(db)
    courses_query = (
        db.query(Course)
        .filter(Course.teacher_id == teacher.teacher_id)
    )
    if semester is not None:
        courses_query = courses_query.filter(Course.semester == semester)

    courses = courses_query.order_by(
        Course.semester.asc(),
        Course.course_code.asc()
    ).all()

    def filtered_enrollments(course_id: int):
        query = (
            db.query(Enrollment)
            .join(Student, Student.student_id == Enrollment.student_id)
            .filter(
                Enrollment.course_id == course_id,
                Enrollment.semester == Student.semester,
            )
        )
        if semester is not None:
            query = query.filter(Enrollment.semester == semester)
        if academic_year:
            query = query.filter(Enrollment.academic_year == academic_year)
        if enrollment_status:
            query = query.filter(Enrollment.enrollment_status == enrollment_status)
        return query.all()

    courses_list = []
    unique_student_ids = set()

    for course in courses:
        enrollments = filtered_enrollments(course.course_id)
        student_ids = {enrollment.student_id for enrollment in enrollments}
        unique_student_ids.update(student_ids)

        section_counts = {}
        for enrollment in enrollments:
            key = (
                enrollment.academic_year,
                enrollment.semester,
                enrollment.section or "Unassigned"
            )
            section_counts.setdefault(key, set()).add(enrollment.student_id)

        sections = [
            {
                "academic_year": year,
                "semester": enrolled_semester,
                "section": section,
                "student_count": len(student_ids_for_section)
            }
            for (year, enrolled_semester, section), student_ids_for_section
            in sorted(section_counts.items())
        ]

        department = course.department
        courses_list.append({
            "course_id": course.course_id,
            "course_code": course.course_code,
            "course_title": course.course_title,
            "course_description": course.course_description,
            "credit_hours": course.credit_hours,
            "semester": course.semester,
            "course_type": course.course_type,
            "status": course.status,
            "enrolled_student_count": len(student_ids),
            "sections": sections,
            "department": {
                "department_id": department.department_id,
                "department_code": department.department_code,
                "department_name": department.department_name,
                "department_short_name": department.department_short_name
            }
        })

    available_enrollment_periods = (
        db.query(Enrollment.academic_year, Enrollment.semester)
        .join(Course, Course.course_id == Enrollment.course_id)
        .filter(Course.teacher_id == teacher.teacher_id)
        .distinct()
        .order_by(Enrollment.academic_year.desc(), Enrollment.semester.asc())
        .all()
    )

    return {
        "success": True,
        "teacher": {
            "teacher_id": teacher.teacher_id,
            "name": f"{teacher.first_name} {teacher.last_name}".strip()
        },
        "filters": {
            "semester": semester,
            "academic_year": academic_year,
            "enrollment_status": enrollment_status
        },
        "metrics": {
            "course_count": len(courses_list),
            "unique_enrolled_student_count": len(unique_student_ids),
            "total_credit_hours": sum(course["credit_hours"] for course in courses_list)
        },
        "available_enrollment_periods": [
            {
                "academic_year": year,
                "semester": enrolled_semester,
                "label": f"Semester {enrolled_semester} ({year})"
            }
            for year, enrolled_semester in available_enrollment_periods
        ],
        "courses": courses_list
    }


@router.get("/students")
def get_teacher_students(
    course_id: Optional[int] = None,
    semester: Optional[int] = None,
    academic_year: Optional[str] = None,
    section: Optional[str] = None,
    enrollment_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return only students enrolled in courses owned by this teacher."""

    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )

    teacher = (
        db.query(Teacher)
        .filter(Teacher.user_id == current_user.user_id)
        .first()
    )
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )

    if course_id is not None:
        owns_course = (
            db.query(Course.course_id)
            .filter(
                Course.course_id == course_id,
                Course.teacher_id == teacher.teacher_id
            )
            .first()
        )
        if owns_course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not assigned to the authenticated teacher"
            )

    enrollments_query = (
        db.query(Enrollment)
        .join(Course, Course.course_id == Enrollment.course_id)
        .join(Student, Student.student_id == Enrollment.student_id)
        .filter(
            Course.teacher_id == teacher.teacher_id,
            Enrollment.semester == Student.semester,
        )
    )
    if course_id is not None:
        enrollments_query = enrollments_query.filter(Enrollment.course_id == course_id)
    if semester is not None:
        enrollments_query = enrollments_query.filter(Enrollment.semester == semester)
    if academic_year:
        enrollments_query = enrollments_query.filter(Enrollment.academic_year == academic_year)
    if section:
        enrollments_query = enrollments_query.filter(Enrollment.section == section)
    if enrollment_status:
        enrollments_query = enrollments_query.filter(
            Enrollment.enrollment_status == enrollment_status
        )

    enrollments = enrollments_query.order_by(
        Enrollment.student_id.asc(),
        Enrollment.enrollment_id.asc()
    ).all()

    student_ids = {enrollment.student_id for enrollment in enrollments}
    students_by_id = {}
    for enrollment in enrollments:
        student = enrollment.student
        course = enrollment.course
        department = student.department
        if student.student_id not in students_by_id:
            calculated_cgpa, completed_credits = completed_cgpa_for_student(
                db, student.student_id, student.semester
            )
            students_by_id[student.student_id] = {
                "student_id": student.student_id,
                "roll_number": student.roll_number,
                "registration_number": student.registration_number,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "name": f"{student.first_name} {student.last_name}".strip(),
                "email": student.user.email,
                "program": student.program,
                "student_semester": student.semester,
                "student_section": student.section,
                "status": student.status,
                "cgpa": calculated_cgpa if completed_credits else None,
                "academic_status": "Good Standing" if calculated_cgpa >= 2 else (
                    "Academic Warning" if completed_credits else None
                ),
                "department": {
                    "department_id": department.department_id,
                    "department_code": department.department_code,
                    "department_name": department.department_name
                },
                "enrollments": []
            }

        students_by_id[student.student_id]["enrollments"].append({
            "enrollment_id": enrollment.enrollment_id,
            "course_id": course.course_id,
            "course_code": course.course_code,
            "course_title": course.course_title,
            "credit_hours": course.credit_hours,
            "academic_year": enrollment.academic_year,
            "semester": enrollment.semester,
            "section": enrollment.section,
            "enrollment_status": enrollment.enrollment_status
        })

    students = sorted(
        students_by_id.values(),
        key=lambda item: (item["last_name"].lower(), item["first_name"].lower())
    )
    teacher_courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher.teacher_id)
        .order_by(Course.semester.asc(), Course.course_code.asc())
        .all()
    )

    return {
        "success": True,
        "teacher_id": teacher.teacher_id,
        "filters": {
            "course_id": course_id,
            "semester": semester,
            "academic_year": academic_year,
            "section": section,
            "enrollment_status": enrollment_status
        },
        "metrics": {
            "student_count": len(students),
            "active_student_count": sum(
                student["status"] == "Active" for student in students
            ),
            "at_risk_student_count": sum(
                student["academic_status"] in {"Warning", "Probation"}
                for student in students
            ),
            "attendance_available": False
        },
        "available_courses": [
            {
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_title": course.course_title,
                "semester": course.semester
            }
            for course in teacher_courses
        ],
        "students": students
    }


def _get_authenticated_teacher(current_user: User, db: Session) -> Teacher:
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )

    teacher = (
        db.query(Teacher)
        .filter(Teacher.user_id == current_user.user_id)
        .first()
    )
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    return teacher


def _serialize_schedule(schedule: ClassSchedule, db: Session) -> dict:
    student_count = (
        db.query(Enrollment.student_id)
        .join(Student, Student.student_id == Enrollment.student_id)
        .filter(
            Enrollment.course_id == schedule.course_id,
            Enrollment.academic_year == schedule.academic_year,
            Enrollment.semester == schedule.semester,
            Enrollment.section == schedule.section,
            Enrollment.semester == Student.semester,
        )
        .distinct()
        .count()
    )
    course = schedule.course
    return {
        "schedule_id": schedule.schedule_id,
        "course_id": schedule.course_id,
        "course_code": course.course_code,
        "course_title": course.course_title,
        "academic_year": schedule.academic_year,
        "semester": schedule.semester,
        "section": schedule.section,
        "day_of_week": schedule.day_of_week,
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "room_location": schedule.room_location,
        "class_type": schedule.class_type,
        "status": schedule.status,
        "enrolled_student_count": student_count
    }


def _owned_attendance_schedule(schedule_id: int, teacher: Teacher, db: Session) -> ClassSchedule:
    schedule = (
        db.query(ClassSchedule)
        .filter(
            ClassSchedule.schedule_id == schedule_id,
            ClassSchedule.teacher_id == teacher.teacher_id,
            ClassSchedule.status == "Active",
        )
        .first()
    )
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active class schedule not found for the authenticated teacher")
    if schedule.course.teacher_id != teacher.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Schedule course is not owned by the authenticated teacher")
    return schedule


def _attendance_roster(schedule: ClassSchedule, db: Session) -> list[Enrollment]:
    return (
        db.query(Enrollment)
        .join(Student, Student.student_id == Enrollment.student_id)
        .filter(
            Enrollment.course_id == schedule.course_id,
            Enrollment.semester == schedule.semester,
            Enrollment.section == schedule.section,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
            Enrollment.semester == Student.semester,
        )
        .order_by(Enrollment.student_id.asc())
        .all()
    )


@router.get("/attendance/courses")
def get_teacher_attendance_courses(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Return only active scheduled classes owned by the authenticated teacher."""
    teacher = _get_authenticated_teacher(current_user, db)
    schedules = (
        db.query(ClassSchedule)
        .filter(ClassSchedule.teacher_id == teacher.teacher_id, ClassSchedule.status == "Active")
        .order_by(ClassSchedule.academic_year.desc(), ClassSchedule.semester.asc(), ClassSchedule.course_id.asc(), ClassSchedule.day_of_week.asc(), ClassSchedule.start_time.asc())
        .all()
    )
    return {
        "success": True,
        "classes": [
            {
                **_serialize_schedule(schedule, db),
                "session_key": f"schedule:{schedule.schedule_id}",
                "label": f"{schedule.course.course_code} — {schedule.course.course_title} | Sem {schedule.semester} | Section {schedule.section} | {schedule.day_of_week} {schedule.start_time}-{schedule.end_time}",
            }
            for schedule in schedules
        ],
    }


@router.get("/attendance/roster")
def get_teacher_attendance_roster(
    schedule_id: int,
    attendance_date: str,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Load the current enrolled roster and saved statuses for one owned class session."""
    teacher = _get_authenticated_teacher(current_user, db)
    schedule = _owned_attendance_schedule(schedule_id, teacher, db)
    try:
        selected_date = datetime.strptime(attendance_date, "%Y-%m-%d").date()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="attendance_date must use YYYY-MM-DD") from error
    saved = {
        row.student_id: row
        for row in db.query(Attendance).filter(
            Attendance.course_id == schedule.course_id,
            Attendance.teacher_id == teacher.teacher_id,
            Attendance.academic_year == schedule.academic_year,
            Attendance.semester == schedule.semester,
            Attendance.section == schedule.section,
            Attendance.attendance_date == selected_date,
            Attendance.session_key == f"schedule:{schedule.schedule_id}",
        ).all()
    }
    roster = []
    for enrollment in _attendance_roster(schedule, db):
        student = enrollment.student
        record = saved.get(student.student_id)
        roster.append({
            "student_id": student.student_id,
            "roll_number": student.roll_number,
            "name": f"{student.first_name} {student.last_name}".strip(),
            "status": record.status if record else "",
            "remarks": record.remarks if record else "",
        })
    return {"success": True, "schedule": _serialize_schedule(schedule, db), "attendance_date": selected_date, "roster": roster, "saved": bool(saved)}


@router.post("/attendance")
def save_teacher_attendance(
    payload: TeacherAttendanceSave,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Create or update one complete attendance roster, enforcing owned schedule and active enrollment."""
    teacher = _get_authenticated_teacher(current_user, db)
    schedule = _owned_attendance_schedule(payload.schedule_id, teacher, db)
    roster_ids = {enrollment.student_id for enrollment in _attendance_roster(schedule, db)}
    submitted_ids = [record.student_id for record in payload.records]
    if len(submitted_ids) != len(set(submitted_ids)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Each student may appear only once")
    if set(submitted_ids) != roster_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attendance records must exactly match the current enrolled roster")

    session_key = f"schedule:{schedule.schedule_id}"
    existing = {
        row.student_id: row
        for row in db.query(Attendance).filter(
            Attendance.course_id == schedule.course_id,
            Attendance.teacher_id == teacher.teacher_id,
            Attendance.academic_year == schedule.academic_year,
            Attendance.semester == schedule.semester,
            Attendance.section == schedule.section,
            Attendance.attendance_date == payload.attendance_date,
            Attendance.session_key == session_key,
        ).all()
    }
    for record in payload.records:
        attendance = existing.get(record.student_id)
        if attendance is None:
            attendance = Attendance(
                student_id=record.student_id, course_id=schedule.course_id, teacher_id=teacher.teacher_id,
                schedule_id=schedule.schedule_id, academic_year=schedule.academic_year, semester=schedule.semester,
                section=schedule.section, attendance_date=payload.attendance_date, session_key=session_key,
            )
            db.add(attendance)
        attendance.status = record.status
        attendance.remarks = (record.remarks or "").strip() or None
        attendance.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "Attendance saved", "schedule_id": schedule.schedule_id, "attendance_date": payload.attendance_date, "records_saved": len(payload.records)}


@router.get("/attendance")
def get_teacher_attendance_history(
    schedule_id: Optional[int] = None,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    teacher = _get_authenticated_teacher(current_user, db)
    query = db.query(Attendance).filter(Attendance.teacher_id == teacher.teacher_id)
    if schedule_id is not None:
        _owned_attendance_schedule(schedule_id, teacher, db)
        query = query.filter(Attendance.schedule_id == schedule_id)
    rows = query.order_by(Attendance.attendance_date.desc(), Attendance.attendance_id.desc()).all()
    return {"success": True, "records": [{"attendance_id": row.attendance_id, "student_id": row.student_id, "student_name": f"{row.student.first_name} {row.student.last_name}".strip(), "roll_number": row.student.roll_number, "course_code": row.course.course_code, "attendance_date": row.attendance_date, "status": row.status, "remarks": row.remarks, "schedule_id": row.schedule_id} for row in rows]}


@router.get("/schedule")
def get_teacher_schedule(
    course_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    semester: Optional[int] = None,
    schedule_status: Optional[str] = "Active",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return timetable entries that belong to the authenticated teacher."""

    teacher = _get_authenticated_teacher(current_user, db)
    academic_year = academic_year or _current_academic_year(db)
    published_query = db.query(ClassSchedule).join(TimetableSession, TimetableSession.legacy_schedule_id == ClassSchedule.schedule_id).join(TimetableCourse, TimetableCourse.timetable_course_id == TimetableSession.timetable_course_id).join(Timetable, Timetable.timetable_id == TimetableCourse.timetable_id).filter(Timetable.status == "Published", TimetableCourse.teacher_id == teacher.teacher_id)
    query = db.query(ClassSchedule).filter(ClassSchedule.teacher_id == teacher.teacher_id)

    if course_id is not None:
        if not query.filter(ClassSchedule.course_id == course_id).first():
            raise HTTPException(status_code=404, detail="No schedule for this course belongs to this teacher")
        query = query.filter(ClassSchedule.course_id == course_id)
        published_query = published_query.filter(TimetableCourse.course_id == course_id)
    if academic_year:
        query = query.filter(ClassSchedule.academic_year == academic_year)
        published_query = published_query.filter(ClassSchedule.academic_year == academic_year)
    if semester is not None:
        query = query.filter(ClassSchedule.semester == semester)
        published_query = published_query.filter(Timetable.semester == semester)
    if schedule_status:
        query = query.filter(ClassSchedule.status == schedule_status)

    day_order = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    candidate_schedules = published_query.distinct().all() or query.all()
    if not academic_year and semester is None:
        latest_term_by_course = {}
        for item in candidate_schedules:
            term_key = (item.academic_year, item.semester)
            latest_term_by_course[item.course_id] = max(
                latest_term_by_course.get(item.course_id, term_key),
                term_key,
            )
        candidate_schedules = [
            item for item in candidate_schedules
            if (item.academic_year, item.semester) == latest_term_by_course[item.course_id]
        ]

    schedules = sorted(
        candidate_schedules,
        key=lambda item: (day_order[item.day_of_week], item.start_time, item.course_id)
    )
    schedule_items = [_serialize_schedule(item, db) for item in schedules]

    term_metrics = {}
    for term_key in sorted({(item.academic_year, item.semester) for item in schedules}):
        term_schedules = [item for item in schedules if (item.academic_year, item.semester) == term_key]
        student_ids = {
            student_id
            for item in term_schedules
            for student_id, in db.query(Enrollment.student_id)
            .filter(
                Enrollment.course_id == item.course_id,
                Enrollment.academic_year == item.academic_year,
                Enrollment.semester == item.semester,
                Enrollment.section == item.section,
                Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
            )
            .distinct()
            .all()
        }
        term_metrics[f"{term_key[0]}:{term_key[1]}"] = {
            "classes_per_week": len(term_schedules),
            "unique_enrolled_students": len(student_ids),
            "teaching_minutes": sum(
                (
                    datetime.strptime(item.end_time, "%H:%M")
                    - datetime.strptime(item.start_time, "%H:%M")
                ).seconds // 60
                for item in term_schedules
            ),
            "room_count": len({item.room_location for item in term_schedules}),
        }

    teaching_minutes = sum(
        (
            datetime.strptime(item["end_time"], "%H:%M")
            - datetime.strptime(item["start_time"], "%H:%M")
        ).seconds // 60
        for item in schedule_items
    )

    teacher_courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher.teacher_id)
        .order_by(Course.semester.asc(), Course.course_code.asc())
        .all()
    )
    return {
        "success": True,
        "teacher_id": teacher.teacher_id,
        "filters": {
            "course_id": course_id,
            "academic_year": academic_year,
            "semester": semester,
            "status": schedule_status
        },
        "metrics": {
            "classes_per_week": len(schedule_items),
            "unique_enrolled_students": len({
                student_id
                for item in schedules
                for student_id, in db.query(Enrollment.student_id)
                .join(Student, Student.student_id == Enrollment.student_id)
                .filter(
                    Enrollment.course_id == item.course_id,
                    Enrollment.academic_year == item.academic_year,
                    Enrollment.semester == item.semester,
                    Enrollment.section == item.section,
                    Enrollment.semester == Student.semester,
                )
                .distinct()
                .all()
            }),
            "teaching_minutes": teaching_minutes,
            "room_count": len({item["room_location"] for item in schedule_items})
        },
        "term_metrics": term_metrics,
        "available_courses": [
            {
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_title": course.course_title,
                "semester": course.semester
            }
            for course in teacher_courses
        ],
        "schedules": schedule_items
    }


@router.post("/schedule", status_code=status.HTTP_201_CREATED)
def create_teacher_schedule(
    schedule_data: TeacherScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a timetable entry for a course owned by the current teacher."""

    teacher = _get_authenticated_teacher(current_user, db)
    course = (
        db.query(Course)
        .filter(
            Course.course_id == schedule_data.course_id,
            Course.teacher_id == teacher.teacher_id
        )
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not assigned to the authenticated teacher"
        )

    try:
        start_time = datetime.strptime(schedule_data.start_time, "%H:%M")
        end_time = datetime.strptime(schedule_data.end_time, "%H:%M")
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time and end_time must use HH:MM 24-hour format"
        ) from error

    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be later than start_time"
        )

    if (end_time - start_time).seconds != 60 * 60:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Each class must be exactly one hour long"
        )

    schedule = ClassSchedule(
        course_id=course.course_id,
        teacher_id=teacher.teacher_id,
        academic_year=schedule_data.academic_year.strip(),
        semester=schedule_data.semester,
        section=schedule_data.section.strip(),
        day_of_week=schedule_data.day_of_week,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time,
        room_location=schedule_data.room_location.strip(),
        class_type=schedule_data.class_type,
        status="Active"
    )
    assert_schedule_is_available(db, schedule)
    db.add(schedule)
    try:
        db.flush()
        sync_student_timetable(db, schedule)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This class conflicts with an existing course, teacher, room, or student timetable entry"
        ) from error

    db.refresh(schedule)
    return {
        "success": True,
        "message": "Schedule entry created",
        "schedule": _serialize_schedule(schedule, db)
    }


def _serialize_assignment(assignment: Assignment, db: Session) -> dict:
    submitted_count = (
        db.query(Submission.submission_id)
        .filter(
            Submission.assignment_id == assignment.assignment_id,
            Submission.submission_status != "Draft"
        )
        .count()
    )
    enrolled_student_count = (
        db.query(Enrollment.student_id)
        .join(Student, Student.student_id == Enrollment.student_id)
        .filter(
            Enrollment.course_id == assignment.course_id,
            Enrollment.academic_year == assignment.academic_year,
            Enrollment.semester == assignment.semester,
            Enrollment.section == assignment.section,
            Enrollment.semester == Student.semester,
        )
        .distinct()
        .count()
    )
    course = assignment.course
    return {
        "assignment_id": assignment.assignment_id,
        "course_id": assignment.course_id,
        "course_code": course.course_code,
        "course_title": course.course_title,
        "title": assignment.title,
        "description": assignment.description,
        "assignment_type": assignment.assignment_type,
        "total_marks": assignment.total_marks,
        "academic_year": assignment.academic_year,
        "semester": assignment.semester,
        "section": assignment.section,
        "section": assignment.section,
        "release_date": assignment.release_date,
        "due_date": assignment.due_date,
        "allow_late_submission": assignment.allow_late_submission,
        "late_penalty_percentage": assignment.late_penalty_percentage,
        "attachment_path": assignment.attachment_path,
        "status": assignment.status,
        "submitted_count": submitted_count,
        "enrolled_student_count": enrolled_student_count
    }


@router.get("/assignments")
def get_teacher_assignments(
    course_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    semester: Optional[int] = None,
    assignment_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List assignments owned by the authenticated teacher only."""

    teacher = _get_authenticated_teacher(current_user, db)
    query = db.query(Assignment).filter(Assignment.teacher_id == teacher.teacher_id)

    if course_id is not None:
        owns_course = (
            db.query(Course.course_id)
            .filter(
                Course.course_id == course_id,
                Course.teacher_id == teacher.teacher_id
            )
            .first()
        )
        if owns_course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not assigned to the authenticated teacher"
            )
        query = query.filter(Assignment.course_id == course_id)
    if academic_year:
        query = query.filter(Assignment.academic_year == academic_year)
    if semester is not None:
        query = query.filter(Assignment.semester == semester)
    if assignment_status:
        query = query.filter(Assignment.status == assignment_status)

    assignments = query.order_by(Assignment.due_date.asc()).all()
    serialized = [_serialize_assignment(assignment, db) for assignment in assignments]
    submission_count = sum(item["submitted_count"] for item in serialized)
    possible_submissions = sum(item["enrolled_student_count"] for item in serialized)
    pending_grading = (
        db.query(Submission.submission_id)
        .join(Assignment, Assignment.assignment_id == Submission.assignment_id)
        .filter(
            Assignment.teacher_id == teacher.teacher_id,
            Submission.submission_status != "Draft",
            Submission.graded.is_(False)
        )
        .count()
    )

    courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher.teacher_id)
        .order_by(Course.semester.asc(), Course.course_code.asc())
        .all()
    )
    return {
        "success": True,
        "teacher_id": teacher.teacher_id,
        "metrics": {
            "assignment_count": len(serialized),
            "pending_grading_count": pending_grading,
            "submission_rate": (
                round((submission_count / possible_submissions) * 100, 1)
                if possible_submissions else None
            ),
            "average_class_score": None
        },
        "available_courses": [
            {
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_title": course.course_title,
                "semester": course.semester
            }
            for course in courses
        ],
        "assignments": serialized
    }


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
def create_teacher_assignment(
    assignment_data: TeacherAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a published assignment for a course owned by the current teacher."""

    teacher = _get_authenticated_teacher(current_user, db)
    course = (
        db.query(Course)
        .filter(
            Course.course_id == assignment_data.course_id,
            Course.teacher_id == teacher.teacher_id
        )
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not assigned to the authenticated teacher"
        )

    assignment = Assignment(
        course_id=course.course_id,
        teacher_id=teacher.teacher_id,
        title=assignment_data.title.strip(),
        description=(assignment_data.description or "").strip() or None,
        assignment_type=assignment_data.assignment_type,
        total_marks=assignment_data.total_marks,
        semester=course.semester,
        academic_year=assignment_data.academic_year.strip(),
        section=assignment_data.section.strip(),
        due_date=assignment_data.due_date,
        status="Published"
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "success": True,
        "message": "Assignment published",
        "assignment": _serialize_assignment(assignment, db)
    }


@router.delete("/assignments/{assignment_id}")
def delete_teacher_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an assignment and its associated submissions/files owned by the teacher."""
    teacher = _get_authenticated_teacher(current_user, db)
    assignment = (
        db.query(Assignment)
        .filter(Assignment.assignment_id == assignment_id, Assignment.teacher_id == teacher.teacher_id)
        .first()
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found for the authenticated teacher"
        )

    # Delete physical reference file if it exists
    if assignment.attachment_path:
        ref_file = UPLOAD_ROOT.parent / assignment.attachment_path
        if ref_file.exists():
            try:
                ref_file.unlink(missing_ok=True)
            except Exception:
                pass

    # Delete physical submission files
    submissions = db.query(Submission).filter(Submission.assignment_id == assignment.assignment_id).all()
    for sub in submissions:
        if sub.file_path and sub.file_path != "inline":
            sub_file = UPLOAD_ROOT.parent / sub.file_path
            if sub_file.exists():
                try:
                    sub_file.unlink(missing_ok=True)
                except Exception:
                    pass
        db.delete(sub)

    db.delete(assignment)
    db.commit()

    return {"success": True, "message": "Assignment and associated submissions deleted successfully", "assignment_id": assignment_id}


@router.post("/assignments/{assignment_id}/attachment")
def upload_teacher_assignment_attachment(assignment_id: int, attachment: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    teacher = _get_authenticated_teacher(current_user, db)
    assignment = db.query(Assignment).filter(Assignment.assignment_id == assignment_id, Assignment.teacher_id == teacher.teacher_id).first()
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found for the authenticated teacher")
    assignment.attachment_path = _save_uploaded_file(attachment, "assignment_references")
    db.commit(); db.refresh(assignment)
    return {"success": True, "attachment_path": assignment.attachment_path}


@router.get("/assignments/{assignment_id}/submissions")
def get_teacher_assignment_submissions(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List submissions only for an assignment owned by the current teacher."""

    teacher = _get_authenticated_teacher(current_user, db)
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.assignment_id == assignment_id,
            Assignment.teacher_id == teacher.teacher_id
        )
        .first()
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found for the authenticated teacher"
        )

    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.assignment_id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    submission_content = {}
    for item in submissions:
        extracted = _extract_text_content(item.file_path)
        analyzable_text = f"{item.response_text or ''}\n{extracted}".strip()
        submission_content[item.submission_id] = analyzable_text
    return {
        "success": True,
        "assignment": _serialize_assignment(assignment, db),
        "submissions": [
            {
                "submission_id": submission.submission_id,
                "student_id": submission.student_id,
                "student_name": f"{submission.student.first_name} {submission.student.last_name}".strip(),
                "roll_number": submission.student.roll_number,
                "submission_title": submission.submission_title,
                "file_name": submission.file_name,
                "file_path": submission.file_path,
                "response_text": submission.response_text,
                "extracted_text": submission_content[submission.submission_id],
                "file_readable": _file_status(submission.file_path, submission_content[submission.submission_id] if submission.file_path == "inline" else _extract_text_content(submission.file_path))["previewable"],
                "file_error": _file_status(submission.file_path, submission_content[submission.submission_id] if submission.file_path == "inline" else _extract_text_content(submission.file_path))["error"],
                "similarity_matches": _similarity_matches(submission, submissions, submission_content),
                "submission_attempt": submission.submission_attempt,
                "submitted_at": submission.submitted_at,
                "is_late": submission.is_late,
                "teacher_marks": submission.teacher_marks,
                "teacher_feedback": submission.teacher_feedback,
                "ai_score": submission.ai_score,
                "ai_feedback": submission.ai_feedback,
                "submission_status": submission.submission_status,
                "graded": submission.graded
            }
            for submission in submissions
        ]
    }


def _extract_text_content(file_rel_path: Optional[str]) -> str:
    """Read full textual content from local PDF, DOCX, text/code, or ZIP files."""
    if not file_rel_path or file_rel_path == "inline":
        return ""
    full_path = UPLOAD_ROOT.parent / file_rel_path
    if not full_path.exists():
        return ""
    suffix = full_path.suffix.lower()

    # 1. Plain text and source code files
    if suffix in {".txt", ".py", ".cpp", ".c", ".java", ".cs", ".sql", ".html", ".css", ".js", ".json", ".md", ".php", ".rb", ".go", ".rs", ".sh"}:
        try:
            return full_path.read_text(encoding="utf-8", errors="ignore")[:15000]
        except Exception as e:
            logger.warning(f"Error reading text file {full_path}: {e}")
            return ""

    # 2. PDF Documents
    if suffix == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(full_path))
            pages_text = []
            for i, page in enumerate(reader.pages[:20]):
                txt = page.extract_text() or ""
                if txt.strip():
                    pages_text.append(f"--- Page {i+1} ---\n{txt}")
            extracted = "\n\n".join(pages_text)
            if extracted.strip():
                return extracted[:15000]
        except Exception as e:
            logger.warning(f"Error extracting PDF {full_path}: {e}")

    # 3. Microsoft Word (.docx)
    if suffix == ".docx":
        try:
            import docx
            doc = docx.Document(str(full_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            extracted = "\n".join(paragraphs)
            if extracted.strip():
                return extracted[:15000]
        except Exception as e:
            logger.warning(f"Error extracting DOCX {full_path}: {e}")

    # 4. ZIP Archives (inspect files inside)
    if suffix == ".zip":
        try:
            import zipfile
            with zipfile.ZipFile(str(full_path), "r") as zf:
                file_list = zf.namelist()
                zip_contents = [f"[ZIP Archive containing {len(file_list)} files: {', '.join(file_list[:15])}]"]
                # Extract code/text files inside ZIP
                for fname in file_list[:8]:
                    fext = Path(fname).suffix.lower()
                    if fext in {".txt", ".py", ".cpp", ".c", ".java", ".sql", ".html", ".css", ".js", ".json", ".md"}:
                        try:
                            with zf.open(fname) as inner_file:
                                content = inner_file.read().decode("utf-8", errors="ignore")[:2000]
                                zip_contents.append(f"\n--- File: {fname} ---\n{content}")
                        except Exception:
                            pass
                return "\n".join(zip_contents)[:15000]
        except Exception as e:
            logger.warning(f"Error reading ZIP {full_path}: {e}")

    return f"[Attached file: {full_path.name}]"


def _file_status(file_rel_path: Optional[str], extracted_text: str = "") -> dict:
    """Describe whether a submission can be previewed and safely analyzed."""
    if not file_rel_path or file_rel_path == "inline":
        return {"previewable": bool(extracted_text.strip()), "ai_readable": bool(extracted_text.strip()), "error": None if extracted_text.strip() else "No student response text was submitted."}
    full_path = UPLOAD_ROOT.parent / file_rel_path
    if not full_path.exists():
        return {"previewable": False, "ai_readable": False, "error": "The uploaded file is missing from the server."}
    suffix = full_path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return {"previewable": True, "ai_readable": False, "error": "Image preview is available, but automatic text analysis cannot read image content."}
    if extracted_text.startswith("[Attached file:") or not extracted_text.strip():
        return {"previewable": False, "ai_readable": False, "error": "The file is empty, corrupted, or its content could not be extracted."}
    return {"previewable": True, "ai_readable": True, "error": None}


def _normalise_for_similarity(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())).strip()


def _similarity_matches(submission: Submission, submissions: list[Submission], content_by_id: dict[int, str]) -> list[dict]:
    current = _normalise_for_similarity(content_by_id.get(submission.submission_id, ""))
    if len(current.split()) < 20:
        return []
    matches = []
    for other in submissions:
        if other.submission_id == submission.submission_id:
            continue
        other_text = _normalise_for_similarity(content_by_id.get(other.submission_id, ""))
        if len(other_text.split()) < 20:
            continue
        ratio = SequenceMatcher(None, current, other_text).ratio()
        if ratio >= 0.82:
            matches.append({
                "submission_id": other.submission_id,
                "student_name": f"{other.student.first_name} {other.student.last_name}".strip(),
                "roll_number": other.student.roll_number,
                "similarity_percent": round(ratio * 100, 1),
                "warning": "High content similarity detected. Teacher review is required."
            })
    return sorted(matches, key=lambda item: item["similarity_percent"], reverse=True)


def _local_submission_evaluation(
    assignment: Assignment,
    submission: Submission,
    student_name: str,
    student_text: str,
    reference_text: str,
    total_marks: float,
) -> dict:
    """Provide a content-based fallback when an external AI provider is unavailable."""
    content = (student_text or "").strip()
    requirements = " ".join(
        part for part in (assignment.description or "", reference_text or "")
        if part and not part.startswith("[Attached file:")
    ).lower()
    words = content.split()
    content_lower = content.lower()
    requirement_terms = {
        word.strip(".,:;()[]{}!?\"")
        for word in requirements.split()
        if len(word.strip(".,:;()[]{}!?\"")) >= 5
    }
    matched_terms = sorted({term for term in requirement_terms if term in content_lower})
    sections = sum(marker in content_lower for marker in ("introduction", "method", "analysis", "result", "conclusion", "references"))
    code_signals = sum(marker in content for marker in ("def ", "class ", "SELECT ", "#include", "function "))

    if not content or content.startswith("[Attached file:"):
        score = 0.0
        strengths = ["A submission record exists, but no readable student content was available for evaluation."]
        limitations = ["No extractable answer, code, or explanation was found in the submitted file."]
    else:
        length_score = min(len(words) / 250, 1.0)
        relevance_score = min(len(matched_terms) / max(min(len(requirement_terms), 12), 1), 1.0)
        structure_score = min((sections + code_signals) / 4, 1.0)
        score = 0.15 + (length_score * 0.35) + (relevance_score * 0.35) + (structure_score * 0.15)
        strengths = [f"Submitted {len(words)} readable words in {submission.file_name or 'the response'}."]
        if matched_terms:
            strengths.append(f"Content overlaps with assignment requirements around: {', '.join(matched_terms[:5])}.")
        if sections or code_signals:
            strengths.append("The submission contains identifiable academic sections or implementation constructs.")
        limitations = []
        if len(words) < 80:
            limitations.append("The answer is very brief and does not demonstrate enough working for full credit.")
        if not matched_terms:
            limitations.append("No clear content match with the stated assignment requirements was detected.")
        if not sections and not code_signals:
            limitations.append("Add structured reasoning, evidence, or implementation details to support the answer.")
        if not limitations:
            limitations.append("Review the remaining requirements and add evidence for each expected outcome.")

    if submission.is_late:
        score *= max(0.0, 1 - ((assignment.late_penalty_percentage or 0) / 100))
        limitations.append("Submitted after the deadline; the configured late penalty was applied.")

    score = max(0.0, min(score, 1.0))
    return {
        "suggested_marks": round(total_marks * score, 1),
        "well_attempted": strengths,
        "limitations": limitations,
        "general_remarks": f"{student_name}, this evaluation is based on the readable content in your specific submission: {len(words)} words and {len(matched_terms)} requirement matches. Review the listed limitations before final grading.",
        "provider": "Local Content Analysis Fallback",
    }


@router.post("/submissions/{submission_id}/ai-evaluate")
def evaluate_submission_with_ai(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Assistant evaluation comparing student submission against teacher assignment content/reference.
    Returns suggested marks, well-attempted points, limitations, and overall remarks.
    """
    teacher = _get_authenticated_teacher(current_user, db)
    submission = (
        db.query(Submission)
        .join(Assignment, Assignment.assignment_id == Submission.assignment_id)
        .filter(Submission.submission_id == submission_id, Assignment.teacher_id == teacher.teacher_id)
        .first()
    )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found for the authenticated teacher")

    assignment = submission.assignment
    student = submission.student
    student_name = f"{student.first_name} {student.last_name}".strip()

    teacher_ref_text = _extract_text_content(assignment.attachment_path)
    extracted_file_text = _extract_text_content(submission.file_path)
    student_sub_text = extracted_file_text
    if submission.response_text:
        student_sub_text = f"{submission.response_text}\n\n{student_sub_text}".strip()

    file_status = _file_status(submission.file_path, extracted_file_text if submission.file_path != "inline" else student_sub_text)
    if not file_status["ai_readable"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=file_status["error"] or "The submission cannot be safely read for automatic evaluation."
        )

    assignment_submissions = db.query(Submission).filter(Submission.assignment_id == assignment.assignment_id).all()
    all_content = {
        item.submission_id: f"{item.response_text or ''}\n{_extract_text_content(item.file_path)}".strip()
        for item in assignment_submissions
    }
    similarity_matches = _similarity_matches(submission, assignment_submissions, all_content)

    total_marks = assignment.total_marks or 20.0

    system_prompt = f"""You are an expert AI Academic Grading Assistant for the University of Haripur.
Your task is to conduct an IN-DEPTH, OBJECTIVE, and CRITICAL evaluation of a specific student's assignment submission by comparing the student's actual submitted text/code against the teacher's task requirements and reference material.

GRADING & EVALUATION RULES:
1. DEEP CONTENT ANALYSIS: You must carefully read the submitted student content. DO NOT give generic, repeated, or identical marks to different students.
2. DIFFERENTIATION & ACCURACY:
   - If the student provided thorough, correct, and well-documented work meeting all criteria, award high marks.
   - If the student provided partial, incomplete, superficial, or irrelevant work, penalize proportionally and state what is missing.
   - If the submission is empty or only a trivial placeholder, award minimal marks (e.g. 0 to 20%).
3. SPECIFIC FEEDBACK:
   - "well_attempted": Explicitly cite concrete concepts, calculations, functions, or sections the student did well.
   - "limitations": Explicitly pinpoint missing questions, logical flaws, syntax errors, or shallow explanations.
   - "general_remarks": Personalized academic feedback addressed directly to {student_name}.
4. OUTPUT FORMAT:
   Return strictly valid JSON without backticks, markdown fences, or preamble.

JSON Schema:
{{
  "suggested_marks": <number between 0 and {total_marks}>,
  "well_attempted": ["Specific positive point 1 with reference to student's work", "Specific positive point 2"],
  "limitations": ["Specific deficiency 1", "Specific deficiency 2"],
  "general_remarks": "<Detailed, personalized feedback addressing {student_name}'s specific submission>",
  "confidence_score": <integer 70-100>
}}
"""

    user_prompt = f"""=== TEACHER'S ASSIGNMENT SPECIFICATION ===
Course: {assignment.course.course_code} - {assignment.course.course_title}
Assignment Title: {assignment.title}
Max Marks: {total_marks}
Assignment Description / Requirements:
{assignment.description or "Complete the assigned tasks thoroughly as per course outline."}

Teacher's Reference Material / Solution Outline:
{teacher_ref_text or "No solution attachment. Evaluate according to standard academic quality and assignment description."}

Similarity warning:
{json.dumps(similarity_matches) if similarity_matches else "No high-similarity submission was detected by the deterministic text comparison."}

=== STUDENT SUBMISSION TO EVALUATE ===
Student: {student_name} (Roll No: {student.roll_number})
Attempt Number: {submission.submission_attempt}
Submission Late: {"Yes (Apply late submission penalty if appropriate)" if submission.is_late else "No"}
Submission File Name: {submission.file_name or "N/A"}

Actual Extracted Content of Student's Work:
\"\"\"
{student_sub_text or "NO SUBMISSION CONTENT FOUND / EMPTY SUBMISSION"}
\"\"\"

Carefully analyze the above content and produce the detailed evaluation JSON."""

    evaluation = None
    try:
        ai_raw, provider_name = provider_manager.generate_chat(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        if ai_raw:
            cleaned = ai_raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError("AI evaluation must be a JSON object")
            evaluation = {
                "suggested_marks": max(0.0, min(float(parsed["suggested_marks"]), float(total_marks))),
                "well_attempted": parsed["well_attempted"],
                "limitations": parsed["limitations"],
                "general_remarks": parsed["general_remarks"],
                "similarity_matches": similarity_matches,
                "provider": provider_name or "AI Academic Engine"
            }
    except Exception as e:
        logger.warning(f"Error calling LLM provider for submission evaluation: {e}")

    if not evaluation:
        evaluation = _local_submission_evaluation(
            assignment=assignment,
            submission=submission,
            student_name=student_name,
            student_text=student_sub_text,
            reference_text=teacher_ref_text,
            total_marks=total_marks,
        )
        evaluation["similarity_matches"] = similarity_matches

    # Save to submission record for caching
    try:
        submission.ai_score = evaluation["suggested_marks"]
        submission.ai_feedback = json.dumps(evaluation)
        db.commit()
    except Exception:
        db.rollback()

    return {
        "success": True,
        "submission_id": submission_id,
        "student_name": student_name,
        "total_marks": total_marks,
        "evaluation": evaluation
    }


@router.patch("/submissions/{submission_id}")
def review_teacher_submission(submission_id: int, review: TeacherSubmissionReview, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    teacher = _get_authenticated_teacher(current_user, db)
    submission = db.query(Submission).join(Assignment, Assignment.assignment_id == Submission.assignment_id).filter(Submission.submission_id == submission_id, Assignment.teacher_id == teacher.teacher_id).first()
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found for the authenticated teacher")
    if review.teacher_marks is not None:
        if review.teacher_marks > submission.assignment.total_marks:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Marks cannot exceed the assignment total")
        submission.teacher_marks = review.teacher_marks
        submission.graded = True
        submission.graded_at = datetime.utcnow()
        submission.submission_status = "Reviewed"
    if review.teacher_feedback is not None:
        submission.teacher_feedback = review.teacher_feedback.strip()
    db.commit(); db.refresh(submission)
    return {"success": True, "submission_id": submission.submission_id, "teacher_marks": submission.teacher_marks, "teacher_feedback": submission.teacher_feedback, "status": submission.submission_status}
    

# ==========================================================
# TEACHER AI ACADEMIC AGENT
# ==========================================================

@router.get("/ai/greeting", response_model=TeacherAIGreetingResponse)
def get_teacher_ai_greeting(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a dynamic, teacher-personalised greeting for the AI Academic Agent.
    Teacher identity is derived exclusively from the authenticated JWT.
    """
    teacher = _get_authenticated_teacher(current_user, db)

    designation = teacher.designation or "Teacher"
    full_name = f"{teacher.first_name} {teacher.last_name}".strip()
    greeting = (
        f"Hello {designation} {full_name}! 👋\n"
        f"I am your AI Academic Agent. How can I assist you with your courses, "
        f"grading, or schedule today?"
    )

    return {
        "success": True,
        "greeting": greeting,
        "teacher_name": full_name,
        "first_name": teacher.first_name,
        "designation": designation,
    }


@router.post("/ai/chat", response_model=TeacherAIChatResponse)
def chat_with_teacher_ai(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process a natural-language question from the authenticated teacher.
    Uses real database context and LLM reasoning.
    Teacher identity is derived exclusively from the JWT — never from the client payload.
    """
    teacher = _get_authenticated_teacher(current_user, db)

    ai_response, provider = process_teacher_chat(
        teacher=teacher,
        db=db,
        user_message=payload.message,
        history=payload.history,
    )

    full_name = f"{teacher.first_name} {teacher.last_name}".strip()

    return {
        "success": True,
        "response": ai_response,
        "provider": provider,
        "teacher_name": full_name,
    }
