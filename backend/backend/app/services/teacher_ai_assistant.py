"""
teacher_ai_assistant.py
========================
Orchestrates the Teacher AI Academic Agent:
  1. Builds teacher-specific database context
  2. Constructs system prompt with full context as JSON ground truth
  3. Calls AIProviderManager (Groq -> Gemini -> HuggingFace -> Ollama)
  4. Falls back to direct DB keyword-based response engine if all LLMs fail
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.teacher import Teacher
from app.schemas.ai_assistant import ChatMessage
from app.services.ai_providers import AIProviderManager
from app.services.teacher_ai_context import build_dynamic_teacher_context

logger = logging.getLogger("teacher_ai_academic_agent")
provider_manager = AIProviderManager()


# ---------------------------------------------------------------
# Direct database fallback engine
# ---------------------------------------------------------------

def generate_direct_db_response_teacher(
    teacher: Teacher,
    query: str,
    context: Dict[str, Any],
) -> str:
    """
    Keyword-based fallback when no external LLM provider is reachable.
    Answers directly from the teacher context dictionary.
    """
    q = query.lower()
    name = teacher.first_name
    identity = context.get("teacher_identity", {})
    courses_ctx = context.get("courses", {})
    students_ctx = context.get("students", {})
    schedule_ctx = context.get("schedule", {})
    attendance_ctx = context.get("attendance", {})
    assignments_ctx = context.get("assignments", {})
    assessments_ctx = context.get("assessments", {})
    grades_ctx = context.get("grades", {})

    # --- Courses ---
    if any(k in q for k in ["course", "subject", "teaching", "teach", "semester"]):
        courses = courses_ctx.get("courses", [])
        if not courses:
            return f"Hello {name}! You currently have no courses assigned in the system."
        lines = "\n".join([
            f"- **{c.get('course_code', 'Unknown course')}** — {c.get('course_title', 'Untitled course')} "
            f"({c.get('credit_hours', 0)} cr, Sem {c.get('semester', 'N/A')}, {c.get('enrolled_student_count', c.get('enrolled_students', 0))} students)"
            for c in courses
        ])
        total_c = courses_ctx.get("total_courses", len(courses))
        total_ch = courses_ctx.get("total_credit_hours", 0)
        total_st = courses_ctx.get("total_unique_students", courses_ctx.get("total_enrolled_students", 0))
        return (
            f"Hello {name}! You are teaching **{total_c} course(s)** "
            f"totalling **{total_ch} credit hours** with **{total_st} unique enrolled students**:\n\n"
            f"{lines}"
        )

    # --- Students ---
    if any(k in q for k in ["student", "enroll", "roster", "how many student", "registered", "who is"]):
        students = students_ctx.get("students", [])
        total = students_ctx.get("total_students", 0)
        if not students:
            return f"Hello {name}! No student enrollment data is available for your courses yet."
        # Check if asking about a specific course
        courses = courses_ctx.get("courses", [])
        for c in courses:
            code = c.get("course_code", "").lower()
            title_words = c.get("course_title", "").lower().split()
            if code in q or any(w in q for w in title_words if len(w) > 3):
                enrolled = [
                    s for s in students
                    if any(e["course_code"] == c["course_code"] for e in s.get("courses_enrolled", []))
                ]
                if enrolled:
                    lines = "\n".join([
                        f"- {s['name']} ({s['roll_number']}, Sem {s['semester']})"
                        for s in enrolled[:30]
                    ])
                    return (
                        f"Hello {name}! Here are the **{len(enrolled)} students** enrolled in "
                        f"**{c['course_code']} — {c['course_title']}**:\n\n{lines}"
                    )
        # General student count
        sample = students[:10]
        lines = "\n".join([f"- {s['name']} ({s['roll_number']}, {s['program']})" for s in sample])
        more = f"\n...and {total - 10} more students." if total > 10 else ""
        return (
            f"Hello {name}! You have **{total} students** enrolled across all your courses.\n\n"
            f"{lines}{more}"
        )

    # --- Schedule / Timetable ---
    if any(k in q for k in ["schedule", "timetable", "today", "class today", "lecture", "when", "room", "time"]):
        today_day = schedule_ctx.get("today_day", datetime.now().strftime("%A"))
        today_classes = schedule_ctx.get("today_classes", [])
        weekly = schedule_ctx.get("weekly_schedule", [])

        if "today" in q:
            if today_classes:
                lines = "\n".join([
                    f"- **{c['course_code']}** {c['course_title']} | "
                    f"{c['start_time']} – {c['end_time']} | Room: {c['room']} | "
                    f"Section {c['section']} | {c['enrolled_student_count']} students"
                    for c in today_classes
                ])
                return (
                    f"Hello {name}! Here are your **{len(today_classes)} class(es)** for today ({today_day}):\n\n{lines}"
                )
            else:
                return f"Hello {name}! You have no scheduled classes today ({today_day})."

        if weekly:
            lines = "\n".join([
                f"- **{c['day']}** | {c['course_code']} {c['course_title']} | "
                f"{c['start_time']} – {c['end_time']} | Room {c['room']} | Section {c['section']}"
                for c in weekly
            ])
            return (
                f"Hello {name}! Here is your full weekly schedule "
                f"(**{len(weekly)} slots** across the week):\n\n{lines}"
            )
        return f"Hello {name}! No active class schedule records found for you."

    # --- Attendance ---
    if any(k in q for k in ["attendance", "absent", "present", "low attendance", "missing", "participation"]):
        if not attendance_ctx.get("has_records", False):
            return f"Hello {name}! No attendance records have been recorded yet for your courses."

        low_students = attendance_ctx.get("low_attendance_students", [])
        course_summaries = attendance_ctx.get("course_summaries", [])

        if any(k in q for k in ["low", "missing", "absent", "warning"]):
            if not low_students:
                return f"Hello {name}! Great news — all students currently have attendance above 75%."
            lines = "\n".join([
                f"- **{s['student_name']}** ({s['roll_number']}) — "
                f"{s['course_code']}: **{s['attendance_percentage']}%** attendance"
                f" ({s['absent']} absences)"
                for s in low_students[:20]
            ])
            return (
                f"Hello {name}! **{len(low_students)} student(s)** have attendance below 75% "
                f"and may need your attention:\n\n{lines}"
            )

        if course_summaries:
            lines = "\n".join([
                f"- **{cs['course_code']}** {cs['course_title']}: "
                f"{cs['attendance_percentage']}% | "
                f"Total sessions: {cs['total_sessions']} | "
                f"Present: {cs['present_count']} | Absent: {cs['absent_count']}"
                for cs in course_summaries
            ])
            return f"Hello {name}! Here is the attendance summary for your courses:\n\n{lines}"

    # --- Assignments ---
    if any(k in q for k in ["assignment", "submission", "pending", "grading", "due", "homework"]):
        assignments = assignments_ctx.get("assignments", [])
        pending_total = assignments_ctx.get("pending_grading_total", 0)

        if not assignments:
            return f"Hello {name}! You have not created any assignments yet."

        if any(k in q for k in ["pending", "grading", "ungraded"]):
            pending = [a for a in assignments if a["ungraded_submissions"] > 0]
            if not pending:
                return f"Hello {name}! All submissions have been graded. No pending reviews."
            lines = "\n".join([
                f"- **{a['title']}** ({a['course_code']}) — "
                f"{a['ungraded_submissions']} ungraded / {a['total_submissions']} submissions"
                for a in pending
            ])
            return (
                f"Hello {name}! You have **{pending_total} ungraded submission(s)** across "
                f"{len(pending)} assignment(s):\n\n{lines}"
            )

        # General assignment overview
        lines = "\n".join([
            f"- **{a['title']}** ({a['course_code']}) | Due: {a['due_date']} | "
            f"Submissions: {a['total_submissions']}/{a['enrolled_students']} | "
            f"Status: {a['status']}"
            for a in assignments[:15]
        ])
        return (
            f"Hello {name}! You have **{len(assignments)} assignment(s)** total "
            f"with {pending_total} ungraded submissions:\n\n{lines}"
        )

    # --- Assessments ---
    if any(k in q for k in ["assessment", "exam", "midterm", "final", "test", "online"]):
        assessments = assessments_ctx.get("assessments", [])
        if not assessments:
            return f"Hello {name}! No assessments or exams have been created yet."
        lines = "\n".join([
            f"- **{a['title']}** ({a['assessment_type']}) — {a['course_code']} | "
            f"Status: {a['status']} | Attempts: {a['completed_attempts']}/{a['total_attempts']} | "
            f"Avg score: {a['average_score']}/{a['total_marks']}"
            for a in assessments[:15]
        ])
        return (
            f"Hello {name}! Here are your **{len(assessments)} assessment(s)/exam(s)**:\n\n{lines}"
        )

    # --- Grades / Performance ---
    if any(k in q for k in ["grade", "mark", "score", "result", "performance", "average", "gpa", "gradebook"]):
        if not grades_ctx.get("has_grades", False):
            return f"Hello {name}! No grade entries have been recorded yet for your courses."
        summaries = grades_ctx.get("course_grade_summaries", [])
        lines = "\n".join([
            f"- **{s['course_code']}** {s['course_title']}: "
            f"Class avg **{s['class_average_percentage']}%** | "
            f"Graded: {s['graded_students']} students | "
            f"Top (>=85%): {len(s['top_performers'])} | Weak (<50%): {len(s['weak_performers'])}"
            for s in summaries
        ])
        return f"Hello {name}! Here is your gradebook summary:\n\n{lines}"

    # --- Default / Workload overview ---
    courses = courses_ctx.get("courses", [])
    total_c = courses_ctx.get("total_courses", 0)
    total_st = courses_ctx.get("total_unique_students", 0)
    total_ch = courses_ctx.get("total_credit_hours", 0)
    today_ct = schedule_ctx.get("today_class_count", 0) if schedule_ctx else 0
    pending_g = assignments_ctx.get("pending_grading_total", 0) if assignments_ctx else 0
    low_att = attendance_ctx.get("low_attendance_count", 0) if attendance_ctx else 0

    return (
        f"Hello {name}! 👋 Here is a quick overview of your academic workload:\n\n"
        f"- **Courses:** {total_c} course(s) | **Total Credits:** {total_ch} | **Students:** {total_st}\n"
        f"- **Classes Today:** {today_ct}\n"
        f"- **Pending Grading:** {pending_g} submission(s)\n"
        f"- **Low Attendance Alerts:** {low_att} student(s) below 75%\n\n"
        f"You can ask me about your courses, students, schedule, attendance, assignments, exams, or grades!"
    )


# ---------------------------------------------------------------
# Main chat processor
# ---------------------------------------------------------------

def process_teacher_chat(
    teacher: Teacher,
    db: Session,
    user_message: str,
    history: Optional[List[ChatMessage]] = None,
) -> Tuple[str, Optional[str]]:
    """
    Main entry point for the Teacher AI Academic Agent.
    Returns: (response_text, provider_name)
    """
    hist_dicts = [{"role": h.role, "content": h.content} for h in (history or [])]

    # Submission review chat already carries its own assignment and document
    # context. Avoid rebuilding the full teacher dashboard context here; that
    # makes local models time out and causes the generic assignment fallback.
    if user_message.startswith("[SUBMISSION REVIEW CHAT CONTEXT]"):
        review_system_prompt = """You are a teacher's submission-review assistant. Answer only from the assignment and student work included in the user message. Do not invent facts, marks, or content that is not present. Explain your reasoning clearly and use professional markdown headings and bullet points. If the file content is unavailable, say so explicitly."""
        review_messages = [
            {"role": "assistant" if item["role"] in ("assistant", "system_bot") else "user", "content": item["content"]}
            for item in hist_dicts[-4:]
        ]
        review_messages.append({"role": "user", "content": user_message})
        review_response, review_provider = provider_manager.generate_chat(
            system_prompt=review_system_prompt,
            messages=review_messages,
        )
        if review_response:
            return review_response, review_provider
        return (
            "### Review Assistant\n\n"
            "The AI model is currently unavailable or timed out. I could not safely generate a submission-specific answer. "
            "Please retry shortly or review the extracted student document manually; no marks were assigned by this fallback.",
            "Local Review Safeguard",
        )

    # 1. Build real-time teacher context from DB
    context = build_dynamic_teacher_context(teacher, db, user_message, hist_dicts)
    context_json = json.dumps(context, indent=2, default=str)

    designation = teacher.designation or "Teacher"
    full_name = f"{teacher.first_name} {teacher.last_name}".strip()
    dept = teacher.department.department_name if teacher.department else "the department"

    # 2. Build system prompt
    system_prompt = f"""You are the official AI Academic Agent for the University of Haripur (UoH), serving {designation} {full_name} from the {dept} department.

YOU HAVE FULL READ ACCESS TO THIS TEACHER'S LIVE DATABASE RECORDS. ACT AS AN AUTONOMOUS ACADEMIC AGENT:

1. NEVER say "check the system" or "contact admin" for data that is present in the VERIFIED DATABASE RECORDS below. Answer directly.
2. Address the teacher warmly as '{teacher.first_name}'.
3. If asked about their courses — list them with student counts, credit hours, and semester.
4. If asked about students — list enrolled students for the relevant course(s) with roll numbers.
5. If asked about schedule — provide today's classes and/or full weekly timetable with room, time, and section.
6. If asked about attendance — give per-course attendance percentages and highlight low-attendance students (< 75%).
7. If asked about assignments — show assignment list, submission counts, and pending grading items.
8. If asked about assessments/exams — show assessments with attempt counts and average scores.
9. If asked about grades/gradebook — show per-course averages, top and weak performers.
10. If asked about workload — summarize total courses, students, credit hours, and pending actions.
11. For general academic, pedagogical, or university policy questions — answer as a knowledgeable academic assistant.
12. Keep answers structured, concise, and professional. Use markdown formatting (bold, lists).

VERIFIED TEACHER DATABASE RECORDS (GROUND TRUTH — USE THIS DATA):
```json
{context_json}
```
"""

    # 3. Format conversation history for LLM
    formatted_messages: List[Dict[str, str]] = []
    if history:
        for msg in history[-6:]:
            role = "assistant" if msg.role in ("assistant", "system_bot") else "user"
            formatted_messages.append({"role": role, "content": msg.content})
    formatted_messages.append({"role": "user", "content": user_message})

    # 4. Try LLM providers
    ai_response, provider = provider_manager.generate_chat(system_prompt, formatted_messages)
    if ai_response:
        return ai_response, provider

    # 5. Fallback to direct DB engine
    logger.info("All LLM providers failed. Using direct DB response engine for teacher agent.")
    direct_response = generate_direct_db_response_teacher(teacher, user_message, context)
    return direct_response, "Local Database Agent"
