"""
teacher_ai_context.py
=====================
Builds a comprehensive real-time context dictionary from the database
for the authenticated teacher AI Academic Agent.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.class_schedule import ClassSchedule
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.exam import Assessment, AssessmentAttempt
from app.models.grade import Grade
from app.models.student import Student
from app.models.submission import Submission
from app.models.teacher import Teacher


def _fmt_time(t_str: str) -> str:
    try:
        return datetime.strptime(t_str, "%H:%M").strftime("%I:%M %p").lstrip("0")
    except Exception:
        return t_str


# ---------------------------------------------------------------
# 1. Teacher Identity
# ---------------------------------------------------------------

def get_teacher_identity_context(teacher: Teacher) -> Dict[str, Any]:
    designation = teacher.designation or "Teacher"
    full_name = f"{teacher.first_name} {teacher.last_name}".strip()
    titled_name = f"{designation} {full_name}"
    return {
        "teacher_id": teacher.teacher_id,
        "employee_id": teacher.employee_id,
        "full_name": full_name,
        "titled_name": titled_name,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "designation": designation,
        "qualification": teacher.qualification or "N/A",
        "specialization": teacher.specialization or "N/A",
        "department": teacher.department.department_name if teacher.department else "N/A",
        "office_email": teacher.office_email,
        "office_room": teacher.office_room or "N/A",
        "phone": teacher.phone or "N/A",
        "employment_type": teacher.employment_type,
        "status": teacher.status,
    }


# ---------------------------------------------------------------
# 2. Courses
# ---------------------------------------------------------------

def get_teacher_courses_context(teacher: Teacher, db: Session) -> Dict[str, Any]:
    courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher.teacher_id)
        .order_by(Course.semester.asc(), Course.course_code.asc())
        .all()
    )

    course_list = []
    total_credits = 0
    total_unique_students = 0

    for c in courses:
        enrolled_count = (
            db.query(func.count(Enrollment.student_id))
            .join(Student, Student.student_id == Enrollment.student_id)
            .filter(
                Enrollment.course_id == c.course_id,
                Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
                Enrollment.semester == Student.semester,
            )
            .scalar() or 0
        )
        total_unique_students += enrolled_count
        total_credits += c.credit_hours or 0

        course_list.append({
            "course_code": c.course_code,
            "course_title": c.course_title,
            "credit_hours": c.credit_hours,
            "semester": c.semester,
            "enrolled_students": enrolled_count,
        })

    return {
        "total_courses": len(course_list),
        "total_credit_hours": total_credits,
        "total_enrolled_students": total_unique_students,
        "courses": course_list,
    }


# ---------------------------------------------------------------
# 3. Student Roster
# ---------------------------------------------------------------

def get_teacher_students_context(teacher: Teacher, db: Session) -> Dict[str, Any]:
    enrollments = (
        db.query(Enrollment)
        .join(Course, Course.course_id == Enrollment.course_id)
        .join(Student, Student.student_id == Enrollment.student_id)
        .filter(
            Course.teacher_id == teacher.teacher_id,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
            Enrollment.semester == Student.semester,
        )
        .all()
    )

    students_map: Dict[int, Dict[str, Any]] = {}
    for e in enrollments:
        s = e.student
        c = e.course
        if s.student_id not in students_map:
            students_map[s.student_id] = {
                "roll_number": s.roll_number,
                "name": f"{s.first_name} {s.last_name}".strip(),
                "program": s.program,
                "semester": s.semester,
                "section": s.section,
                "course": c.course_code,
            }

    students_list = sorted(students_map.values(), key=lambda x: x["name"])
    return {
        "total_students": len(students_list),
        "sample_students": students_list[:30],
    }


# ---------------------------------------------------------------
# 4. Schedule
# ---------------------------------------------------------------

def get_teacher_schedule_context(teacher: Teacher, db: Session) -> Dict[str, Any]:
    today_name = datetime.now().strftime("%A")
    schedules = (
        db.query(ClassSchedule)
        .filter(
            ClassSchedule.teacher_id == teacher.teacher_id,
            ClassSchedule.status == "Active",
        )
        .all()
    )

    day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                 "Friday": 4, "Saturday": 5, "Sunday": 6}
    schedules.sort(key=lambda s: (day_order.get(s.day_of_week, 99), s.start_time))

    today_classes: List[Dict[str, Any]] = []
    weekly_by_day: Dict[str, List[str]] = {}

    for sched in schedules:
        c = sched.course
        code = c.course_code if c else ""
        t_str = f"{_fmt_time(sched.start_time)}-{_fmt_time(sched.end_time)}"
        slot_str = f"{code} ({sched.room_location}, {t_str})"
        slots = weekly_by_day.setdefault(sched.day_of_week, [])
        if len(slots) < 4:
            slots.append(slot_str)

        if sched.day_of_week.lower() == today_name.lower():
            today_classes.append({
                "course_code": code,
                "course_title": c.course_title if c else "",
                "time": t_str,
                "room": sched.room_location,
                "section": sched.section,
            })

    return {
        "today_day": today_name,
        "today_classes": today_classes,
        "today_class_count": len(today_classes),
        "weekly_sample_by_day": weekly_by_day,
        "total_weekly_slots": len(schedules),
    }




# ---------------------------------------------------------------
# 5. Attendance
# ---------------------------------------------------------------

def get_teacher_attendance_context(teacher: Teacher, db: Session) -> Dict[str, Any]:
    records = (
        db.query(Attendance)
        .filter(Attendance.teacher_id == teacher.teacher_id)
        .all()
    )

    if not records:
        return {
            "has_records": False,
            "message": "No attendance records have been saved yet.",
            "total_sessions_recorded": 0,
            "course_summaries": [],
            "low_attendance_students": [],
        }

    course_stats: Dict[int, Dict[str, Any]] = {}
    student_course_stats: Dict[tuple, Dict[str, Any]] = {}

    for r in records:
        cid = r.course_id
        c = r.course
        if cid not in course_stats:
            course_stats[cid] = {
                "course_id": cid,
                "course_code": c.course_code if c else "",
                "course_title": c.course_title if c else "",
                "total_sessions": 0,
                "present_count": 0,
                "absent_count": 0,
                "late_count": 0,
                "leave_count": 0,
            }
        cs = course_stats[cid]
        cs["total_sessions"] += 1
        if r.status == "Present":
            cs["present_count"] += 1
        elif r.status == "Absent":
            cs["absent_count"] += 1
        elif r.status == "Late":
            cs["late_count"] += 1
        elif r.status == "Leave":
            cs["leave_count"] += 1

        key = (r.student_id, cid)
        if key not in student_course_stats:
            s = r.student
            student_course_stats[key] = {
                "student_id": r.student_id,
                "student_name": f"{s.first_name} {s.last_name}".strip() if s else "Unknown",
                "roll_number": s.roll_number if s else "",
                "course_code": c.course_code if c else "",
                "course_title": c.course_title if c else "",
                "total": 0,
                "present": 0,
                "absent": 0,
                "late": 0,
            }
        scs = student_course_stats[key]
        scs["total"] += 1
        if r.status == "Present":
            scs["present"] += 1
        elif r.status == "Absent":
            scs["absent"] += 1
        elif r.status == "Late":
            scs["late"] += 1

    course_summaries = []
    for cs in course_stats.values():
        attended = cs["present_count"] + cs["late_count"]
        total = cs["total_sessions"]
        cs["attendance_percentage"] = round(attended / total * 100, 1) if total > 0 else 0.0
        course_summaries.append(cs)

    low_att_students = []
    for scs in student_course_stats.values():
        total = scs["total"]
        attended = scs["present"] + scs["late"]
        pct = round(attended / total * 100, 1) if total > 0 else 0.0
        scs["attendance_percentage"] = pct
        if pct < 75.0:
            low_att_students.append(scs)

    low_att_students.sort(key=lambda x: x["attendance_percentage"])

    return {
        "has_records": True,
        "total_sessions_recorded": len(records),
        "course_summaries": course_summaries,
        "low_attendance_students": low_att_students,
        "low_attendance_count": len(low_att_students),
    }


# ---------------------------------------------------------------
# 6. Assignments
# ---------------------------------------------------------------

def get_teacher_assignments_context(teacher: Teacher, db: Session) -> Dict[str, Any]:
    assignments = (
        db.query(Assignment)
        .filter(Assignment.teacher_id == teacher.teacher_id)
        .order_by(Assignment.due_date.desc())
        .all()
    )

    now = datetime.utcnow()
    assignment_list = []
    pending_grading_count = 0

    for a in assignments:
        c = a.course
        submissions = (
            db.query(Submission)
            .filter(Submission.assignment_id == a.assignment_id)
            .all()
        )
        total_subs = len(submissions)
        graded_subs = sum(1 for s in submissions if s.graded)
        ungraded = total_subs - graded_subs
        late_subs = sum(1 for s in submissions if s.is_late)

        enrolled_count = (
            db.query(func.count(Enrollment.student_id))
            .join(Student, Student.student_id == Enrollment.student_id)
            .filter(
                Enrollment.course_id == a.course_id,
                Enrollment.semester == Student.semester,
                Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
            )
            .scalar() or 0
        )

        pending_grading_count += ungraded

        assignment_list.append({
            "assignment_id": a.assignment_id,
            "title": a.title,
            "assignment_type": a.assignment_type,
            "course_code": c.course_code if c else "",
            "course_title": c.course_title if c else "",
            "total_marks": a.total_marks,
            "semester": a.semester,
            "section": a.section,
            "release_date": str(a.release_date.date()) if a.release_date else "",
            "due_date": str(a.due_date.date()) if a.due_date else "",
            "is_past_due": a.due_date < now,
            "status": a.status,
            "enrolled_students": enrolled_count,
            "total_submissions": total_subs,
            "graded_submissions": graded_subs,
            "ungraded_submissions": ungraded,
            "late_submissions": late_subs,
            "submission_rate": round(total_subs / enrolled_count * 100, 1) if enrolled_count > 0 else 0.0,
        })

    return {
        "total_assignments": len(assignment_list),
        "pending_grading_total": pending_grading_count,
        "assignments": assignment_list,
    }


# ---------------------------------------------------------------
# 7. Assessments / Exams
# ---------------------------------------------------------------

def get_teacher_assessments_context(teacher: Teacher, db: Session) -> Dict[str, Any]:
    assessments = (
        db.query(Assessment)
        .filter(Assessment.teacher_id == teacher.teacher_id)
        .order_by(Assessment.start_at.desc())
        .all()
    )

    assessment_list = []
    for a in assessments:
        c = a.course
        attempts = (
            db.query(AssessmentAttempt)
            .filter(AssessmentAttempt.assessment_id == a.assessment_id)
            .all()
        )
        total_attempts = len(attempts)
        completed = sum(1 for at in attempts if at.status == "Submitted")
        avg_score = 0.0
        if completed > 0:
            total_obtained = sum(at.obtained_marks for at in attempts if at.status == "Submitted")
            avg_score = round(total_obtained / completed, 1)

        assessment_list.append({
            "assessment_id": a.assessment_id,
            "title": a.title,
            "assessment_type": a.assessment_type,
            "course_code": c.course_code if c else "",
            "course_title": c.course_title if c else "",
            "semester": a.semester,
            "section": a.section,
            "total_marks": a.total_marks,
            "start_at": str(a.start_at),
            "end_at": str(a.end_at),
            "duration_minutes": a.duration_minutes,
            "status": a.status,
            "total_attempts": total_attempts,
            "completed_attempts": completed,
            "average_score": avg_score,
        })

    return {
        "total_assessments": len(assessment_list),
        "assessments": assessment_list,
    }


# ---------------------------------------------------------------
# 8. Grades / Gradebook
# ---------------------------------------------------------------

def get_teacher_grades_context(teacher: Teacher, db: Session) -> Dict[str, Any]:
    grades = (
        db.query(Grade)
        .filter(Grade.graded_by == teacher.teacher_id)
        .all()
    )

    if not grades:
        return {
            "has_grades": False,
            "message": "No grades have been entered yet.",
            "course_grade_summaries": [],
        }

    course_grades: Dict[int, Dict[str, Any]] = {}
    for g in grades:
        enrollment = g.enrollment
        if not enrollment:
            continue
        cid = enrollment.course_id
        course = enrollment.course
        if cid not in course_grades:
            course_grades[cid] = {
                "course_code": course.course_code if course else "",
                "course_title": course.course_title if course else "",
                "student_scores": {},
            }

        student = enrollment.student
        sid = enrollment.student_id
        student_name = f"{student.first_name} {student.last_name}".strip() if student else "Unknown"
        roll = student.roll_number if student else ""

        if sid not in course_grades[cid]["student_scores"]:
            course_grades[cid]["student_scores"][sid] = {
                "student_name": student_name,
                "roll_number": roll,
                "total_obtained": 0.0,
                "total_possible": 0.0,
            }
        ss = course_grades[cid]["student_scores"][sid]
        ss["total_obtained"] += g.obtained_marks or 0.0
        ss["total_possible"] += g.total_marks or 0.0

    summaries = []
    for cid, data in course_grades.items():
        scores = list(data["student_scores"].values())
        for sc in scores:
            sc["percentage"] = round(sc["total_obtained"] / sc["total_possible"] * 100, 1) if sc["total_possible"] > 0 else 0.0

        avg_pct = round(sum(sc["percentage"] for sc in scores) / len(scores), 1) if scores else 0.0
        scores_sorted = sorted(scores, key=lambda x: x["percentage"])
        top_performers = [s for s in scores if s["percentage"] >= 85]
        weak_performers = [s for s in scores if s["percentage"] < 50]

        summaries.append({
            "course_code": data["course_code"],
            "course_title": data["course_title"],
            "graded_students": len(scores),
            "class_average_percentage": avg_pct,
            "top_performers": top_performers,
            "weak_performers": weak_performers,
            "lowest_student": scores_sorted[0] if scores_sorted else None,
            "highest_student": scores_sorted[-1] if scores_sorted else None,
        })

    return {
        "has_grades": True,
        "total_grade_entries": len(grades),
        "course_grade_summaries": summaries,
    }


# ---------------------------------------------------------------
# Master context builder
# ---------------------------------------------------------------

def build_dynamic_teacher_context(
    teacher: Teacher,
    db: Session,
    user_message: str = "",
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Builds the full real-time context for the teacher AI agent.
    Uses keyword routing to include only the relevant sections.
    """
    q = user_message.lower()

    ctx: Dict[str, Any] = {
        "teacher_identity": get_teacher_identity_context(teacher),
        "courses": get_teacher_courses_context(teacher, db),
    }

    if any(k in q for k in ["student", "enroll", "roster", "who", "how many", "registered", "name"]):
        ctx["students"] = get_teacher_students_context(teacher, db)

    if any(k in q for k in ["schedule", "timetable", "today", "time", "class", "when", "room", "lecture"]):
        ctx["schedule"] = get_teacher_schedule_context(teacher, db)

    if any(k in q for k in ["attendance", "absent", "present", "low attendance", "missing", "participation"]):
        ctx["attendance"] = get_teacher_attendance_context(teacher, db)

    if any(k in q for k in ["assignment", "submission", "pending", "grading", "due", "quiz", "project", "homework"]):
        ctx["assignments"] = get_teacher_assignments_context(teacher, db)

    if any(k in q for k in ["assessment", "exam", "midterm", "final", "test", "online exam"]):
        ctx["assessments"] = get_teacher_assessments_context(teacher, db)

    if any(k in q for k in ["grade", "gradebook", "mark", "score", "result", "performance", "average", "gpa"]):
        ctx["grades"] = get_teacher_grades_context(teacher, db)

    # For general / broad questions — include a lightweight overview
    is_specific = any(k in q for k in [
        "course", "subject", "teach", "student", "enroll", "schedule", "timetable",
        "today", "time", "class", "when", "attendance", "absent", "assignment",
        "submission", "grade", "assessment", "exam", "quiz", "performance", "roster", "who", "mark"
    ])
    if not is_specific:
        ctx["schedule"] = get_teacher_schedule_context(teacher, db)
        ctx["assignments"] = get_teacher_assignments_context(teacher, db)


    ctx["context_generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ctx
