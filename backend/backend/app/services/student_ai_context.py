from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, or_

from app.models.student import Student
from app.models.course import Course
from app.models.teacher import Teacher
from app.models.enrollment import Enrollment
from app.models.attendance import Attendance
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.student_cgpa import StudentCGPA
from app.models.semester_gpa import SemesterGPA
from app.models.course_result import CourseResult
from app.models.class_schedule import ClassSchedule
from app.models.student_timetable import StudentTimetable
from app.models.exam import Assessment, AssessmentAttempt


def get_student_identity_context(student: Student, db: Session) -> Dict[str, Any]:
    """Basic profile and cohort information."""
    return {
        "student_id": student.student_id,
        "name": f"{student.first_name} {student.last_name}".strip(),
        "first_name": student.first_name,
        "last_name": student.last_name,
        "roll_number": student.roll_number,
        "registration_number": student.registration_number,
        "program": student.program,
        "current_semester": student.semester,
        "section": student.section or "A",
        "batch_year": student.batch_year,
        "status": student.status,
    }


def get_cgpa_and_results_context(student: Student, db: Session) -> Dict[str, Any]:
    """CGPA, Semester GPAs, and completed course grades."""
    cgpa_record = (
        db.query(StudentCGPA)
        .filter(StudentCGPA.student_id == student.student_id)
        .first()
    )

    overall_cgpa = float(cgpa_record.overall_cgpa) if cgpa_record and cgpa_record.overall_cgpa is not None else 0.0
    completed_credits = cgpa_record.total_completed_credit_hours if cgpa_record else 0
    academic_status = cgpa_record.academic_status if cgpa_record else ("Good Standing" if overall_cgpa >= 2.0 else "In Progress")

    # Semester GPAs
    gpa_rows = (
        db.query(SemesterGPA)
        .filter(SemesterGPA.student_id == student.student_id)
        .order_by(SemesterGPA.semester.asc())
        .all()
    )
    semester_gpas = [
        {
            "semester": r.semester,
            "academic_year": r.academic_year,
            "gpa": float(r.semester_gpa or 0.0),
            "earned_credits": r.earned_credit_hours or 0,
            "status": r.academic_status
        }
        for r in gpa_rows
    ]

    # Completed Course Results
    results = (
        db.query(CourseResult)
        .filter(CourseResult.student_id == student.student_id)
        .order_by(CourseResult.semester.asc(), CourseResult.course_id.asc())
        .all()
    )

    course_results = []
    weak_courses = []
    strong_courses = []

    for r in results:
        course = r.course
        grade_pts = float(r.grade_points or 0.0)
        entry = {
            "semester": r.semester,
            "academic_year": r.academic_year,
            "course_code": course.course_code if course else "",
            "course_title": course.course_title if course else "",
            "credit_hours": r.credit_hours,
            "total_marks": float(r.total_marks or 0.0),
            "letter_grade": r.letter_grade or "N/A",
            "grade_points": grade_pts,
            "status": r.result_status
        }
        course_results.append(entry)

        if grade_pts < 2.5 or (r.letter_grade and r.letter_grade in ["C", "C-", "D+", "D", "F"]):
            weak_courses.append(entry)
        elif grade_pts >= 3.3 or (r.letter_grade and r.letter_grade in ["A", "A-", "B+"]):
            strong_courses.append(entry)

    return {
        "overall_cgpa": round(overall_cgpa, 2),
        "total_completed_credits": completed_credits,
        "academic_status": academic_status,
        "semester_gpas": semester_gpas,
        "completed_course_results": course_results,
        "weak_subjects": weak_courses,
        "strong_subjects": strong_courses,
    }


def get_current_courses_context(student: Student, db: Session) -> Dict[str, Any]:
    """Currently enrolled courses and their teachers for the student's active semester."""
    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student.student_id,
            Enrollment.semester == student.semester,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"])
        )
        .all()
    )

    courses = []
    total_credit_hours = 0
    for e in enrollments:
        c = e.course
        if not c:
            continue
        t = c.teacher
        teacher_name = f"{t.designation} {t.first_name} {t.last_name}".strip() if t else "Faculty Assigned"
        teacher_email = t.office_email if t and t.office_email else "N/A"
        office_room = f"Room {t.office_room}" if t and t.office_room else "N/A"

        total_credit_hours += c.credit_hours or 0
        courses.append({
            "course_id": c.course_id,
            "course_code": c.course_code,
            "course_title": c.course_title,
            "credit_hours": c.credit_hours,
            "course_type": c.course_type or "Core",
            "section": e.section,
            "academic_year": e.academic_year,
            "teacher": teacher_name,
            "teacher_email": teacher_email,
            "office_room": office_room,
        })

    return {
        "current_semester": student.semester,
        "total_enrolled_courses": len(courses),
        "total_credits": total_credit_hours,
        "courses": courses,
    }


def get_timetable_context(student: Student, db: Session, target_day: Optional[str] = None) -> Dict[str, Any]:
    """Class schedules, today's schedule, and next class for the student."""
    today_name = target_day or datetime.now().strftime("%A")

    # Fetch canonical timetable rows
    schedules = (
        db.query(ClassSchedule)
        .join(StudentTimetable, StudentTimetable.schedule_id == ClassSchedule.schedule_id)
        .join(Enrollment, Enrollment.enrollment_id == StudentTimetable.enrollment_id)
        .join(Course, Course.course_id == ClassSchedule.course_id)
        .filter(
            StudentTimetable.student_id == student.student_id,
            Enrollment.semester == student.semester,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
            ClassSchedule.status == "Active"
        )
        .all()
    )

    day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    schedules.sort(key=lambda s: (day_order.get(s.day_of_week, 99), s.start_time))

    def format_time(t_str: str) -> str:
        try:
            return datetime.strptime(t_str, "%H:%M").strftime("%I:%M %p").lstrip("0")
        except Exception:
            return t_str

    all_classes = []
    today_classes = []

    for s in schedules:
        c = s.course
        t = s.teacher
        teacher_name = f"{t.designation} {t.first_name} {t.last_name}".strip() if t else "Faculty Assigned"
        entry = {
            "day": s.day_of_week,
            "start_time": format_time(s.start_time),
            "end_time": format_time(s.end_time),
            "course_code": c.course_code if c else "",
            "course_title": c.course_title if c else "",
            "room": s.room_location,
            "teacher": teacher_name,
            "class_type": s.class_type,
        }
        all_classes.append(entry)
        if s.day_of_week.lower() == today_name.lower():
            today_classes.append(entry)

    next_class = today_classes[0] if today_classes else (all_classes[0] if all_classes else None)

    return {
        "today_day": today_name,
        "today_classes": today_classes,
        "today_classes_count": len(today_classes),
        "next_class": next_class,
        "weekly_schedule": all_classes,
        "total_weekly_classes": len(all_classes),
    }


def get_attendance_context(student: Student, db: Session) -> Dict[str, Any]:
    """Attendance statistics, percentages, and course breakdown."""
    records = (
        db.query(Attendance)
        .filter(Attendance.student_id == student.student_id)
        .all()
    )

    if not records:
        return {
            "has_records": False,
            "message": "No attendance records recorded yet for this student.",
            "overall_percentage": 0.0,
            "total_classes": 0,
            "courses_attendance": []
        }

    course_stats: Dict[int, Dict[str, Any]] = {}
    total_present = 0
    total_late = 0
    total_absent = 0
    total_leave = 0

    for r in records:
        cid = r.course_id
        if cid not in course_stats:
            c = r.course
            t = r.teacher
            teacher_name = f"{t.first_name} {t.last_name}".strip() if t else "Faculty"
            course_stats[cid] = {
                "course_code": c.course_code if c else "",
                "course_title": c.course_title if c else "",
                "teacher": teacher_name,
                "total_classes": 0,
                "present": 0,
                "late": 0,
                "absent": 0,
                "leave": 0,
            }

        st = course_stats[cid]
        st["total_classes"] += 1

        if r.status == "Present":
            st["present"] += 1
            total_present += 1
        elif r.status == "Late":
            st["late"] += 1
            total_late += 1
        elif r.status == "Absent":
            st["absent"] += 1
            total_absent += 1
        elif r.status == "Leave":
            st["leave"] += 1
            total_leave += 1

    courses_list = []
    for cid, st in course_stats.items():
        attended = st["present"] + st["late"]
        pct = round((attended / st["total_classes"] * 100), 1) if st["total_classes"] > 0 else 0.0
        st["attended"] = attended
        st["percentage"] = pct
        courses_list.append(st)

    courses_list.sort(key=lambda x: x["percentage"])
    total_classes = len(records)
    total_attended = total_present + total_late
    overall_pct = round((total_attended / total_classes * 100), 1) if total_classes > 0 else 0.0

    low_attendance_courses = [c for c in courses_list if c["percentage"] < 75.0]

    return {
        "has_records": True,
        "total_classes": total_classes,
        "total_attended": total_attended,
        "total_absent": total_absent,
        "total_late": total_late,
        "total_leave": total_leave,
        "overall_percentage": overall_pct,
        "courses_attendance": courses_list,
        "lowest_attendance_course": courses_list[0] if courses_list else None,
        "low_attendance_warnings": low_attendance_courses,
    }


def get_assignments_context(student: Student, db: Session) -> Dict[str, Any]:
    """Pending and submitted assignments with marks, deadlines, and submission status."""
    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student.student_id,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"])
        )
        .all()
    )
    enrolled_course_ids = [e.course_id for e in enrollments]

    if not enrolled_course_ids:
        return {
            "total_assignments": 0,
            "pending_count": 0,
            "submitted_count": 0,
            "missed_count": 0,
            "pending_assignments": [],
            "submitted_assignments": [],
            "missed_assignments": [],
        }

    assignments = (
        db.query(Assignment)
        .filter(
            Assignment.course_id.in_(enrolled_course_ids),
            Assignment.status == "Published"
        )
        .order_by(Assignment.due_date.asc())
        .all()
    )

    now = datetime.utcnow()
    pending = []
    submitted = []
    missed = []

    for assignment in assignments:
        sub = (
            db.query(Submission)
            .filter(
                Submission.assignment_id == assignment.assignment_id,
                Submission.student_id == student.student_id
            )
            .order_by(Submission.submission_attempt.desc())
            .first()
        )

        c = assignment.course
        due_str = assignment.due_date.strftime("%Y-%m-%d %I:%M %p") if assignment.due_date else "No due date"
        is_past_due = assignment.due_date and (now > assignment.due_date)

        item = {
            "assignment_id": assignment.assignment_id,
            "title": assignment.title,
            "description": assignment.description or "",
            "course_code": c.course_code if c else "",
            "course_title": c.course_title if c else "",
            "total_marks": assignment.total_marks,
            "due_date": due_str,
            "is_past_due": is_past_due,
            "submission_status": sub.submission_status if sub else "Not Submitted",
            "teacher_marks": sub.teacher_marks if sub and sub.teacher_marks is not None else None,
            "teacher_feedback": sub.teacher_feedback if sub and sub.teacher_feedback else None,
        }

        if sub:
            submitted.append(item)
        elif is_past_due:
            missed.append(item)
        else:
            pending.append(item)

    return {
        "total_assignments": len(assignments),
        "pending_count": len(pending),
        "submitted_count": len(submitted),
        "missed_count": len(missed),
        "pending_assignments": pending,
        "submitted_assignments": submitted,
        "missed_assignments": missed,
    }


def get_fee_status_context(student: Student, db: Session) -> Dict[str, Any]:
    """Fee status, dues, payments, and receipt history."""
    def date_string(value) -> Optional[str]:
        if value in (None, ""):
            return None
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value).split()[0]

    try:
        fee_rows = db.execute(
            text(
                """
                SELECT 
                    fee_id,
                    student_id,
                    semester,
                    academic_year,
                    total_fee,
                    paid_amount,
                    scholarship_amount,
                    payable_amount,
                    remaining_amount,
                    payment_status,
                    due_date,
                    payment_date,
                    payment_method,
                    transaction_id,
                    verified,
                    fine_amount,
                    discount_amount,
                    remarks
                FROM Fee_Records
                WHERE student_id = :student_id
                ORDER BY semester DESC
                """
            ),
            {"student_id": student.student_id},
        ).mappings().all()
    except Exception:
        # Older development databases may not have the fee table yet.  Missing
        # records are represented as missing; never manufacture a balance.
        fee_rows = []

    if not fee_rows:
        return {
            "has_fee_records": False,
            "current_semester": student.semester,
            "payment_status": None,
            "fee_status": None,
            "total_fee": None,
            "paid_amount": None,
            "remaining_amount": None,
            "due_date": None,
            "remarks": "No fee record found for this student",
            "all_semester_records": []
        }

    # Find active/latest semester fee record
    active_record = next((r for r in fee_rows if r["semester"] == student.semester), fee_rows[0])
    total_fee = float(active_record["total_fee"] or 0.0)
    paid_amount = float(active_record["paid_amount"] or 0.0)
    remaining_amount = float(active_record["remaining_amount"] if active_record["remaining_amount"] is not None else (total_fee - paid_amount))
    status_str = active_record["payment_status"] or ("Paid" if remaining_amount <= 0 else "Pending")

    due_str = date_string(active_record["due_date"])
    pay_date_str = date_string(active_record["payment_date"])

    records_list = []
    for r in fee_rows:
        records_list.append({
            "semester": r["semester"],
            "academic_year": r["academic_year"],
            "total_fee": float(r["total_fee"] or 0.0),
            "paid_amount": float(r["paid_amount"] or 0.0),
            "remaining_amount": float(r["remaining_amount"] or 0.0),
            "status": r["payment_status"] or "Pending",
            "due_date": date_string(r["due_date"]),
            "transaction_id": r["transaction_id"] or "N/A"
        })

    return {
        "has_fee_records": True,
        "current_semester": active_record["semester"],
        "academic_year": active_record["academic_year"],
        "total_fee": total_fee,
        "payable_amount": float(active_record["payable_amount"] or total_fee),
        "paid_amount": paid_amount,
        "remaining_amount": remaining_amount,
        "payment_status": status_str,
        "fee_status": status_str,
        "due_date": due_str,
        "payment_date": pay_date_str,
        "payment_method": active_record["payment_method"] or "N/A",
        "transaction_id": active_record["transaction_id"] or "N/A",
        "verified": bool(active_record["verified"]),
        "fine_amount": float(active_record["fine_amount"] or 0.0),
        "discount_amount": float(active_record["discount_amount"] or 0.0),
        "scholarship_amount": float(active_record["scholarship_amount"] or 0.0),
        "remarks": active_record["remarks"] or "",
        "all_semester_records": records_list
    }


def get_exams_context(student: Student, db: Session) -> Dict[str, Any]:
    """Exams and online assessments for the student's enrolled courses."""
    now = datetime.utcnow()

    # Active roster check
    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student.student_id,
            Enrollment.semester == student.semester,
            Enrollment.enrollment_status.in_(["Enrolled", "Completed"])
        )
        .all()
    )

    course_sections = {(e.course_id, e.academic_year, e.semester, e.section) for e in enrollments}

    assessments = (
        db.query(Assessment)
        .filter(Assessment.status == "Published")
        .order_by(Assessment.start_at.asc())
        .all()
    )

    upcoming = []
    available = []
    submitted = []
    expired = []

    for a in assessments:
        key = (a.course_id, a.academic_year, a.semester, a.section)
        if key not in course_sections:
            continue

        c = a.course
        attempt = (
            db.query(AssessmentAttempt)
            .filter_by(assessment_id=a.assessment_id, student_id=student.student_id)
            .first()
        )

        item = {
            "assessment_id": a.assessment_id,
            "title": a.title,
            "type": a.assessment_type,
            "course_code": c.course_code if c else "",
            "course_title": c.course_title if c else "",
            "start_at": a.start_at.strftime("%Y-%m-%d %I:%M %p") if a.start_at else "",
            "end_at": a.end_at.strftime("%Y-%m-%d %I:%M %p") if a.end_at else "",
            "duration_minutes": a.duration_minutes,
            "total_marks": a.total_marks,
            "attempt_status": attempt.status if attempt else "Not Attempted",
            "obtained_marks": attempt.obtained_marks if attempt and attempt.obtained_marks is not None else None,
        }

        if attempt and attempt.status != "In Progress":
            submitted.append(item)
        elif a.start_at and a.end_at and (a.start_at <= now < a.end_at):
            available.append(item)
        elif a.start_at and now < a.start_at:
            upcoming.append(item)
        else:
            expired.append(item)

    return {
        "upcoming_exams": upcoming,
        "available_exams": available,
        "submitted_exams": submitted,
        "expired_exams": expired,
        "total_active_exams": len(upcoming) + len(available),
    }


def get_academic_advice_context(student: Student, db: Session) -> Dict[str, Any]:
    """Synthesizes academic performance indicators for tailored advice."""
    cgpa_ctx = get_cgpa_and_results_context(student, db)
    att_ctx = get_attendance_context(student, db)
    assign_ctx = get_assignments_context(student, db)
    courses_ctx = get_current_courses_context(student, db)
    exams_ctx = get_exams_context(student, db)

    return {
        "student_name": f"{student.first_name} {student.last_name}".strip(),
        "cgpa": cgpa_ctx["overall_cgpa"],
        "academic_status": cgpa_ctx["academic_status"],
        "weak_subjects": cgpa_ctx["weak_subjects"],
        "attendance_rate": att_ctx["overall_percentage"] if att_ctx["has_records"] else "No records",
        "low_attendance_warnings": att_ctx.get("low_attendance_warnings", []),
        "pending_assignments_count": assign_ctx["pending_count"],
        "pending_assignments": assign_ctx["pending_assignments"][:3],
        "upcoming_exams_count": len(exams_ctx["upcoming_exams"]),
        "current_courses_count": courses_ctx["total_enrolled_courses"],
    }


def build_dynamic_student_context(student: Student, db: Session, query: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Intelligently retrieves relevant student database context based on the student's question and history.
    Always includes an essential baseline overview so the AI Agent always knows key live stats.
    """
    q_lower = query.lower()

    # Preload basic context pieces for instant baseline awareness
    profile = get_student_identity_context(student, db)
    fee_ctx = get_fee_status_context(student, db)
    assign_ctx = get_assignments_context(student, db)

    # Core context always accessible to the agent
    context: Dict[str, Any] = {
        "student_profile": profile,
        "live_summary": {
            "current_semester": student.semester,
            "fee_status": fee_ctx.get("fee_status", "Unpaid"),
            "fee_remaining_amount": fee_ctx.get("remaining_amount", 0.0),
            "fee_due_date": fee_ctx.get("due_date", "N/A"),
            "pending_assignments_count": assign_ctx.get("pending_count", 0),
            "pending_assignment_titles": [a["title"] + f" ({a['course_title']})" for a in assign_ctx.get("pending_assignments", [])],
        }
    }

    # Intent detection triggers
    fee_keywords = ["fee", "fees", "challan", "dues", "due", "paid", "payment", "unpaid", "voucher", "scholarship", "installment", "balance", "cost"]
    cgpa_keywords = ["cgpa", "gpa", "grade", "marks", "result", "performance", "standing", "improve", "percentage", "fail", "pass"]
    timetable_keywords = ["class", "classes", "timetable", "schedule", "today", "tomorrow", "next class", "room", "when", "time", "lecture", "lab"]
    course_keywords = ["course", "courses", "subject", "subjects", "studying", "enrolled", "teacher", "professor", "faculty", "credit", "credits"]
    attendance_keywords = ["attendance", "present", "absent", "late", "leave", "miss", "attended", "lowest attendance"]
    assignment_keywords = ["assignment", "assignments", "homework", "task", "pending", "pendings", "submitted", "deadline", "submission", "solve", "help me with"]
    exam_keywords = ["exam", "exams", "quiz", "quizzes", "midterm", "final", "paper", "test", "assessment"]
    advice_keywords = ["improve", "how can i", "what should i", "focus", "advice", "help", "guide", "suggestion", "career", "study plan"]

    include_all = any(k in q_lower for k in advice_keywords)

    if include_all or any(k in q_lower for k in fee_keywords):
        context["fee_status"] = fee_ctx

    if include_all or any(k in q_lower for k in cgpa_keywords):
        context["cgpa_and_results"] = get_cgpa_and_results_context(student, db)

    if include_all or any(k in q_lower for k in timetable_keywords):
        context["timetable"] = get_timetable_context(student, db)

    if include_all or any(k in q_lower for k in course_keywords):
        context["current_courses"] = get_current_courses_context(student, db)

    if include_all or any(k in q_lower for k in attendance_keywords):
        context["attendance"] = get_attendance_context(student, db)

    if include_all or any(k in q_lower for k in assignment_keywords):
        context["assignments"] = assign_ctx

    if include_all or any(k in q_lower for k in exam_keywords):
        context["exams"] = get_exams_context(student, db)

    # History-aware context fallback for short follow-ups (e.g. "pendings", "fees", "how to solve it?")
    if history and len(history) > 0:
        hist_text = " ".join([h.get("content", "").lower() for h in history[-3:]])
        if any(k in hist_text for k in fee_keywords) and "fee_status" not in context:
            context["fee_status"] = fee_ctx
        if any(k in hist_text for k in cgpa_keywords) and "cgpa_and_results" not in context:
            context["cgpa_and_results"] = get_cgpa_and_results_context(student, db)
        if any(k in hist_text for k in timetable_keywords) and "timetable" not in context:
            context["timetable"] = get_timetable_context(student, db)
        if any(k in hist_text for k in attendance_keywords) and "attendance" not in context:
            context["attendance"] = get_attendance_context(student, db)
        if any(k in hist_text for k in assignment_keywords) and "assignments" not in context:
            context["assignments"] = assign_ctx

    return context
