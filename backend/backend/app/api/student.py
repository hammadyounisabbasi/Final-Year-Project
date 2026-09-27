from datetime import datetime
from typing import Optional
from pathlib import Path
import shutil
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.course_result import CourseResult
from app.models.semester_gpa import SemesterGPA
from app.models.student_cgpa import StudentCGPA
from app.models.grade import Grade
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.attendance import Attendance
from app.models.academic_term import AcademicTerm
from app.models.class_schedule import ClassSchedule
from app.models.student_timetable import StudentTimetable
from app.models.timetable import Timetable, TimetableCourse, TimetableSession
from app.services.academic_results import completed_term_keys, term_status
from app.schemas.student import StudentAssignmentSubmissionCreate, StudentProfileUpdate
from app.schemas.ai_assistant import AIChatRequest, AIChatResponse, AIGreetingResponse, FeeAIChatResponse
from app.services.student_ai_assistant import process_student_chat
from app.services.fee_ai_assistant import process_fee_chat


router = APIRouter(
    prefix="/student",
    tags=["Student"]
)

STUDENT_UPLOAD_ROOT = settings.UPLOAD_DIR / "student_submissions"
STUDENT_ALLOWED_SUFFIXES = {".pdf", ".docx", ".zip", ".txt", ".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _display_time(value: str) -> str:
    return datetime.strptime(value, "%H:%M").strftime("%I:%M %p").lstrip("0")


def _current_student(current_user: User, db: Session) -> Student:
    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")
    student = db.query(Student).filter(Student.user_id == current_user.user_id).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return student


def _student_assignment_query(student: Student, assignment_id: int | None, db: Session):
    query = (
        db.query(Assignment, Enrollment)
        .join(Enrollment, Enrollment.course_id == Assignment.course_id)
        .filter(
            Enrollment.student_id == student.student_id,
            Enrollment.academic_year == Assignment.academic_year,
            Enrollment.semester == Assignment.semester,
            # Legacy assignments created before v7 have no section; they are
            # course-wide. New assignments remain section-scoped.
            or_(Assignment.section.is_(None), Enrollment.section == Assignment.section),
            Enrollment.semester == student.semester,
            Assignment.status == "Published"
        )
    )
    if assignment_id is not None:
        query = query.filter(Assignment.assignment_id == assignment_id)
    return query


@router.get("/attendance")
def get_student_attendance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return attendance belonging only to the JWT-authenticated student."""
    student = _current_student(current_user, db)
    records = (
        db.query(Attendance)
        .filter(Attendance.student_id == student.student_id)
        .order_by(Attendance.attendance_date.desc(), Attendance.attendance_id.desc())
        .all()
    )
    summaries: dict[tuple, dict] = {}
    for record in records:
        key = (record.course_id, record.academic_year, record.semester, record.section)
        if key not in summaries:
            teacher = record.teacher
            summaries[key] = {
                "course_id": record.course_id,
                "course_code": record.course.course_code,
                "course_title": record.course.course_title,
                "teacher": f"{teacher.designation} {teacher.first_name} {teacher.last_name}".strip(),
                "academic_year": record.academic_year,
                "semester": record.semester,
                "section": record.section,
                "total_classes": 0,
                "present": 0,
                "absent": 0,
                "late": 0,
                "leave": 0,
            }
        summary = summaries[key]
        summary["total_classes"] += 1
        if record.status == "Present":
            summary["present"] += 1
        elif record.status == "Absent":
            summary["absent"] += 1
        elif record.status == "Late":
            summary["late"] += 1
        else:
            summary["leave"] += 1
    courses = []
    for summary in summaries.values():
        attended = summary["present"] + summary["late"]
        summary["attended"] = attended
        summary["percentage"] = round((attended * 100 / summary["total_classes"]), 1) if summary["total_classes"] else 0
        courses.append(summary)
    courses.sort(key=lambda item: (item["semester"], item["course_code"]))
    totals = {
        "total_classes": len(records),
        "present": sum(1 for record in records if record.status == "Present"),
        "absent": sum(1 for record in records if record.status == "Absent"),
        "late": sum(1 for record in records if record.status == "Late"),
        "leave": sum(1 for record in records if record.status == "Leave"),
    }
    totals["attended"] = totals["present"] + totals["late"]
    totals["percentage"] = round(totals["attended"] * 100 / totals["total_classes"], 1) if totals["total_classes"] else 0
    return {
        "success": True,
        "student_id": student.student_id,
        "summary": totals,
        "courses": courses,
        "recent": [
            {
                "attendance_id": record.attendance_id,
                "course_code": record.course.course_code,
                "course_title": record.course.course_title,
                "teacher": f"{record.teacher.first_name} {record.teacher.last_name}".strip(),
                "attendance_date": record.attendance_date,
                "status": record.status,
                "remarks": record.remarks,
            }
            for record in records[:50]
        ],
    }


@router.get("/assignments")
def get_student_assignments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = _current_student(current_user, db)
    rows = _student_assignment_query(student, None, db).order_by(Assignment.due_date.asc()).all()
    data = []
    for assignment, enrollment in rows:
        submission = db.query(Submission).filter(Submission.assignment_id == assignment.assignment_id, Submission.student_id == student.student_id).order_by(Submission.submission_attempt.desc()).first()
        data.append({
            "assignment_id": assignment.assignment_id,
            "title": assignment.title,
            "description": assignment.description,
            "assignment_type": assignment.assignment_type,
            "total_marks": assignment.total_marks,
            "course_code": assignment.course.course_code,
            "course_title": assignment.course.course_title,
            "academic_year": assignment.academic_year,
            "semester": assignment.semester,
            "section": assignment.section,
            "due_date": assignment.due_date,
            "attachment_path": assignment.attachment_path,
            "attachment_name": Path(assignment.attachment_path).name if assignment.attachment_path else None,
            "status": assignment.status,
            "submission": None if submission is None else {
                "submission_id": submission.submission_id,
                "submission_title": submission.submission_title,
                "file_name": submission.file_name,
                "file_path": submission.file_path,
                "response_text": submission.response_text,
                "submission_attempt": submission.submission_attempt,
                "submitted_at": submission.submitted_at,
                "submission_status": submission.submission_status,
                "teacher_marks": submission.teacher_marks,
                "teacher_feedback": submission.teacher_feedback,
                "graded": submission.graded
            }
        })
    return {"success": True, "student_id": student.student_id, "assignments": data}


@router.post("/assignments/{assignment_id}/submissions", status_code=status.HTTP_201_CREATED)
def create_student_assignment_submission(assignment_id: int, submission_data: StudentAssignmentSubmissionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = _current_student(current_user, db)
    row = _student_assignment_query(student, assignment_id, db).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment is not available to this student")
    assignment, _ = row
    response_text = submission_data.response_text.strip()
    if not response_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A response is required")
    attempt = (db.query(Submission).filter(Submission.assignment_id == assignment_id, Submission.student_id == student.student_id).count() + 1)
    submission = Submission(assignment_id=assignment_id, student_id=student.student_id, submission_title=(submission_data.submission_title or assignment.title).strip(), file_name="text-response", file_path="inline", response_text=response_text, submission_attempt=attempt, is_late=datetime.utcnow() > assignment.due_date, submission_status="Submitted")
    db.add(submission); db.commit(); db.refresh(submission)
    return {"success": True, "submission_id": submission.submission_id, "status": submission.submission_status, "submitted_at": submission.submitted_at}


@router.post("/assignments/{assignment_id}/submissions/file", status_code=status.HTTP_201_CREATED)
def create_student_file_submission(assignment_id: int, response_text: str = Form(""), attachment: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = _current_student(current_user, db)
    row = _student_assignment_query(student, assignment_id, db).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment is not available to this student")
    suffix = Path(attachment.filename or "").suffix.lower()
    if suffix not in STUDENT_ALLOWED_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only PDF, DOCX, ZIP, and TXT files are allowed")
    assignment, _ = row
    STUDENT_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    stored = STUDENT_UPLOAD_ROOT / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{suffix}"
    with stored.open("wb") as output:
        shutil.copyfileobj(attachment.file, output)
    if stored.stat().st_size > 25 * 1024 * 1024:
        stored.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds the 25 MB limit")
    attempt = db.query(Submission).filter(Submission.assignment_id == assignment_id, Submission.student_id == student.student_id).count() + 1
    submission = Submission(assignment_id=assignment_id, student_id=student.student_id, submission_title=attachment.filename, file_name=attachment.filename, file_path=str(stored.relative_to(settings.UPLOAD_DIR.parent)).replace("\\", "/"), response_text=response_text.strip() or None, submission_attempt=attempt, is_late=datetime.utcnow() > assignment.due_date, submission_status="Submitted")
    db.add(submission); db.commit(); db.refresh(submission)
    return {"success": True, "submission_id": submission.submission_id, "status": submission.submission_status, "submitted_at": submission.submitted_at}


# ==========================================================
# STUDENT PROFILE
# ==========================================================

@router.get("/profile")
def get_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the profile of the currently authenticated student.
    """

    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )

    student = (
        db.query(Student)
        .filter(
            Student.user_id == current_user.user_id
        )
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    return {
        "student_id": student.student_id,
        "user_id": student.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "roll_number": student.roll_number,
        "registration_number": student.registration_number,

        "first_name": student.first_name,
        "last_name": student.last_name,
        "gender": student.gender,

        "date_of_birth": student.date_of_birth,
        "phone": student.phone,
        "emergency_contact": student.emergency_contact,
        "address": student.address,

        "program": student.program,
        "semester": student.semester,
        "section": student.section,
        "batch_year": student.batch_year,

        "admission_date": student.admission_date,
        "expected_graduation": student.expected_graduation,
        # Canonical API name; retain the legacy key above for existing clients.
        "expected_graduation_date": student.expected_graduation,

        "credits_completed": student.credits_completed,
        "profile_photo": student.profile_photo,
        "status": student.status,
        "created_at": student.created_at,
        "updated_at": student.updated_at,

        "department": {
            "department_id": student.department.department_id,
            "department_code": student.department.department_code,
            "department_name": student.department.department_name,
            "department_short_name": (
                student.department.department_short_name
            ),
        }
    }


@router.put("/profile")
def update_student_profile(
    profile_data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update editable contact/profile information for the currently authenticated student.
    """

    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )

    student = (
        db.query(Student)
        .filter(
            Student.user_id == current_user.user_id
        )
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    if profile_data.first_name is not None and profile_data.first_name.strip():
        student.first_name = profile_data.first_name.strip()
    if profile_data.last_name is not None and profile_data.last_name.strip():
        student.last_name = profile_data.last_name.strip()
    if profile_data.phone is not None:
        student.phone = profile_data.phone.strip()
    if profile_data.emergency_contact is not None:
        student.emergency_contact = profile_data.emergency_contact.strip()
    if profile_data.address is not None:
        student.address = profile_data.address.strip()

    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)

    return {
        "success": True,
        "message": "Profile updated successfully",
        "student_id": student.student_id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "phone": student.phone,
        "emergency_contact": student.emergency_contact,
        "address": student.address,
        "updated_at": student.updated_at
    }


# ==========================================================
# STUDENT COURSES
# ==========================================================

@router.get("/courses")
def get_student_courses(
    semester: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all enrolled courses, instructor information, schedules, and metrics
    for the currently authenticated student.
    """

    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )

    student = (
        db.query(Student)
        .filter(
            Student.user_id == current_user.user_id
        )
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    target_semester = semester if semester is not None else student.semester

    # Query enrollments
    query = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student.student_id
        )
    )
    if target_semester:
        query = query.filter(Enrollment.semester == target_semester)

    enrollments = query.order_by(Enrollment.enrollment_id.asc()).all()

    # Find available distinct semesters for semester selector
    all_enrollments = (
        db.query(Enrollment.semester, Enrollment.academic_year)
        .filter(
            Enrollment.student_id == student.student_id
        )
        .distinct()
        .all()
    )
    available_semesters = [
        {
            "semester": sem,
            "academic_year": year,
            "label": f"Semester {sem} ({year})"
        }
        for sem, year in sorted(all_enrollments, key=lambda x: x[0])
    ]

    courses_list = []
    total_credits = 0

    for idx, enr in enumerate(enrollments):
        c = enr.course
        t = c.teacher if c else None
        d = c.department if c else None

        if c:
            total_credits += c.credit_hours

        teacher_name = (
            f"{t.designation} {t.first_name} {t.last_name}".strip()
            if t else "Faculty Assigned"
        )

        schedule_rows = (
            db.query(ClassSchedule)
            .filter(
                ClassSchedule.course_id == enr.course_id,
                ClassSchedule.academic_year == enr.academic_year,
                ClassSchedule.semester == enr.semester,
                ClassSchedule.section == (enr.section or student.section or "A"),
                ClassSchedule.status == "Active",
            )
            .order_by(ClassSchedule.day_of_week.asc(), ClassSchedule.start_time.asc())
            .all()
        )
        schedule = "; ".join(
            f"{row.day_of_week[:3]} {_display_time(row.start_time)}-{_display_time(row.end_time)}"
            for row in schedule_rows
        ) or "Schedule TBA"
        location = ", ".join(dict.fromkeys(row.room_location for row in schedule_rows)) or "Room TBA"
        schedule_entries = [
            {
                "schedule_id": row.schedule_id,
                "day_of_week": row.day_of_week,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "room_location": row.room_location,
                "class_type": row.class_type,
            }
            for row in schedule_rows
        ]

        courses_list.append({
            "enrollment_id": enr.enrollment_id,
            "course_id": c.course_id if c else None,
            "course_code": c.course_code if c else "",
            "course_title": c.course_title if c else "",
            "course_description": c.course_description if c else "",
            "credit_hours": c.credit_hours if c else 0,
            "course_type": c.course_type if c else "Core",
            "semester": enr.semester,
            "section": enr.section or student.section or "A",
            "academic_year": enr.academic_year,
            "enrollment_status": enr.enrollment_status,
            "schedule": schedule,
            "location": location,
            "schedule_entries": schedule_entries,
            "progress_percentage": 75,
            "instructor": {
                "teacher_id": t.teacher_id if t else None,
                "name": teacher_name,
                "first_name": t.first_name if t else "",
                "last_name": t.last_name if t else "",
                "designation": t.designation if t else "",
                "office_email": t.office_email if t else "",
                "office_room": t.office_room if t else "",
                "profile_photo": t.profile_photo if t else None
            },
            "department": {
                "department_id": d.department_id if d else None,
                "department_code": d.department_code if d else "",
                "department_name": d.department_name if d else ""
            }
        })

    # Fetch CGPA
    cgpa_query = text(
        "SELECT overall_cgpa, total_completed_credit_hours "
        "FROM Student_CGPA WHERE student_id = :s_id LIMIT 1"
    )
    cgpa_row = db.execute(
        cgpa_query,
        {"s_id": student.student_id}
    ).mappings().first()

    cgpa_val = float(cgpa_row["overall_cgpa"]) if cgpa_row and cgpa_row["overall_cgpa"] is not None else 0.0
    completed_cr = int(cgpa_row["total_completed_credit_hours"]) if cgpa_row and cgpa_row["total_completed_credit_hours"] is not None else (student.credits_completed or 0)

    return {
        "success": True,
        "student": {
            "student_id": student.student_id,
            "name": f"{student.first_name} {student.last_name}".strip(),
            "roll_number": student.roll_number,
            "program": student.program,
            "semester": student.semester,
            "section": student.section,
            "profile_photo": student.profile_photo
        },
        "metrics": {
            "enrolled_courses_count": len(courses_list),
            "total_credit_hours": total_credits,
            "cgpa": round(cgpa_val, 2),
            "completed_credits": completed_cr,
            "current_semester": target_semester
        },
        "available_semesters": available_semesters,
        "courses": courses_list
    }


# ==========================================================
# STUDENT TIMETABLE
# ==========================================================

@router.get("/timetable")
def get_student_timetable(
    semester: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return the student's real, teacher-owned class schedule."""
    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")

    student = db.query(Student).filter(Student.user_id == current_user.user_id).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    target_semester = semester if semester is not None else student.semester

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student.student_id,
            Enrollment.semester == target_semester,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"])
        )
        .order_by(Enrollment.enrollment_id.asc())
        .all()
    )

    # Available semesters for dropdown
    all_sems = (
        db.query(Enrollment.semester, Enrollment.academic_year)
        .filter(Enrollment.student_id == student.student_id)
        .distinct().all()
    )
    available_semesters = [
        {"semester": s, "academic_year": y, "label": f"Semester {s} ({y})"}
        for s, y in sorted(all_sems, key=lambda x: x[0])
    ]

    # Only canonical database schedules are displayed; no synthetic slots/rooms.
    themes = ["slot-ds", "slot-db", "slot-dm", "slot-we", "slot-os", "slot-cn", "slot-isl", "slot-welab"]
    total_credits = sum(enrollment.course.credit_hours for enrollment in enrollments if enrollment.course)
    published_schedules = (
        db.query(ClassSchedule)
        .join(TimetableSession, TimetableSession.legacy_schedule_id == ClassSchedule.schedule_id)
        .join(TimetableCourse, TimetableCourse.timetable_course_id == TimetableSession.timetable_course_id)
        .join(Timetable, Timetable.timetable_id == TimetableCourse.timetable_id)
        .join(Enrollment, (Enrollment.course_id == TimetableCourse.course_id) & (Enrollment.academic_year == ClassSchedule.academic_year) & (Enrollment.semester == Timetable.semester) & (Enrollment.section == Timetable.section))
        .filter(
            Enrollment.student_id == student.student_id,
            Enrollment.semester == target_semester,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
            Timetable.status == "Published",
            Timetable.department_id == student.department_id,
            Timetable.semester == target_semester,
        )
        .distinct().all()
    )
    legacy_schedules = (
        db.query(ClassSchedule)
        .join(StudentTimetable, StudentTimetable.schedule_id == ClassSchedule.schedule_id)
        .join(Enrollment, Enrollment.enrollment_id == StudentTimetable.enrollment_id)
        .join(Course, Course.course_id == ClassSchedule.course_id)
        .filter(
            StudentTimetable.student_id == student.student_id,
            Enrollment.semester == target_semester,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
            ClassSchedule.status == "Active",
        )
        .all()
    )
    # Published aggregate sessions are canonical. Legacy links are a temporary
    # compatibility projection for attendance and old portal components.
    real_schedules = published_schedules or legacy_schedules
    day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5}
    real_schedules.sort(key=lambda item: (day_order.get(item.day_of_week, 99), item.start_time, item.course_id))

    def display_time(value: str) -> str:
        return datetime.strptime(value, "%H:%M").strftime("%I:%M %p").lstrip("0")

    slot_pairs = sorted({(item.start_time, item.end_time) for item in real_schedules})
    slot_indexes = {pair: index for index, pair in enumerate(slot_pairs)}
    time_slots = [
        {"label": f"{display_time(start)} - {display_time(end)}", "startHour": int(start[:2]), "startMin": int(start[3:])}
        for start, end in slot_pairs
    ]
    timetable_grid, upcoming_classes, schedule_conflicts = {}, [], []
    for index, schedule in enumerate(real_schedules):
        day_index = day_order.get(schedule.day_of_week)
        if day_index is None:
            continue
        course, teacher = schedule.course, schedule.teacher
        teacher_name = f"{teacher.designation} {teacher.first_name} {teacher.last_name}".strip()
        slot_index = slot_indexes[(schedule.start_time, schedule.end_time)]
        grid_key = f"{slot_index}-{day_index}"
        class_entry = {
            "name": course.course_title, "code": course.course_code,
            "teacher": teacher_name, "teacher_email": teacher.office_email or "",
            "room": schedule.room_location, "theme": themes[index % len(themes)],
            "credit_hours": course.credit_hours, "course_type": course.course_type or "Core",
            "schedule_id": schedule.schedule_id,
        }
        existing_entry = timetable_grid.get(grid_key)
        if existing_entry is None:
            timetable_grid[grid_key] = class_entry
        else:
            entries = existing_entry if isinstance(existing_entry, list) else [existing_entry]
            entries.append(class_entry)
            timetable_grid[grid_key] = entries
            schedule_conflicts.append({
                "day": schedule.day_of_week,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "schedule_ids": [entry["schedule_id"] for entry in entries],
            })
        upcoming_classes.append({
            "time": display_time(schedule.start_time), "title": course.course_title,
            "code": course.course_code, "teacher": teacher_name,
            "room": schedule.room_location, "day": schedule.day_of_week,
            "statusText": schedule.class_type, "statusClass": "blue",
        })
    total_credits = sum(item.course.credit_hours for item in enrollments if item.course)
    classes_per_week = len(real_schedules)

    # Determine next class info (first entry is "next class")
    next_class_name = upcoming_classes[0]["title"] if upcoming_classes else "No Class"
    next_class_time = upcoming_classes[0]["time"] if upcoming_classes else "-"
    next_class_room = upcoming_classes[0]["room"] if upcoming_classes else "-"

    # CGPA
    cgpa_row = db.execute(
        text("SELECT overall_cgpa FROM Student_CGPA WHERE student_id = :s_id LIMIT 1"),
        {"s_id": student.student_id}
    ).mappings().first()
    cgpa_val = float(cgpa_row["overall_cgpa"]) if cgpa_row and cgpa_row["overall_cgpa"] else 0.0

    return {
        "success": True,
        "student": {
            "student_id": student.student_id,
            "name": f"{student.first_name} {student.last_name}".strip(),
            "roll_number": student.roll_number,
            "program": student.program,
            "semester": student.semester,
            "section": student.section,
            "profile_photo": student.profile_photo
        },
        "metrics": {
            "total_courses": len(enrollments),
            "total_credits": total_credits,
            "classes_per_week": classes_per_week,
            "next_class": next_class_name,
            "next_class_time": next_class_time,
            "current_room": next_class_room,
            "room_location": f"Semester {target_semester} Schedule",
            "cgpa": round(cgpa_val, 2),
            "current_semester": target_semester
        },
        "time_slots": time_slots,
        "timetable_grid": timetable_grid,
        "schedule_conflicts": schedule_conflicts,
        "upcoming_classes": upcoming_classes[:5],
        "available_semesters": available_semesters
    }


# ==========================================================
# STUDENT RESULTS & CGPA
# ==========================================================

@router.get("/results")
def get_student_results(
    semester: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed academic results, semester wise summary, grades, and CGPA metrics
    for the currently authenticated student.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")

    student = db.query(Student).filter(Student.user_id == current_user.user_id).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student.student_id).all()
    # A profile's current semester is in progress for that student.  Academic
    # term rows are shared by cohorts, so their global status cannot finalize a
    # current semester for every student who has the same term number.
    current_term_keys = {(e.academic_year, e.semester) for e in enrollments if e.semester == student.semester}
    # Progress belongs to the student cohort: every lower semester is completed
    # and the profile semester is the only active one, regardless of a shared
    # calendar row used by a different cohort.
    completed_keys = {
        (e.academic_year, e.semester)
        for e in enrollments
        if e.semester < student.semester
    }
    current_unfinalized_term_keys = current_term_keys
    in_progress_terms = [{"semester": e.semester, "academic_year": e.academic_year,
                          "label": f"Semester {e.semester} ({e.academic_year})",
                          "status": "Active"}
                         for e in enrollments
                         if (e.academic_year, e.semester) in current_unfinalized_term_keys]
    # Deduplicate terms while retaining all current classes in /student/courses.
    in_progress_terms = list({(x["academic_year"], x["semester"]): x for x in in_progress_terms}.values())

    rows = [r for r in db.query(CourseResult).filter(CourseResult.student_id == student.student_id).all()
            if (r.academic_year, r.semester) in completed_keys
            and (r.academic_year, r.semester) not in current_unfinalized_term_keys]
    if semester is not None:
        rows = [r for r in rows if r.semester == semester]
    rows.sort(key=lambda r: (r.academic_year, r.semester, r.result_id))
    formatted_course_results = []
    grouped = {}
    for r in rows:
        c = r.course
        formatted_course_results.append({"id": r.result_id, "code": c.course_code if c else "",
            "name": c.course_title if c else "", "credit": r.credit_hours,
            "sessional_marks": r.sessional_marks or 0.0, "midterm_marks": r.midterm_marks or 0.0,
            "final_marks": r.final_marks or 0.0, "marks": float(r.total_marks or 0),
            "ng": f"{float(r.grade_points or 0):.2f}", "grade": r.letter_grade or "N/A",
            "gradePoints": f"{float(r.quality_points or 0):.2f}", "remarks": r.result_status or "Finalized",
            "category": c.course_type.lower() if c and c.course_type else "core", "semester": r.semester,
            "academic_year": r.academic_year})
        grouped.setdefault((r.academic_year, r.semester), []).append(r)

    semester_summary, total_completed_credits, total_grade_points = [], 0, 0.0
    for (year, sem), term_rows in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        credits = sum(int(r.credit_hours or 0) for r in term_rows)
        quality = sum(float(r.quality_points or 0) for r in term_rows)
        earned = sum(int(r.credit_hours or 0) for r in term_rows if (r.letter_grade or "").upper() != "F")
        total_completed_credits += earned
        total_grade_points += quality
        gpa = round(quality / credits, 2) if credits else 0.0
        semester_summary.append({"semester": sem, "academic_year": year, "semester_name": f"Semester {sem} ({year})",
            "credit_hours": earned, "gpa": gpa,
            "cgpa": round(total_grade_points / total_completed_credits, 2) if total_completed_credits else 0.0,
            "grade_points": round(quality, 2),
            "percentage": f"{(sum(float(r.total_marks or 0) for r in term_rows) / (len(term_rows) * 100) * 100):.2f}%",
            "status": "Completed"})

    overall_cgpa = round(total_grade_points / total_completed_credits, 2) if total_completed_credits else 0.0
    academic_standing = "Good Standing" if overall_cgpa >= 2 else ("Academic Warning" if total_completed_credits else "No finalized result")
    available_semesters = [{"semester": s["semester"], "academic_year": s["academic_year"], "label": s["semester_name"]}
                           for s in semester_summary]
    total_obtained_marks = sum(float(r.total_marks or 0) for r in rows)
    total_max_marks = len(rows) * 100
    current_summary_bar = {"gpa": "Not finalized" if in_progress_terms else f"{overall_cgpa:.2f} / 4.00",
        "credit_hours": total_completed_credits, "grade_points": f"{total_grade_points:.2f}",
        "obtained_marks": f"{int(total_obtained_marks)} / {int(total_max_marks)}",
        "percentage": f"{(total_obtained_marks / total_max_marks * 100):.2f}%" if total_max_marks else "0.00%",
        "result_status": "In Progress" if in_progress_terms else "Finalized"}
    chart_labels = [s["semester_name"] for s in semester_summary]
    chart_data = [s["cgpa"] for s in semester_summary]

    return {
        "success": True,
        "student": {
            "student_id": student.student_id,
            "name": f"{student.first_name} {student.last_name}".strip(),
            "roll_number": student.roll_number,
            "program": student.program,
            "semester": student.semester,
            "section": student.section,
            "profile_photo": student.profile_photo
        },
        "metrics": {
            "cgpa": overall_cgpa,
            "total_credit_hours": total_completed_credits,
            "total_grade_points": total_grade_points,
            "sessional_average": current_summary_bar["percentage"],
            "academic_standing": academic_standing
        },
        "current_semester_summary": current_summary_bar,
        "available_semesters": available_semesters,
        "course_results": formatted_course_results,
        "semester_summary": semester_summary,
        "in_progress_terms": in_progress_terms,
        "result_notice": "Current semester is in progress. Final results, GPA, CGPA contribution, and marksheet are unavailable until the term is completed." if in_progress_terms else None,
        "chart": {
            "labels": chart_labels,
            "data": chart_data
        }
    }


# ==========================================================
# STUDENT DASHBOARD
# ==========================================================

@router.get("/dashboard")
def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return complete academic dashboard data for the
    currently authenticated student.

    Data sources:
        Users
        Students
        Enrollments
        Courses
        Course_Results
        Semester_GPA
        Student_CGPA
    """

    # ------------------------------------------------------
    # 1. VERIFY STUDENT ROLE
    # ------------------------------------------------------

    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )

    # ------------------------------------------------------
    # 2. FIND CURRENT STUDENT
    # ------------------------------------------------------

    student = (
        db.query(Student)
        .filter(
            Student.user_id == current_user.user_id
        )
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    student_id = student.student_id
    current_semester = student.semester

    # ======================================================
    # 3. STUDENT BASIC INFORMATION
    # ======================================================

    student_data = {
        "student_id": student.student_id,
        "user_id": student.user_id,
        "name": f"{student.first_name} {student.last_name}".strip(),
        "first_name": student.first_name,
        "last_name": student.last_name,
        "roll_number": student.roll_number,
        "registration_number": student.registration_number,
        "program": student.program,
        "semester": student.semester,
        "section": student.section,
        "batch_year": student.batch_year,
        "credits_completed": student.credits_completed,
        "profile_photo": student.profile_photo,
        "status": student.status
    }

    # ======================================================
    # 4. CURRENT ENROLLED COURSES
    # ======================================================

    courses_query = text("""
        SELECT
            e.enrollment_id,
            e.course_id,
            e.academic_year,
            e.semester,
            e.section AS enrollment_section,
            e.enrollment_status,

            c.course_code,
            c.course_title,
            c.course_description,
            c.credit_hours,
            c.course_type,
            c.status AS course_status

        FROM Enrollments e

        INNER JOIN Courses c
            ON c.course_id = e.course_id

        WHERE e.student_id = :student_id
          AND e.semester = :semester
          AND e.enrollment_status = 'Enrolled'
          AND c.status = 'Active'

        ORDER BY c.course_code
    """)

    courses_result = db.execute(
        courses_query,
        {
            "student_id": student_id,
            "semester": current_semester
        }
    )

    courses = []

    for row in courses_result.mappings():
        courses.append({
            "enrollment_id": row["enrollment_id"],
            "course_id": row["course_id"],
            "course_code": row["course_code"],
            "course_title": row["course_title"],
            "course_description": row["course_description"],
            "credit_hours": row["credit_hours"],
            "course_type": row["course_type"],
            "academic_year": row["academic_year"],
            "semester": row["semester"],
            "section": (
                row["enrollment_section"]
                or student.section
            ),
            "enrollment_status": row["enrollment_status"]
        })

    # ======================================================
    # 5. OVERALL CGPA
    # ======================================================

    cgpa_query = text("""
        SELECT
            total_completed_credit_hours,
            total_grade_points,
            overall_cgpa,
            total_passed_courses,
            total_failed_courses,
            academic_status,
            graduation_eligible,
            honors_status,
            remarks,
            last_calculated

        FROM Student_CGPA

        WHERE student_id = :student_id

        LIMIT 1
    """)

    cgpa_row = db.execute(
        cgpa_query,
        {
            "student_id": student_id
        }
    ).mappings().first()

    if cgpa_row:
        cgpa_data = {
            "total_completed_credit_hours":
                cgpa_row["total_completed_credit_hours"],

            "total_grade_points":
                cgpa_row["total_grade_points"],

            "overall_cgpa":
                cgpa_row["overall_cgpa"],

            "total_passed_courses":
                cgpa_row["total_passed_courses"],

            "total_failed_courses":
                cgpa_row["total_failed_courses"],

            "academic_status":
                cgpa_row["academic_status"],

            "graduation_eligible":
                bool(cgpa_row["graduation_eligible"]),

            "honors_status":
                cgpa_row["honors_status"],

            "remarks":
                cgpa_row["remarks"]
        }
    else:
        cgpa_data = {
            "total_completed_credit_hours": 0,
            "total_grade_points": 0,
            "overall_cgpa": 0,
            "total_passed_courses": 0,
            "total_failed_courses": 0,
            "academic_status": "Good Standing",
            "graduation_eligible": False,
            "honors_status": "None",
            "remarks": None
        }

    # Dashboard metrics must use the same completed-term boundary as /results;
    # cached CGPA rows can otherwise still include an active term.
    dashboard_current_term_keys = {(course["academic_year"], course["semester"]) for course in courses
                                   if course["semester"] == current_semester}
    # The current semester belongs to this student's active progression.  A
    # shared Academic_Terms row may be completed for an older cohort, so it
    # must not turn this student's active semester into a finalized one.
    dashboard_current_unfinalized_keys = dashboard_current_term_keys
    dashboard_final_rows = [r for r in db.query(CourseResult).filter(
        CourseResult.student_id == student_id
    ).all() if r.semester < student.semester]
    dashboard_credits = sum(int(r.credit_hours or 0) for r in dashboard_final_rows
                            if (r.letter_grade or "").upper() != "F")
    dashboard_quality = sum(float(r.quality_points or 0) for r in dashboard_final_rows)
    cgpa_data["total_completed_credit_hours"] = dashboard_credits
    cgpa_data["total_grade_points"] = round(dashboard_quality, 2)
    cgpa_data["overall_cgpa"] = round(dashboard_quality / dashboard_credits, 2) if dashboard_credits else 0.0
    cgpa_data["academic_status"] = "Good Standing" if cgpa_data["overall_cgpa"] >= 2 else (
        "Academic Warning" if dashboard_credits else "No finalized result"
    )

    # ======================================================
    # 6. CURRENT / LATEST SEMESTER GPA
    # ======================================================

    semester_gpa_query = text("""
        SELECT
            semester_gpa_id,
            semester,
            academic_year,
            total_credit_hours,
            earned_credit_hours,
            total_grade_points,
            semester_gpa,
            academic_status,
            remarks

        FROM Semester_GPA

        WHERE student_id = :student_id
          AND semester = :semester

        ORDER BY semester_gpa_id DESC

        LIMIT 1
    """)

    semester_gpa_row = db.execute(
        semester_gpa_query,
        {
            "student_id": student_id,
            "semester": current_semester
        }
    ).mappings().first()

    # If current semester GPA does not exist yet,
    # find the latest completed semester GPA.

    # The student's current enrollment never has a final semester GPA.
    current_term_in_progress = bool(dashboard_current_unfinalized_keys)
    if current_term_in_progress:
        semester_gpa_row = None

    if semester_gpa_row is None and not current_term_in_progress:

        semester_gpa_query = text("""
            SELECT
                semester_gpa_id,
                semester,
                academic_year,
                total_credit_hours,
                earned_credit_hours,
                total_grade_points,
                semester_gpa,
                academic_status,
                remarks

            FROM Semester_GPA

            WHERE student_id = :student_id

            ORDER BY semester DESC, semester_gpa_id DESC

            LIMIT 1
        """)

        semester_gpa_row = db.execute(
            semester_gpa_query,
            {
                "student_id": student_id
            }
        ).mappings().first()

    if semester_gpa_row:

        semester_gpa_data = {
            "semester_gpa_id":
                semester_gpa_row["semester_gpa_id"],

            "semester":
                semester_gpa_row["semester"],

            "academic_year":
                semester_gpa_row["academic_year"],

            "total_credit_hours":
                semester_gpa_row["total_credit_hours"],

            "earned_credit_hours":
                semester_gpa_row["earned_credit_hours"],

            "total_grade_points":
                semester_gpa_row["total_grade_points"],

            "semester_gpa":
                semester_gpa_row["semester_gpa"],

            "academic_status":
                semester_gpa_row["academic_status"],

            "remarks":
                semester_gpa_row["remarks"]
        }

    else:

        semester_gpa_data = {
            "semester_gpa_id": None,
            "semester": None,
            "academic_year": None,
            "total_credit_hours": 0,
            "earned_credit_hours": 0,
            "total_grade_points": 0,
            "semester_gpa": 0,
            "academic_status": "Good Standing",
            "remarks": None
        }

    # ======================================================
    # 7. COURSE RESULTS
    # ======================================================

    results_query = text("""
        SELECT
            cr.result_id,
            cr.enrollment_id,
            cr.student_id,
            cr.course_id,
            cr.teacher_id,

            cr.semester,
            cr.academic_year,

            cr.credit_hours,
            cr.quality_points,

            cr.sessional_marks,
            cr.midterm_marks,
            cr.final_marks,

            cr.total_marks,
            cr.percentage,
            cr.letter_grade,
            cr.grade_points,

            cr.result_status,
            cr.verified,
            cr.published,
            cr.locked,
            cr.remarks,

            c.course_code,
            c.course_title

        FROM Course_Results cr

        INNER JOIN Courses c
            ON c.course_id = cr.course_id

        INNER JOIN Enrollments e
            ON e.enrollment_id = cr.enrollment_id

        WHERE cr.student_id = :student_id
          AND cr.published = 1

        ORDER BY cr.semester DESC, c.course_code
    """)

    results_rows = db.execute(
        results_query,
        {
            "student_id": student_id
        }
    )

    course_results = []

    for row in results_rows.mappings():

        course_results.append({
            "result_id": row["result_id"],
            "enrollment_id": row["enrollment_id"],
            "course_id": row["course_id"],
            "course_code": row["course_code"],
            "course_title": row["course_title"],
            "teacher_id": row["teacher_id"],

            "semester": row["semester"],
            "academic_year": row["academic_year"],

            "credit_hours": row["credit_hours"],
            "quality_points": row["quality_points"],

            "sessional_marks": row["sessional_marks"],
            "midterm_marks": row["midterm_marks"],
            "final_marks": row["final_marks"],

            "total_marks": row["total_marks"],
            "percentage": row["percentage"],
            "letter_grade": row["letter_grade"],
            "grade_points": row["grade_points"],

            "result_status": row["result_status"],
            "verified": bool(row["verified"]),
            "published": bool(row["published"]),
            "locked": bool(row["locked"]),

            "remarks": row["remarks"]
        })

    # Never surface active-term gradebook progress as a finalized dashboard result.
    course_results = [result for result in course_results if (
        result["academic_year"], result["semester"]
    ) in completed_term_keys(db) and (
        result["academic_year"], result["semester"]
    ) not in dashboard_current_unfinalized_keys]

    # ======================================================
    # 8. RESULT SUMMARY
    # ======================================================

    grade_summary = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
        "F": 0
    }

    for result in course_results:

        letter = result["letter_grade"]

        if letter in grade_summary:
            grade_summary[letter] += 1

    # ======================================================
    # 9. FINAL DASHBOARD RESPONSE
    # ======================================================

    return {
        "success": True,

        "student": student_data,

        "academic": {
            "current_semester": current_semester,
            "enrolled_courses": len(courses),

            "cgpa": cgpa_data,
            "semester_gpa": semester_gpa_data
        },

        "courses": courses,

        "results": {
            "total_results": len(course_results),
            "grade_summary": grade_summary,
            "course_results": course_results
        },

        "academic_standing": cgpa_data["academic_status"]
    }


# ==========================================================
# STUDENT FEES
# ==========================================================

@router.get("/fees")
def get_student_fees(
    semester: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get fee details, payment status, breakdown, scholarship information,
    and payment history for the currently authenticated student.
    Data sources:
        Fee_Records
        Students
        Users
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )

    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.user_id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    student_id = student.student_id

    # Query all fee records for this student
    all_fee_rows = db.execute(
        text("""
            SELECT
                fee_id,
                student_id,
                semester,
                academic_year,
                total_fee,
                scholarship_amount,
                fine_amount,
                discount_amount,
                payable_amount,
                paid_amount,
                remaining_amount,
                payment_status,
                payment_method,
                transaction_id,
                payment_date,
                due_date,
                verified,
                remarks,
                created_at,
                updated_at
            FROM Fee_Records
            WHERE student_id = :student_id
            ORDER BY semester DESC
        """),
        {"student_id": student_id}
    ).mappings().all()

    # Determine target fee record (selected semester or latest/current semester record)
    target_record = None
    if semester is not None:
        target_record = next((r for r in all_fee_rows if r["semester"] == semester), None)
    
    if target_record is None and all_fee_rows:
        target_record = next((r for r in all_fee_rows if r["semester"] == student.semester), all_fee_rows[0])

    if target_record:
        rec_semester = target_record["semester"]
        rec_acad_year = target_record["academic_year"]
        current_sem_label = f"Semester {rec_semester} ({rec_acad_year})"
        total_fee = float(target_record["total_fee"] or 0.0)
        paid_amount = float(target_record["paid_amount"] or 0.0)
        outstanding_amount = float(target_record["remaining_amount"] if target_record["remaining_amount"] is not None else (total_fee - paid_amount))
        scholarship_amount = float(target_record["scholarship_amount"] or 0.0)
        payable_amount = float(target_record["payable_amount"] or (total_fee - scholarship_amount))
        fine_amount = float(target_record["fine_amount"] or 0.0)
        raw_status = target_record["payment_status"] or "Pending"
        fee_status = "Paid" if raw_status == "Paid" else ("Partial" if raw_status == "Partial" else "Unpaid")
        is_scholarship = scholarship_amount > 0 or (target_record["remarks"] and "scholarship" in target_record["remarks"].lower())
        
        due_date_raw = target_record["due_date"]
        due_date_str = "31 May 2025"
        if due_date_raw:
            try:
                if isinstance(due_date_raw, str):
                    d_obj = datetime.strptime(due_date_raw.split()[0], "%Y-%m-%d")
                else:
                    d_obj = due_date_raw
                due_date_str = d_obj.strftime("%d %b %Y")
            except Exception:
                due_date_str = str(due_date_raw).split()[0]

        payment_method = target_record["payment_method"] or "Online / Bank"
        transaction_id = target_record["transaction_id"] or f"TXN-CSE-2026-{target_record['fee_id']}"
        remarks = target_record["remarks"] or ("Fee Paid" if fee_status == "Paid" else "Fee Unpaid")
    else:
        # Fallback when student has no fee row in database yet
        total_fee = 55000.0
        paid_amount = 0.0
        outstanding_amount = 55000.0
        scholarship_amount = 0.0
        payable_amount = 55000.0
        fine_amount = 0.0
        fee_status = "Unpaid"
        is_scholarship = False
        due_date_str = "31 May 2025"
        current_sem_label = f"Semester {student.semester or 1} (2026-27)"
        payment_method = "Online / Bank"
        transaction_id = None
        remarks = "Fee Pending"

    # Deterministic standard fee breakdown proportional to total fee
    tuition_share = round(total_fee * (30000.0 / 63500.0))
    exam_share = round(total_fee * (8000.0 / 63500.0))
    lab_share = round(total_fee * (5000.0 / 63500.0))
    lib_share = round(total_fee * (3000.0 / 63500.0))
    ict_share = round(total_fee * (2500.0 / 63500.0))
    act_share = round(total_fee * (1500.0 / 63500.0))
    misc_share = int(total_fee - (tuition_share + exam_share + lab_share + lib_share + ict_share + act_share))

    fee_breakdown = [
        {"id": 1, "head": "Tuition Fee", "amount": int(tuition_share)},
        {"id": 2, "head": "Examination Fee", "amount": int(exam_share)},
        {"id": 3, "head": "Lab Fee", "amount": int(lab_share)},
        {"id": 4, "head": "Library Fee", "amount": int(lib_share)},
        {"id": 5, "head": "ICT Fee", "amount": int(ict_share)},
        {"id": 6, "head": "Student Activity Fee", "amount": int(act_share)},
        {"id": 7, "head": "Miscellaneous / Other Charges", "amount": misc_share}
    ]

    # Semester Summary (all fee records)
    semester_summary = []
    for r in all_fee_rows:
        r_sem = r["semester"]
        r_year = r["academic_year"]
        is_current = (r_sem == (target_record["semester"] if target_record else student.semester))
        sem_title = f"Semester {r_sem} ({r_year})" + (" (Current)" if is_current else "")
        r_total = float(r["total_fee"] or 0.0)
        r_paid = float(r["paid_amount"] or 0.0)
        r_out = float(r["remaining_amount"] if r["remaining_amount"] is not None else (r_total - r_paid))
        r_status = "Paid" if (r["payment_status"] == "Paid" or r_out == 0) else "Unpaid"
        semester_summary.append({
            "semester": sem_title,
            "semester_num": r_sem,
            "academic_year": r_year,
            "total": int(r_total),
            "paid": int(r_paid),
            "outstanding": int(r_out),
            "status": r_status
        })

    # Payment History
    payment_history = []
    for r in all_fee_rows:
        if r["paid_amount"] and r["paid_amount"] > 0:
            p_date_raw = r["payment_date"] or r["created_at"]
            p_date_str = "18 Sep 2024"
            if p_date_raw:
                try:
                    if isinstance(p_date_raw, str):
                        p_d_obj = datetime.strptime(p_date_raw.split()[0], "%Y-%m-%d")
                    else:
                        p_d_obj = p_date_raw
                    p_date_str = p_d_obj.strftime("%d %b %Y")
                except Exception:
                    p_date_str = str(p_date_raw).split()[0]

            txn_receipt = r["transaction_id"] or f"R-{r['fee_id']:05d}"
            payment_history.append({
                "date": p_date_str,
                "desc": f"Semester {r['semester']} Fee ({r['academic_year']})",
                "amount": f"{int(r['paid_amount']):,}",
                "receipt": txn_receipt,
                "status": "Paid",
                "payment_method": r["payment_method"] or "Online"
            })

    # Available Semesters for filtering dropdown
    available_semesters = [
        {
            "semester": r["semester"],
            "academic_year": r["academic_year"],
            "label": f"Semester {r['semester']} ({r['academic_year']})"
        }
        for r in all_fee_rows
    ]

    return {
        "success": True,
        "student": {
            "student_id": student.student_id,
            "name": f"{student.first_name} {student.last_name}".strip(),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "roll_number": student.roll_number,
            "registration_number": student.registration_number,
            "program": student.program,
            "semester": student.semester,
            "section": student.section,
            "profile_photo": student.profile_photo,
            "isScholarshipHolder": is_scholarship
        },
        "currentSemester": current_sem_label,
        "totalFee": int(total_fee),
        "paidAmount": int(paid_amount),
        "outstandingAmount": int(outstanding_amount),
        "dueDate": due_date_str,
        "feeStatus": fee_status,
        "feeBreakdown": fee_breakdown,
        "scholarship": {
            "statusText": "Approved" if is_scholarship else "None",
            "subtext": f"Your scholarship has been approved for {current_sem_label}." if is_scholarship else "No active scholarship for this semester.",
            "type": "Merit Scholarship" if is_scholarship else "None",
            "amount": int(scholarship_amount),
            "adjustmentApplied": int(scholarship_amount),
            "statusBadge": "Active" if is_scholarship else "Inactive"
        },
        "semesterSummary": semester_summary,
        "paymentHistory": payment_history,
        "available_semesters": available_semesters
    }


# ==========================================================
# STUDENT LIBRARY
# ==========================================================

@router.get("/library")
def get_student_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get student's library profile, metrics (books issued, due, fines),
    recently added books, digital resources, issued book records, and library announcements.
    Data sources:
        Library
        Library_Issues
        Notifications
        Students
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )

    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.user_id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    # 1. Fetch Issued Books for this student
    issues_rows = db.execute(
        text("""
            SELECT
                i.issue_id,
                i.book_id,
                i.issue_date,
                i.due_date,
                i.return_date,
                i.fine_amount,
                i.issue_status,
                i.remarks,
                b.title,
                b.author,
                b.category
            FROM Library_Issues i
            JOIN Library b ON i.book_id = b.book_id
            WHERE i.student_id = :student_id
            ORDER BY i.due_date ASC
        """),
        {"student_id": student.student_id}
    ).mappings().all()

    issued_books_list = []
    books_issued_count = 0
    due_in_7_days = 0
    overdue_count = 0
    total_fines = 0.0

    now = datetime.now()

    for row in issues_rows:
        if row["issue_status"] in ("Issued", "Late"):
            books_issued_count += 1
            fine = float(row["fine_amount"] or 0.0)
            total_fines += fine

            issue_dt = row["issue_date"]
            due_dt = row["due_date"]
            issue_date_str = issue_dt.strftime("%d %b %Y") if isinstance(issue_dt, datetime) else str(issue_dt).split()[0]
            due_date_str = due_dt.strftime("%d %b %Y") if isinstance(due_dt, datetime) else str(due_dt).split()[0]

            days_remaining = None
            if isinstance(due_dt, datetime):
                days_remaining = (due_dt.date() - now.date()).days
            elif isinstance(due_dt, str):
                try:
                    d_parsed = datetime.strptime(due_dt.split()[0], "%Y-%m-%d")
                    days_remaining = (d_parsed.date() - now.date()).days
                except Exception:
                    pass

            if days_remaining is not None and days_remaining < 0:
                overdue_count += 1
                status_text = f"Overdue by {abs(days_remaining)} days"
                status_type = "overdue"
            elif days_remaining is not None and days_remaining <= 7:
                due_in_7_days += 1
                status_text = f"Due in {days_remaining} days"
                status_type = "due-soon"
            else:
                status_text = "Issued"
                status_type = "issued"

            issued_books_list.append({
                "id": row["issue_id"],
                "book_id": row["book_id"],
                "title": row["title"],
                "author": row["author"],
                "issueDate": issue_date_str,
                "dueDate": due_date_str,
                "status": status_text,
                "statusType": status_type,
                "fine": fine
            })

    # 2. Fetch Recently Added / Available Books
    books_rows = db.execute(
        text("""
            SELECT
                book_id,
                isbn,
                title,
                author,
                edition,
                category,
                status
            FROM Library
            ORDER BY book_id DESC
            LIMIT 10
        """)
    ).mappings().all()

    gradients = [
        "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        "linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)",
        "linear-gradient(135deg, #022c22 0%, #064e3b 100%)",
        "linear-gradient(135deg, #172554 0%, #1e40af 100%)",
        "linear-gradient(135deg, #451a03 0%, #78350f 100%)",
        "linear-gradient(135deg, #3b0764 0%, #581c87 100%)",
        "linear-gradient(135deg, #134e4a 0%, #042f2e 100%)"
    ]

    recent_books = []
    for idx, b in enumerate(books_rows):
        recent_books.append({
            "id": b["book_id"],
            "title": b["title"],
            "subtitle": b["edition"] or b["category"] or "Textbook",
            "author": b["author"],
            "badge": b["status"] or "Available",
            "bgGradient": gradients[idx % len(gradients)]
        })

    # 3. Digital Resources (Standard HEC Digital Library Portals)
    digital_resources = [
        {
            "id": "ieee",
            "name": "IEEE Xplore",
            "description": "Research papers, articles and conference proceedings",
            "url": "https://ieeexplore.ieee.org"
        },
        {
            "id": "springer",
            "name": "SpringerLink",
            "description": "Journals, books and research content",
            "url": "https://link.springer.com"
        },
        {
            "id": "sciencedirect",
            "name": "ScienceDirect",
            "description": "Full-text articles and academic journals",
            "url": "https://www.sciencedirect.com"
        },
        {
            "id": "proquest",
            "name": "ProQuest",
            "description": "Dissertations, theses and research databases",
            "url": "https://www.proquest.com"
        },
        {
            "id": "ebsco",
            "name": "EBSCOhost",
            "description": "E-journals, ebooks and academic content",
            "url": "https://www.ebsco.com"
        }
    ]

    # 4. Library Specific Announcements from Notifications table
    notif_rows = db.execute(
        text("""
            SELECT
                notification_id,
                title,
                message,
                created_at,
                sender,
                notification_type
            FROM Notifications
            WHERE sender LIKE '%Library%' OR message LIKE '%book%' OR message LIKE '%library%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
    ).mappings().all()

    announcements = []
    icon_map = {
        "Information": ("volume-2", "#eff6ff", "#2563eb"),
        "Reminder": ("book-open", "#fffbebfb", "#d97706"),
        "Warning": ("calendar", "#f0fdf4", "#16a34a"),
        "Success": ("check-circle", "#f0fdf4", "#16a34a")
    }

    for n in notif_rows:
        n_type = n["notification_type"] or "Information"
        icon_name, bg_col, col = icon_map.get(n_type, ("volume-2", "#eff6ff", "#2563eb"))
        c_dt = n["created_at"]
        date_str = c_dt.strftime("%d %b %Y") if isinstance(c_dt, datetime) else str(c_dt).split()[0]

        announcements.append({
            "id": n["notification_id"],
            "title": n["title"],
            "description": n["message"],
            "date": date_str,
            "icon": icon_name,
            "bg": bg_col,
            "color": col
        })

    if not announcements:
        announcements = [
            {
                "id": 1,
                "title": "New E-Books Added",
                "description": "50+ new computer science and engineering e-books added.",
                "date": now.strftime("%d %b %Y"),
                "icon": "volume-2",
                "bg": "#eff6ff",
                "color": "#2563eb"
            }
        ]

    return {
        "success": True,
        "student": {
            "student_id": student.student_id,
            "name": f"{student.first_name} {student.last_name}".strip(),
            "roll_number": student.roll_number,
            "program": student.program,
            "semester": student.semester,
            "profile_photo": student.profile_photo
        },
        "metrics": {
            "booksIssued": books_issued_count,
            "dueIn7Days": due_in_7_days,
            "overdue": overdue_count,
            "reservations": 0,
            "finePayable": f"PKR {int(total_fines)}"
        },
        "recentlyAddedBooks": recent_books,
        "digitalResources": digital_resources,
        "issuedBooks": issued_books_list,
        "announcements": announcements
    }


# ==========================================================
# STUDENT NOTICES & ANNOUNCEMENTS
# ==========================================================

# ==========================================================
# AI ACADEMIC ASSISTANT
# ==========================================================

@router.get("/ai/greeting", response_model=AIGreetingResponse)
def get_student_ai_greeting(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return dynamic, student-aware greeting for the authenticated student.
    """
    student = _current_student(current_user, db)
    greeting = f"Hello {student.first_name}! 👋 I am your AI Academic Assistant. How can I assist you with your courses, timetable, or exam preparations today?"
    return {
        "success": True,
        "greeting": greeting,
        "student_name": f"{student.first_name} {student.last_name}".strip(),
        "first_name": student.first_name
    }


@router.post("/ai/chat", response_model=AIChatResponse)
def chat_with_student_ai(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process natural language question for the authenticated student using real database context and AI reasoning.
    """
    student = _current_student(current_user, db)
    ai_response, provider = process_student_chat(
        student=student,
        db=db,
        user_message=payload.message,
        history=payload.history
    )
    return {
        "success": True,
        "response": ai_response,
        "provider": provider,
        "student_name": student.first_name
    }


# ==========================================================
# STUDENT FEE AI ASSISTANT
# ==========================================================

@router.get("/fee-ai/greeting", response_model=AIGreetingResponse)
def get_fee_ai_greeting(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = _current_student(current_user, db)
    return {
        "success": True,
        "greeting": f"Hello {student.first_name}! I can help with your fee record, payments, due dates, and verified university fee procedures.",
        "student_name": f"{student.first_name} {student.last_name}".strip(),
        "first_name": student.first_name,
    }


@router.post("/fee-ai/chat", response_model=FeeAIChatResponse)
def chat_with_fee_ai(
    payload: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Answer a fee question for only the JWT-authenticated student."""
    student = _current_student(current_user, db)
    response, provider, sources = process_fee_chat(
        student=student,
        db=db,
        user_message=payload.message,
        history=payload.history,
    )
    return {
        "success": True,
        "response": response,
        "provider": provider,
        "student_name": student.first_name,
        "sources": sources,
    }
