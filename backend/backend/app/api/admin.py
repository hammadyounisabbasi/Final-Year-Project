from datetime import datetime, timezone
import csv

from io import BytesIO
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import inspect

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.models.academic_term import AcademicTerm
from app.models.enrollment import Enrollment
from app.models.course_result import CourseResult
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.course import Course
from app.models.department import Department
from app.models.class_schedule import ClassSchedule
from app.models.student_timetable import StudentTimetable
from app.schemas.admin import AcademicTermStatusUpdate, AdminFacultyAIRequest, AdminFacultyUpdate, AdminIntegrityAIRequest, AdminStudentAIRequest, AdminStudentUpdate, TimetableScope, TimetableProposalRequest, TimetableApprovalRequest, TimetableChatRequest, TimetablePdfRequest, TimetableDraftSetupRequest, TimetableSessionEditRequest, CreateRoomRequest
from app.models.timetable import Room, TimetableConfiguration, Timetable, TimetableCourse, TimetableCourseRoom, TimetableSession
from app.services.academic_results import recalculate_student_completed_results
from app.services.timetable_creator import analyze as analyze_timetable, run_generation_workflow, run_chat_workflow, serialize_schedule, overlaps, validate_draft
from app.services.timetable_documents import extract_document_text, extract_reference_facts, build_timetable_pdf
from app.services.timetable_approval import attach_proposal, verify_proposal
from app.services.timetable_constraints import ConstraintSnapshot, FIELDS
from app.services.timetable_scheduler import generate_timetable
from app.services.timetable_validation import validate_timetable
from app.services.timetable_integrity import sync_student_timetable
from app.services.admin_student_management import get_student_detail, list_students, student_management_overview, update_student
from app.services.admin_student_ai import process_admin_student_chat
from app.services.admin_faculty_management import faculty_management_overview, get_faculty_detail, list_faculty, update_faculty
from app.services.admin_faculty_ai import process_admin_faculty_chat
from app.services.academic_integrity import overview as integrity_overview, list_submissions as integrity_submissions, submission_detail as integrity_submission_detail, list_warnings as integrity_warning_list, student_integrity, teacher_integrity
from app.services.academic_integrity_ai import process_admin_integrity_chat
from sqlalchemy import text as sql_text


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


def _require_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.get("/students/overview")
def admin_student_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **student_management_overview(db)}


@router.get("/students")
def admin_students(
    search: str = Query("", max_length=200),
    department_id: int | None = Query(None, gt=0),
    program: str = Query("", max_length=150),
    semester: int | None = Query(None, ge=1, le=20),
    section: str = Query("", max_length=20),
    student_status: str = Query("", max_length=30),
    sort_by: str = Query("name", pattern="^(name|roll_number|registration_number|program|semester|batch_year|status)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    return {"success": True, **list_students(
        db, search=search, department_id=department_id, program=program,
        semester=semester, section=section, student_status=student_status,
        sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size,
    )}


@router.get("/students/{student_id}")
def admin_student_detail(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **get_student_detail(db, student_id)}


@router.patch("/students/{student_id}")
def admin_student_update(payload: AdminStudentUpdate, student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, "student": update_student(db, student_id, payload.model_dump(exclude_unset=True))}


@router.post("/students/ai/chat")
def admin_student_ai_chat(payload: AdminStudentAIRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    response, provider = process_admin_student_chat(
        db, payload.message,
        [{"role": item.role, "content": item.content} for item in payload.history],
        payload.selected_student_id,
    )
    return {"success": True, "response": response, "provider": provider}


@router.get("/faculty/overview")
def admin_faculty_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **faculty_management_overview(db)}


@router.get("/faculty")
def admin_faculty(
    search: str = Query("", max_length=200),
    department_id: int | None = Query(None, gt=0),
    designation: str = Query("", max_length=150),
    employment_type: str = Query("", max_length=30),
    faculty_status: str = Query("", max_length=30),
    account_active: bool | None = Query(None),
    sort_by: str = Query("name", pattern="^(name|employee_id|department|designation|joining_date|status)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    return {"success": True, **list_faculty(
        db, search=search, department_id=department_id, designation=designation,
        employment_type=employment_type, faculty_status=faculty_status,
        account_active=account_active, sort_by=sort_by, sort_order=sort_order,
        page=page, page_size=page_size,
    )}


@router.get("/faculty/{teacher_id}")
def admin_faculty_detail(teacher_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **get_faculty_detail(db, teacher_id)}


@router.patch("/faculty/{teacher_id}")
def admin_faculty_update(payload: AdminFacultyUpdate, teacher_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, "faculty": update_faculty(db, teacher_id, payload.model_dump(exclude_unset=True))}


@router.post("/faculty/ai/chat")
def admin_faculty_ai_chat(payload: AdminFacultyAIRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    response, provider = process_admin_faculty_chat(
        db, payload.message,
        [{"role": item.role, "content": item.content} for item in payload.history],
        payload.selected_teacher_id,
    )
    return {"success": True, "response": response, "provider": provider}


@router.get("/academic-integrity/overview")
def admin_integrity_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **integrity_overview(db)}


@router.get("/academic-integrity/submissions")
def admin_integrity_submissions(
    search: str = Query("", max_length=200), department_id: int | None = Query(None, gt=0),
    course_id: int | None = Query(None, gt=0), teacher_id: int | None = Query(None, gt=0),
    semester: int | None = Query(None, ge=1, le=20), review_state: str = Query("", max_length=30),
    grading_status: str = Query("", pattern="^(|graded|ungraded)$"),
    min_similarity: float | None = Query(None, ge=0, le=100), max_similarity: float | None = Query(None, ge=0, le=100),
    sort_by: str = Query("submitted_at", pattern="^(submitted_at|similarity|student|course|assignment|marks)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=5, le=100),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _require_admin(current_user)
    return {"success": True, **integrity_submissions(db, search=search, department_id=department_id, course_id=course_id,
        teacher_id=teacher_id, semester=semester, review_state=review_state, grading_status=grading_status,
        min_similarity=min_similarity, max_similarity=max_similarity, sort_by=sort_by, sort_order=sort_order, page=page, page_size=page_size)}


@router.get("/academic-integrity/submissions/{submission_id}")
def admin_integrity_submission(submission_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **integrity_submission_detail(db, submission_id)}


@router.get("/academic-integrity/grading-warnings")
def admin_integrity_warnings(
    severity: str = Query("", max_length=40), code: str = Query("", max_length=80), student_id: int | None = Query(None, gt=0),
    teacher_id: int | None = Query(None, gt=0), course_id: int | None = Query(None, gt=0),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=5, le=100),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _require_admin(current_user)
    return {"success": True, **integrity_warning_list(db, severity=severity, code=code, student_id=student_id,
        teacher_id=teacher_id, course_id=course_id, page=page, page_size=page_size)}


@router.get("/academic-integrity/students/{student_id}")
def admin_integrity_student(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **student_integrity(db, student_id)}


@router.get("/academic-integrity/teachers/{teacher_id}")
def admin_integrity_teacher(teacher_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **teacher_integrity(db, teacher_id)}


@router.post("/academic-integrity/ai/chat")
def admin_integrity_ai_chat(payload: AdminIntegrityAIRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    response, provider, context = process_admin_integrity_chat(db, payload.message,
        [{"role": item.role, "content": item.content} for item in payload.history],
        selected_submission_id=payload.selected_submission_id, selected_student_id=payload.selected_student_id,
        selected_teacher_id=payload.selected_teacher_id)
    return {"success": True, "response": response, "provider": provider, "context": context}


@router.get("/academic-integrity/report.csv")
def admin_integrity_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    summary = integrity_overview(db)
    warnings = integrity_warning_list(db, page=1, page_size=max(summary["stats"]["data_warnings"], 1))["items"]
    output = BytesIO()
    rows = [["ACADEMIC INTEGRITY EVIDENCE REPORT"], ["Generated UTC", datetime.now(timezone.utc).isoformat()], [], ["Metric", "Value"]]
    rows.extend([[key.replace("_", " ").title(), value] for key, value in summary["stats"].items()])
    rows.extend([[], ["Warning Code", "Severity", "Student", "Roll Number", "Course", "Message"]])
    rows.extend([[row["code"], row["severity"], row.get("student_name") or "N/A", row.get("roll_number") or "N/A", row.get("course") or "N/A", row["message"]] for row in warnings])
    text_output = __import__("io").StringIO(newline="")
    csv.writer(text_output).writerows(rows)
    output.write(text_output.getvalue().encode("utf-8-sig")); output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=academic-integrity-evidence.csv"})


def _require_timetable_builder_schema(db: Session):
    required = {"Rooms", "Room_Availability", "Timetable_Configurations", "Timetables", "Timetable_Courses", "Timetable_Course_Rooms", "Timetable_Sessions"}
    available = set(inspect(db.bind).get_table_names())
    missing = sorted(required - available)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "The data-driven timetable migration must be applied first.", "missing_tables": missing},
        )


def _serialize_builder_draft(row: Timetable):
    return {
        "timetable_id": row.timetable_id,
        "department_id": row.department_id,
        "department": row.department.department_name,
        "term_id": row.term_id,
        "academic_year": row.term.academic_year,
        "semester": row.semester,
        "section": row.section,
        "status": row.status,
        "configuration": {
            "working_days": row.configuration.working_day_list,
            "day_start_time": row.configuration.day_start_time,
            "day_end_time": row.configuration.day_end_time,
            "slot_minutes": row.configuration.slot_minutes,
        },
        "courses": [{
            "timetable_course_id": item.timetable_course_id,
            "course_id": item.course_id,
            "course_code": item.course.course_code,
            "course_title": item.course.course_title,
            "credit_hours": item.course.credit_hours,
            "teacher_id": item.teacher_id,
            "teacher": f"{item.teacher.first_name} {item.teacher.last_name}".strip(),
            "weekly_sessions": item.weekly_sessions,
            "session_duration_minutes": item.session_duration_minutes,
            "class_type": item.class_type,
            "required_room_type": item.required_room_type,
            "room_ids": [choice.room_id for choice in item.eligible_rooms],
            "sessions": [{
                "session_id": session.timetable_session_id,
                "day": session.day_of_week,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "room_id": session.room_id,
                "room": session.room.room_code,
                "legacy_schedule_id": session.legacy_schedule_id,
            } for session in sorted(item.sessions, key=lambda value: (value.day_of_week, value.start_time))],
        } for item in row.courses],
    }


def _builder_draft(db, timetable_id):
    row = db.get(Timetable, timetable_id)
    if row is None:
        raise HTTPException(404, "Timetable draft not found")
    return row


@router.get("/timetable-builder/options")
def timetable_builder_options(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return source-of-truth choices for the structured Admin setup wizard."""
    _require_admin(current_user)
    _require_timetable_builder_schema(db)
    default = db.query(TimetableConfiguration).filter_by(status="Active").order_by(TimetableConfiguration.configuration_id).first()
    years = {value for (value,) in db.query(Enrollment.academic_year).distinct().all() if value}
    years.update(value for (value,) in db.query(AcademicTerm.academic_year).distinct().all() if value)
    return {
        "departments": [{"id": row.department_id, "name": row.department_name} for row in db.query(Department).filter_by(status="Active").order_by(Department.department_name)],
        "courses": [{"id": row.course_id, "department_id": row.department_id, "semester": row.semester, "code": row.course_code, "title": row.course_title, "credit_hours": row.credit_hours, "course_type": row.course_type, "assigned_teacher_id": row.teacher_id} for row in db.query(Course).filter_by(status="Active").order_by(Course.semester, Course.course_code)],
        "teachers": [{"id": row.teacher_id, "department_id": row.department_id, "name": f"{row.first_name} {row.last_name}".strip(), "specialization": row.specialization} for row in db.query(Teacher).filter_by(status="Active").order_by(Teacher.first_name, Teacher.last_name)],
        "rooms": [{"id": row.room_id, "code": row.room_code, "name": row.room_name, "room_type": row.room_type, "capacity": row.capacity} for row in db.query(Room).filter_by(status="Active").order_by(Room.room_code)],
        "academic_years": sorted(years, reverse=True),
        "semesters": sorted({value for (value,) in db.query(Course.semester).filter(Course.status == "Active").distinct().all()}),
        "defaults": {
            "working_days": default.working_day_list if default else ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "day_start_time": default.day_start_time if default else "08:30",
            "day_end_time": default.day_end_time if default else "15:30",
            "slot_minutes": default.slot_minutes if default else 60,
        },
    }


@router.post("/timetable-builder/rooms", status_code=status.HTTP_201_CREATED)
def create_timetable_builder_room(payload: CreateRoomRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new room in the database for timetable scheduling."""
    _require_admin(current_user)
    _require_timetable_builder_schema(db)
    clean_code = payload.room_code.strip().upper()
    existing = db.query(Room).filter(Room.room_code.ilike(clean_code)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Room with code '{clean_code}' already exists.")
    
    room = Room(
        room_code=clean_code,
        room_name=payload.room_name.strip() if payload.room_name else clean_code,
        room_type=payload.room_type,
        capacity=payload.capacity,
        status="Active"
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return {
        "success": True,
        "message": f"Room {room.room_code} created successfully.",
        "room": {
            "id": room.room_id,
            "code": room.room_code,
            "name": room.room_name,
            "room_type": room.room_type,
            "capacity": room.capacity
        }
    }


@router.post("/timetable-builder/drafts", status_code=status.HTTP_201_CREATED)
def create_timetable_builder_drafts(payload: TimetableDraftSetupRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Persist reviewed setup data as drafts; generation/publishing are separate."""
    _require_admin(current_user)
    _require_timetable_builder_schema(db)
    department = db.get(Department, payload.department_id)
    if department is None or department.status != "Active":
        raise HTTPException(422, "Select an active department")
    course_ids = {item.course_id for semester in payload.semesters for item in semester.courses}
    teacher_ids = {item.teacher_id for semester in payload.semesters for item in semester.courses}
    meeting_teacher_ids = {m.teacher_id for semester in payload.semesters for item in semester.courses for m in (item.meetings or []) if m.teacher_id}
    teacher_ids.update(meeting_teacher_ids)
    room_ids = {room_id for semester in payload.semesters for item in semester.courses for room_id in item.room_ids}
    meeting_room_ids = {m.room_id for semester in payload.semesters for item in semester.courses for m in (item.meetings or []) if m.room_id}
    room_ids.update(meeting_room_ids)
    courses = {row.course_id: row for row in db.query(Course).filter(Course.course_id.in_(course_ids)).all()}
    teachers = {row.teacher_id: row for row in db.query(Teacher).filter(Teacher.teacher_id.in_(teacher_ids)).all()}
    rooms = {row.room_id: row for row in db.query(Room).filter(Room.room_id.in_(room_ids)).all()}
    errors = []
    for semester in payload.semesters:
        for setup in semester.courses:
            course, teacher = courses.get(setup.course_id), teachers.get(setup.teacher_id)
            if course is None or course.status != "Active" or course.department_id != payload.department_id or course.semester != semester.semester:
                errors.append(f"Course {setup.course_id} is not active in the selected department and semester.")
            elif course.credit_hours != setup.credit_hours:
                errors.append(f"{course.course_code} credit hours changed; reload the setup data.")
            if teacher is None or teacher.status != "Active":
                errors.append(f"Teacher {setup.teacher_id} is not active.")
            selected_rooms = [rooms.get(room_id) for room_id in setup.room_ids]
            if any(room is None or room.status != "Active" for room in selected_rooms):
                errors.append(f"One or more rooms for course {setup.course_id} are unavailable.")
            elif not any(room.room_type == setup.required_room_type for room in selected_rooms):
                errors.append(f"Course {setup.course_id} needs at least one eligible {setup.required_room_type}.")
    if errors:
        raise HTTPException(422, {"message": "Setup validation failed", "errors": list(dict.fromkeys(errors))})

    configuration = TimetableConfiguration(
        name=f"Draft setup {current_user.user_id} {datetime.utcnow().isoformat(timespec='microseconds')}",
        working_days=",".join(payload.working_days),
        day_start_time=payload.day_start_time,
        day_end_time=payload.day_end_time,
        slot_minutes=payload.slot_minutes,
    )
    db.add(configuration)
    created = []
    try:
        db.flush()
        for semester in payload.semesters:
            term = db.query(AcademicTerm).filter_by(academic_year=payload.academic_year.strip(), semester=semester.semester).first()
            if term is None:
                term = AcademicTerm(academic_year=payload.academic_year.strip(), semester=semester.semester, term_name=f"Semester {semester.semester}")
                db.add(term)
                db.flush()
            duplicate = db.query(Timetable).filter_by(department_id=payload.department_id, term_id=term.term_id, semester=semester.semester, section=semester.section.strip()).first()
            if duplicate:
                raise HTTPException(409, f"A {duplicate.status.lower()} timetable already exists for Semester {semester.semester}, Section {semester.section.strip()}.")
            timetable = Timetable(department_id=payload.department_id, term_id=term.term_id, configuration_id=configuration.configuration_id, semester=semester.semester, section=semester.section.strip(), created_by=current_user.user_id)
            db.add(timetable)
            db.flush()
            for setup in semester.courses:
                item = TimetableCourse(timetable_id=timetable.timetable_id, course_id=setup.course_id, teacher_id=setup.teacher_id, weekly_sessions=setup.weekly_sessions, session_duration_minutes=setup.session_duration_minutes, class_type=setup.class_type, required_room_type=setup.required_room_type)
                db.add(item)
                db.flush()
                for room_id in sorted(set(setup.room_ids)):
                    db.add(TimetableCourseRoom(timetable_course_id=item.timetable_course_id, room_id=room_id))
                
                # If explicit meetings were supplied with full details (day, start, end, room), populate them
                if setup.meetings:
                    for m in setup.meetings:
                        if m.day and m.start_time and m.end_time and m.room_id:
                            meeting_room = rooms.get(m.room_id)
                            if meeting_room:
                                db.add(TimetableSession(
                                    timetable_course_id=item.timetable_course_id,
                                    room_id=m.room_id,
                                    day_of_week=m.day,
                                    start_time=m.start_time,
                                    end_time=m.end_time
                                ))
            created.append(timetable)
        db.commit()
        for timetable in created:
            db.refresh(timetable)
        return {"success": True, "message": f"Created {len(created)} timetable draft(s).", "drafts": [_serialize_builder_draft(row) for row in created]}
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "The timetable setup conflicts with an existing draft. Reload and try again.") from error


@router.get("/timetable-builder/drafts/{timetable_id}")
def get_timetable_builder_draft(timetable_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    row = _builder_draft(db, timetable_id)
    return {"success": True, "draft": _serialize_builder_draft(row), "validation": validate_timetable(db, row) if row.courses and any(item.sessions for item in row.courses) else []}


@router.post("/timetable-builder/drafts/{timetable_id}/generate")
def generate_timetable_builder_draft(timetable_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    row = _builder_draft(db, timetable_id)
    result = generate_timetable(db, row)
    if not result["success"]:
        return {**result, "draft": _serialize_builder_draft(row)}
    return {**result, "draft": _serialize_builder_draft(row), "validation": validate_timetable(db, row)}


@router.post("/timetable-builder/drafts/{timetable_id}/validate")
def validate_timetable_builder_draft(timetable_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    row = _builder_draft(db, timetable_id)
    issues = validate_timetable(db, row)
    return {"success": not issues, "issues": issues, "draft": _serialize_builder_draft(row)}


@router.patch("/timetable-builder/sessions/{session_id}")
def edit_timetable_builder_session(session_id: int, payload: TimetableSessionEditRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    session = db.get(TimetableSession, session_id)
    if session is None:
        raise HTTPException(404, "Timetable session not found")
    timetable = session.timetable_course.timetable
    if timetable.status != "Draft":
        raise HTTPException(409, "Only draft sessions can be edited")
    previous = (session.day_of_week, session.start_time, session.end_time, session.room_id, session.timetable_course.teacher_id)
    session.day_of_week, session.start_time, session.end_time, session.room_id = payload.day_of_week, payload.start_time, payload.end_time, payload.room_id
    if payload.teacher_id is not None:
        teacher = db.get(Teacher, payload.teacher_id)
        if teacher is None or teacher.status != "Active":
            db.rollback()
            raise HTTPException(422, "Select an active teacher")
        session.timetable_course.teacher_id = payload.teacher_id
    try:
        db.flush()
        issues = validate_timetable(db, timetable)
        if issues:
            db.rollback()
            raise HTTPException(409, {"message": "The edit creates timetable conflicts; the previous session was preserved.", "issues": issues})
        db.commit()
        db.refresh(timetable)
        return {"success": True, "message": "Session updated and revalidated.", "draft": _serialize_builder_draft(timetable), "validation": []}
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        raise HTTPException(409, "The edit could not be saved; the previous session was preserved.") from error


@router.post("/timetable-builder/drafts/{timetable_id}/approve")
def approve_timetable_builder_draft(timetable_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    row = _builder_draft(db, timetable_id)
    if row.status != "Draft":
        raise HTTPException(409, "Only a draft can be approved")
    if not row.courses or not any(item.sessions for item in row.courses):
        raise HTTPException(409, "Generate the timetable before approval")
    issues = validate_timetable(db, row)
    if issues:
        raise HTTPException(409, {"message": "Resolve validation conflicts before approval.", "issues": issues})
    row.status = "Approved"
    row.approved_by = current_user.user_id
    row.approved_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": "Timetable approved. It is not visible in portals until published.", "draft": _serialize_builder_draft(row)}


@router.post("/timetable-builder/drafts/{timetable_id}/publish")
def publish_timetable_builder_draft(timetable_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    row = _builder_draft(db, timetable_id)
    if row.status != "Approved":
        raise HTTPException(409, "Approve the timetable before publishing")
    issues = validate_timetable(db, row)
    if issues:
        raise HTTPException(409, {"message": "The approved timetable is no longer valid; return it to draft and regenerate.", "issues": issues})
    course_ids = [item.course_id for item in row.courses]
    replaced = db.query(ClassSchedule).filter(
        ClassSchedule.course_id.in_(course_ids), ClassSchedule.academic_year == row.term.academic_year,
        ClassSchedule.semester == row.semester, ClassSchedule.section == row.section,
        ClassSchedule.status == "Active",
    ).all()
    for old in replaced:
        old.status = "Cancelled"
    try:
        db.flush()
        for item in row.courses:
            for session in item.sessions:
                legacy = ClassSchedule(course_id=item.course_id, teacher_id=item.teacher_id, academic_year=row.term.academic_year, semester=row.semester, section=row.section, day_of_week=session.day_of_week, start_time=session.start_time, end_time=session.end_time, room_location=session.room.room_code, class_type=item.class_type, status="Active")
                db.add(legacy)
                db.flush()
                sync_student_timetable(db, legacy)
                session.legacy_schedule_id = legacy.schedule_id
        row.status = "Published"
        row.published_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
    except Exception as error:
        db.rollback()
        raise HTTPException(409, "Publication failed and all changes were rolled back. Revalidate the timetable.") from error
    return {"success": True, "message": "Timetable published to Student and Teacher portals.", "replaced_legacy_entries": len(replaced), "draft": _serialize_builder_draft(row)}


@router.get("/timetable-creator/options")
def timetable_creator_options(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dynamic filter values; no department, staff, or student names are hard-coded."""
    _require_admin(current_user)
    return {
        "departments": [{"id": d.department_id, "name": d.department_name} for d in db.query(Department).order_by(Department.department_name)],
        "teachers": [{"id": t.teacher_id, "name": f"{t.first_name} {t.last_name}", "department_id": t.department_id} for t in db.query(Teacher).filter(Teacher.status == "Active").order_by(Teacher.first_name)],
        "students": [{"id": s.student_id, "name": f"{s.first_name} {s.last_name}", "department_id": s.department_id, "semester": s.semester, "section": s.section} for s in db.query(Student).filter(Student.status == "Active").order_by(Student.first_name)],
        "semesters": [row[0] for row in db.query(Student.semester).filter(Student.status == "Active").distinct().order_by(Student.semester)],
        "sections": [row[0] for row in db.query(Student.section).filter(Student.status == "Active", Student.section.isnot(None)).distinct().order_by(Student.section)],
        "academic_years": [row[0] for row in db.query(Enrollment.academic_year).distinct().order_by(Enrollment.academic_year.desc())],
    }


@router.post("/timetable-creator/analyze")
def timetable_creator_analyze(payload: TimetableScope, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return {"success": True, **analyze_timetable(db, payload.model_dump())}


@router.post("/timetable-creator/generate")
def timetable_creator_generate(payload: TimetableProposalRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    # LangGraph extracts typed requirements and produces a validated read-only draft.
    values = payload.model_dump()
    return attach_proposal({"success": True, "mode": payload.mode, **run_generation_workflow(
        db,
        values,
        payload.prompt or "",
        values.get("history"),
        values.get("document_name") or "",
        values.get("document_text") or "",
    )}, db, current_user)


@router.post("/timetable-creator/chat")
def timetable_creator_chat(payload: TimetableChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    return attach_proposal({"success": True, **run_chat_workflow(db, payload.model_dump(), payload.message)}, db, current_user)


@router.post("/timetable-creator/document")
async def timetable_creator_document(
    document: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Extract optional admin-provided course/teacher notes without persisting them."""
    _require_admin(current_user)
    filename = (document.filename or "").replace('\\', '/').split('/')[-1].strip()
    if not filename.lower().endswith((".pdf", ".txt", ".docx", ".csv", ".xlsx", ".png", ".jpg", ".jpeg", ".webp")):
        raise HTTPException(status_code=422, detail="Use PDF, DOCX, TXT, CSV, XLSX, PNG, JPEG, or WebP references")
    content = await document.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Timetable reference exceeds the 5 MB limit")
    try:
        text = await run_in_threadpool(extract_document_text, filename, content)
    except Exception as error:
        raise HTTPException(status_code=422, detail=f"Could not extract readable content from {filename}. Upload a clearer file or provide the details manually.") from error
    if len(text) > 20000:
        raise HTTPException(422, 'Reference exceeds 20,000 extracted characters. Upload a shorter relevant excerpt for review.')
    if not text.strip():
        raise HTTPException(422, f'Could not extract readable content from {filename}. Upload a clearer file or provide the details manually.')
    from app.services.timetable_conversation import parse_input
    return {"success": True, "document_name": filename, "text": text, "characters": len(text), "facts": parse_input(text), "needs_review": False, "warning": None}


@router.post("/timetable-creator/approve")
def timetable_creator_approve(payload: TimetableApprovalRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    created = []
    try:
        # Serialize validation + persistence against other SQLite writers.
        db.rollback()
        db.execute(sql_text("BEGIN IMMEDIATE"))
        verify_proposal(payload.proposal_token, payload.changes, db, current_user)
        snapshot = ConstraintSnapshot(db)
        errors = snapshot.validate(payload.changes) + snapshot.validate_coverage(payload.changes)
        if errors:
            raise HTTPException(409, {"message":"Proposal is no longer valid", "errors":errors})
        for change in payload.changes:
            if change['action'] == 'update':
                old = db.get(ClassSchedule,change['schedule_id'])
                old.status = 'Cancelled'
        db.flush()
        for change in payload.changes:
            candidate = ClassSchedule(**{key:change[key] for key in FIELDS}, status='Active')
            db.add(candidate)
            db.flush()
            # Explicit links also cover a capability-matched alternate teacher;
            # the schedule teacher is authoritative for this scheduled class.
            enrollments = db.query(Enrollment).filter_by(course_id=candidate.course_id,
                academic_year=candidate.academic_year,semester=candidate.semester,
                section=candidate.section,enrollment_status='Enrolled').all()
            for enrollment in enrollments:
                if not db.query(StudentTimetable).filter_by(enrollment_id=enrollment.enrollment_id,schedule_id=candidate.schedule_id).first():
                    db.add(StudentTimetable(student_id=enrollment.student_id,enrollment_id=enrollment.enrollment_id,schedule_id=candidate.schedule_id))
            db.flush()
            created.append(serialize_schedule(candidate))
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except OperationalError as error:
        db.rollback()
        import logging
        code = getattr(error.orig, 'sqlite_errorcode', 0) & 0xff
        if code in (5, 6):
            logging.getLogger(__name__).warning('Timetable publication deferred: another database writer is active')
            raise HTTPException(409, 'Another update is in progress. Refresh the preview and retry approval.') from error
        logging.getLogger(__name__).exception('Timetable database operation failed')
        raise HTTPException(503, 'Database temporarily unavailable; no timetable changes were saved') from error
    except Exception as error:
        db.rollback()
        import logging
        logging.getLogger(__name__).exception('Approved timetable transaction failed')
        raise HTTPException(409,'Unable to save the approved proposal; all changes rolled back') from error
    return {"success":True,"message":f"Approved and saved {len(created)} timetable entries.","created":created}


@router.post("/timetable-creator/pdf")
def timetable_creator_pdf(payload: TimetablePdfRequest, current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    if not payload.schedules:
        raise HTTPException(422,'No timetable rows to export')
    output = build_timetable_pdf(payload.schedules)
    return StreamingResponse(output,media_type='application/pdf',headers={'Content-Disposition':'attachment; filename=timetable-preview.pdf'})


@router.put("/academic-terms/status")
def set_academic_term_status(
    payload: AcademicTermStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registrar-only publication control; completion recalculates affected CGPAs."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    term = db.query(AcademicTerm).filter(
        AcademicTerm.academic_year == payload.academic_year.strip(),
        AcademicTerm.semester == payload.semester,
    ).first()
    if term is None:
        term = AcademicTerm(academic_year=payload.academic_year.strip(), semester=payload.semester)
        db.add(term)
    if payload.status == "Completed":
        enrollment_count = db.query(Enrollment).filter(
            Enrollment.academic_year == payload.academic_year.strip(),
            Enrollment.semester == payload.semester,
            Enrollment.enrollment_status == "Enrolled",
        ).count()
        final_result_count = db.query(CourseResult).join(Enrollment).filter(
            Enrollment.academic_year == payload.academic_year.strip(),
            Enrollment.semester == payload.semester,
            CourseResult.published.is_(True),
        ).count()
        if enrollment_count and final_result_count < enrollment_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot complete a term until every enrolled course has a published final result",
            )
    term.status = payload.status
    term.completed_at = datetime.utcnow() if payload.status == "Completed" else None
    db.flush()
    affected_students = db.query(Student).join(Enrollment).filter(
        Enrollment.academic_year == term.academic_year,
        Enrollment.semester == term.semester,
    ).distinct().all()
    for affected_student in affected_students:
        recalculate_student_completed_results(db, affected_student.student_id)
    db.commit()
    return {"success": True, "academic_year": term.academic_year, "semester": term.semester,
            "status": term.status, "affected_students": len(affected_students)}


@router.get("/profile")
def get_admin_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Find admin profile
    admin = (
        db.query(Admin)
        .filter(
            Admin.user_id == current_user.user_id
        )
        .first()
    )

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin profile not found"
        )

    return {
        "admin_id": admin.admin_id,
        "user_id": admin.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": admin.first_name,
        "last_name": admin.last_name,
        "designation": admin.designation,
        "phone": admin.phone,
        "office_email": admin.office_email,
        "profile_photo": admin.profile_photo,
        "status": admin.status
    }
