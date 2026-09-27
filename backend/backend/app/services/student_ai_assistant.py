import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.ai_assistant import ChatMessage
from app.services.ai_providers import AIProviderManager
from app.services.student_ai_context import build_dynamic_student_context

logger = logging.getLogger("ai_academic_assistant")
provider_manager = AIProviderManager()


def generate_direct_database_response(student: Student, query: str, context: Dict[str, Any]) -> str:
    """
    Fallback generator when no external AI LLM providers are reachable or configured.
    Provides direct, accurate answers from the student's database context.
    """
    q_lower = query.lower()
    first_name = student.first_name

    # 0. Fee Status & Dues
    if any(k in q_lower for k in ["fee", "dues", "challan", "voucher", "payment", "scholarship", "unpaid", "paid", "balance", "cost"]):
        fee_info = context.get("fee_status", {})
        status = fee_info.get("fee_status", "Unpaid")
        total = fee_info.get("total_fee", 55000.0)
        paid = fee_info.get("paid_amount", 0.0)
        rem = fee_info.get("remaining_amount", total)
        due = fee_info.get("due_date", "N/A")
        txn = fee_info.get("transaction_id", "N/A")
        sem = fee_info.get("current_semester", student.semester)

        return (
            f"Hello {first_name}! Here is your fee status for Semester {sem}:\n\n"
            f"- **Payment Status**: **{status}**\n"
            f"- **Total Semester Fee**: PKR {total:,.0f}\n"
            f"- **Paid Amount**: PKR {paid:,.0f}\n"
            f"- **Remaining Balance Due**: PKR {rem:,.0f}\n"
            f"- **Due Date**: {due}\n"
            f"- **Receipt / Transaction ID**: {txn}"
        )

    # 1. CGPA & GPA
    if "cgpa" in q_lower or "gpa" in q_lower or "result" in q_lower:
        cgpa_info = context.get("cgpa_and_results", {})
        cgpa = cgpa_info.get("overall_cgpa", 0.0)
        credits_done = cgpa_info.get("total_completed_credits", 0)
        standing = cgpa_info.get("academic_status", "Good Standing")
        sem_gpas = cgpa_info.get("semester_gpas", [])

        if not sem_gpas and cgpa == 0.0:
            return f"Hello {first_name}, your current semester (Semester {student.semester}) is currently in progress. Final CGPA and GPA will be updated once your semester exams and course results are finalized."

        gpa_str = "\n".join([f"- **Semester {s['semester']}**: GPA {s['gpa']} ({s['earned_credits']} credits)" for s in sem_gpas])
        return (
            f"Hello {first_name}! Here is your current academic performance record:\n\n"
            f"- **Overall CGPA**: **{cgpa:.2f}** / 4.00\n"
            f"- **Completed Credit Hours**: {credits_done}\n"
            f"- **Academic Standing**: {standing}\n\n"
            f"**Semester-wise GPA Breakdown**:\n{gpa_str or 'No past semester GPA recorded.'}"
        )

    # 2. Timetable & Classes
    if "class" in q_lower or "timetable" in q_lower or "schedule" in q_lower:
        tt_info = context.get("timetable", {})
        today_day = tt_info.get("today_day", "Today")
        today_classes = tt_info.get("today_classes", [])
        next_cls = tt_info.get("next_class")

        if "next" in q_lower and next_cls:
            return (
                f"Hello {first_name}, your next scheduled class is **{next_cls['course_title']}** ({next_cls['course_code']}) "
                f"on **{next_cls['day']}** at **{next_cls['start_time']} - {next_cls['end_time']}** in **{next_cls['room']}** "
                f"with {next_cls['teacher']}."
            )

        if today_classes:
            class_lines = "\n".join([
                f"- **{c['course_title']}** ({c['course_code']}): {c['start_time']} - {c['end_time']} | Room: {c['room']} | Instructor: {c['teacher']}"
                for c in today_classes
            ])
            return f"Hello {first_name}, here are your scheduled classes for today ({today_day}):\n\n{class_lines}"
        else:
            weekly = tt_info.get("weekly_schedule", [])
            if weekly:
                return f"Hello {first_name}, you have no classes scheduled for {today_day}. You have {len(weekly)} class sessions scheduled across the week."
            return f"Hello {first_name}, I don't have a configured timetable for your section yet."

    # 3. Courses
    if "course" in q_lower or "subject" in q_lower or "teacher" in q_lower or "professor" in q_lower:
        crs_info = context.get("current_courses", {})
        courses = crs_info.get("courses", [])
        if courses:
            crs_lines = "\n".join([
                f"- **{c['course_title']}** (`{c['course_code']}`) - {c['credit_hours']} Credit Hours | Instructor: {c['teacher']} ({c['office_room']})"
                for c in courses
            ])
            return (
                f"Hello {first_name}, you are currently enrolled in **{len(courses)} courses** for Semester {student.semester}:\n\n"
                f"{crs_lines}"
            )
        return f"Hello {first_name}, no active enrolled courses were found for your profile in Semester {student.semester}."

    # 4. Attendance
    if "attendance" in q_lower or "present" in q_lower or "absent" in q_lower:
        att_info = context.get("attendance", {})
        if not att_info.get("has_records"):
            return f"Hello {first_name}, no attendance records have been uploaded for your classes yet."

        overall = att_info.get("overall_percentage", 0.0)
        c_att = att_info.get("courses_attendance", [])
        breakdown = "\n".join([
            f"- **{c['course_title']}** ({c['course_code']}): **{c['percentage']}%** ({c['attended']}/{c['total_classes']} classes attended)"
            for c in c_att
        ])
        return (
            f"Hello {first_name}, your overall attendance across all courses is **{overall}%**.\n\n"
            f"**Course Breakdown**:\n{breakdown}"
        )

    # 5. Assignments
    if any(k in q_lower for k in ["assignment", "assignments", "homework", "task", "pending", "pendings", "submission"]):
        asg_info = context.get("assignments", {})
        pending = asg_info.get("pending_assignments", [])
        submitted = asg_info.get("submitted_assignments", [])

        if not pending and not submitted:
            return f"Hello {first_name}, you currently have no pending or active assignments assigned."

        p_str = "\n".join([f"- **{a['title']}** ({a['course_title']}) - Due: {a['due_date']} (Max Marks: {a['total_marks']})" for a in pending]) or "None"
        s_str = "\n".join([f"- **{a['title']}** ({a['course_title']}) - Status: {a['submission_status']}" for a in submitted]) or "None"

        return (
            f"Hello {first_name}, here is your assignment status:\n\n"
            f"**Pending Assignments ({len(pending)})**:\n{p_str}\n\n"
            f"**Submitted Assignments ({len(submitted)})**:\n{s_str}"
        )

    # 6. Exams
    if "exam" in q_lower or "quiz" in q_lower or "midterm" in q_lower or "final" in q_lower or "test" in q_lower:
        exam_info = context.get("exams", {})
        upcoming = exam_info.get("upcoming_exams", [])
        available = exam_info.get("available_exams", [])

        if not upcoming and not available:
            return f"Hello {first_name}, you currently have no active or upcoming online exams scheduled."

        av_str = "\n".join([f"- **{e['title']}** ({e['course_code']} {e['type']}) - Open until: {e['end_at']} ({e['duration_minutes']} mins)" for e in available])
        up_str = "\n".join([f"- **{e['title']}** ({e['course_code']} {e['type']}) - Scheduled: {e['start_at']}" for e in upcoming])

        resp = f"Hello {first_name}, here are your exam schedules:\n\n"
        if available:
            resp += f"**Available Right Now**:\n{av_str}\n\n"
        if upcoming:
            resp += f"**Upcoming Exams**:\n{up_str}\n\n"
        return resp.strip()

    # 7. Academic Improvement, Weak Subjects, & Performance Advice
    advice_keywords = ["improve", "focus", "performance", "weak", "study", "advice", "suggestion", "recommend", "better", "how to solve"]
    if any(k in q_lower for k in advice_keywords):
        cgpa_info = context.get("cgpa_and_results", {})
        cgpa = cgpa_info.get("overall_cgpa", 0.0)
        weak_subs = cgpa_info.get("weak_subjects", [])
        crs_info = context.get("current_courses", {})
        courses = crs_info.get("courses", [])

        weak_lines = ""
        if weak_subs:
            weak_lines = "\n".join([f"- **{w['course_title']}** (`{w['course_code']}`): Grade {w['letter_grade']} (GPA {w['grade_points']})" for w in weak_subs[:3]])
        else:
            weak_lines = "- You maintained solid academic standing across your completed semesters."

        current_crs_lines = "\n".join([f"- **{c['course_title']}** (`{c['course_code']}`) - {c['credit_hours']} credits" for c in courses[:4]])

        return (
            f"Hello {first_name}! Here is a personalized strategy to excel in Semester {student.semester}:\n\n"
            f"**1. Current Performance Baseline**:\n"
            f"- Current CGPA: **{cgpa:.2f}** / 4.00\n"
            f"- Areas for improvement from previous semesters:\n{weak_lines}\n\n"
            f"**2. High-Impact Target for Semester {student.semester}**:\n"
            f"- Focus strongly on your active core courses:\n{current_crs_lines}\n"
            f"- Aiming for an 'A' (4.00) or 'A-' (3.67) in high-credit courses will significantly boost your cumulative CGPA.\n\n"
            f"**3. Key Action Steps**:\n"
            f"- **Consistent Attendance**: Keep course attendance above 85% to ensure full internal sessional marks.\n"
            f"- **Assignments**: Complete and submit all lab/theory assignments before the due date.\n"
            f"- **Midterms & Quizzes**: Prepare early for upcoming teacher assessments."
        )

    # 8. General Welcome / Default Academic Overview
    return (
        f"Hello {first_name}! 👋 I am your AI Academic Agent for {student.program} (Semester {student.semester}, Section {student.section or 'A'}).\n\n"
        f"You can ask me about:\n"
        f"- Fee status, dues, and payment breakdown\n"
        f"- Pending and submitted assignments with solution strategies\n"
        f"- Your CGPA, GPA, and course grades\n"
        f"- Today's lecture timetable and next upcoming class\n"
        f"- Enrolled courses and professor contact info\n"
        f"- Attendance records and warnings\n"
        f"- Online quizzes, midterms, and exam dates\n"
        f"- General subject explanations and study guidance"
    )


def process_student_chat(
    student: Student,
    db: Session,
    user_message: str,
    history: Optional[List[ChatMessage]] = None
) -> Tuple[str, Optional[str]]:
    """
    Orchestrates context retrieval, system prompt formatting, multi-provider LLM calling, and fallback.
    Returns: (response_text, provider_name)
    """
    # 1. Retrieve dynamic student context from real database
    hist_dicts = [{"role": h.role, "content": h.content} for h in (history or [])]
    context = build_dynamic_student_context(student, db, user_message, hist_dicts)

    context_json = json.dumps(context, indent=2, default=str)

    system_prompt = f"""You are the official Autonomous AI Campus Agent and Academic Assistant for the University of Haripur (UoH), serving the student '{student.first_name} {student.last_name}' ({student.program}, Semester {student.semester}).

YOU HAVE FULL READ ACCESS TO THE STUDENT'S LIVE DATABASE RECORDS. ACT AS AN AUTONOMOUS AGENT:
1. NEVER tell the student to "check your student portal" or "contact the student services office" for their fee, timetable, grades, attendance, or assignments. YOU ARE THEIR PORTAL AGENT. Answer them directly with the exact facts and figures from the verified database records below.
2. If the student asks about fee status ("my fee status tell me?", "fee dues", "challan"):
   - Read the 'fee_status' object from the database records.
   - Tell them their payment status (Paid/Unpaid/Partial), total fee, paid amount, remaining balance, due date, and receipt/transaction ID.
3. If the student asks about assignments ("how can i solve my assignments?", "my assignments details", "pendings"):
   - Look at the 'assignments' or 'live_summary.pending_assignment_titles'.
   - List their pending assignments (title, course, deadline, marks).
   - If they ask how to solve them, provide practical academic guidance, core concepts, and step-by-step problem-solving tips for those specific subjects.
4. If the student asks follow-up or shorthand questions (e.g. "pendings", "fees", "how to improve?"), understand the conversational context from the conversation history and the live database snapshot.
5. For general knowledge, coding, math, history, or science questions, answer accurately and informatively like an expert tutor.
6. Address the student warmly as '{student.first_name}'.

VERIFIED STUDENT DATABASE RECORDS (GROUND TRUTH):
```json
{context_json}
```
"""

    # 3. Format message history for LLM
    formatted_messages: List[Dict[str, str]] = []
    if history:
        for msg in history[-6:]:  # Keep recent turns for context window efficiency
            formatted_messages.append({"role": msg.role, "content": msg.content})

    formatted_messages.append({"role": "user", "content": user_message})

    # 4. Attempt generation via multi-provider manager
    ai_response, provider = provider_manager.generate_chat(system_prompt, formatted_messages)

    if ai_response:
        return ai_response, provider

    # 5. If all configured LLM providers fail or none configured, use direct database engine
    logger.info("Falling back to direct database ground-truth response generator.")
    direct_response = generate_direct_database_response(student, user_message, context)
    return direct_response, "Local Database Assistant"
