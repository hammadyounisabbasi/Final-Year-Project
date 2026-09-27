"""Structured, database-backed timetable analysis and draft generation.

No LLM chooses database IDs or persists records.  All output is explainable
and remains a draft until an authorised administrator approves it.
"""
from collections import defaultdict
import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session, joinedload
from app.models.class_schedule import ClassSchedule
from app.models.course import Course
from app.models.department import Department
from app.models.teacher import Teacher
from app.models.enrollment import Enrollment
from app.services.ai_providers import AIProviderManager

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SLOTS = [("08:30", "09:30"), ("09:30", "10:30"), ("10:45", "11:45"), ("11:45", "12:45"), ("13:30", "14:30"), ("14:30", "15:30")]
MAX_REFERENCE_CHARS = 16000
MAX_HISTORY_ITEMS = 20
MAX_HISTORY_CHARS = 4000


def compact_agent_context(context: dict) -> dict:
    """Keep verified facts useful to the model without sending the whole DB dump."""
    teachers = []
    for teacher in context.get("teachers", [])[:40]:
        teachers.append({
            "teacher_id": teacher["teacher_id"],
            "name": teacher["name"],
            "department": teacher["department"],
            "assigned_courses": teacher.get("assigned_courses", [])[:8],
            "weekly_sessions": teacher.get("weekly_sessions", 0),
            "current_slots": teacher.get("current_slots", [])[:8],
        })
    return {
        "scope": context.get("scope", {}),
        "teacher_count": context.get("teacher_count", 0),
        "teachers": teachers,
        "courses": context.get("courses", [])[:80],
        "active_schedule_count": context.get("active_schedule_count", 0),
        "global_active_schedule_count": context.get("global_active_schedule_count", 0),
        "available_rooms": context.get("available_rooms", []),
        "scoped_teacher_ids": context.get("scoped_teacher_ids", [])[:80],
    }


def compact_history(history: list[dict] | None) -> list[dict]:
    return [
        {"role": item["role"], "content": str(item["content"])[:MAX_HISTORY_CHARS]}
        for item in (history or [])[-MAX_HISTORY_ITEMS:]
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]


def infer_request_scope(db: Session, scope: dict, request: str) -> dict:
    """Resolve explicit department and semester phrases against live records."""
    resolved = dict(scope)
    normalized = re.sub(r"\s+", " ", request.lower().replace('-semester', ' semester')).strip()
    departments = db.query(Department).filter(Department.status == "Active").all()
    matches = []
    for department in departments:
        names = {department.department_code.lower(), (department.department_short_name or "").lower(), department.department_name.lower().replace("department of ", "")}
        full_name = department.department_name.lower().replace('department of ', '')
        acronym = ''.join(word[0] for word in re.findall(r'\w+', full_name) if word not in {'and','of','the'})
        peers = [d for d in departments if ''.join(word[0] for word in re.findall(r'\w+', d.department_name.lower().replace('department of ', '')) if word not in {'and','of','the'}) == acronym]
        preferred = [d for d in peers if d.department_code.lower().startswith(acronym)]
        if len(acronym) >= 2 and (len(peers) == 1 or (len(preferred) == 1 and preferred[0].department_id == department.department_id)):
            names.add(acronym)
        for name in sorted(names, key=lambda value: (-len(value), value)):
            if name and re.search(rf"\b{re.escape(name)}\b", normalized):
                matches.append((normalized.index(name), len(name), department))
                break
    matches.sort(key=lambda item: (item[0], -item[1]))
    if not resolved.get("department_id") and matches:
        resolved["department_id"] = matches[0][2].department_id
    ordinal = re.search(r"\b(first|1st|one|second|2nd|two|third|3rd|three|fourth|4th|four)\s+semester\b", normalized)
    if not resolved.get("semester") and ordinal:
        values = {"first": 1, "1st": 1, "one": 1, "second": 2, "2nd": 2, "two": 2, "third": 3, "3rd": 3, "three": 3, "fourth": 4, "4th": 4, "four": 4}
        resolved["semester"] = values[ordinal.group(1)]
    if len(matches) > 1 and re.search(r"\b(based on|using|from|same|as)\b", normalized):
        resolved["source_department_id"] = matches[-1][2].department_id
    elif matches and resolved.get('department_id') != matches[-1][2].department_id and re.search(r'\b(same|as|from)\b', normalized):
        resolved['source_department_id'] = matches[-1][2].department_id
    numeric = re.search(r"\bsemester\s+(\d{1,2})\b", normalized)
    if not resolved.get("semester") and numeric: resolved["semester"] = int(numeric.group(1))
    return resolved

def overlaps(left, right):
    return left.start_time < right.end_time and left.end_time > right.start_time

def scoped_schedules(db: Session, scope: dict):
    query = db.query(ClassSchedule).join(Course).join(Department).join(Teacher).options(joinedload(ClassSchedule.course).joinedload(Course.department), joinedload(ClassSchedule.teacher)).filter(ClassSchedule.status == "Active")
    if scope.get("department_id"): query = query.filter(Course.department_id == scope["department_id"])
    if scope.get("semester"): query = query.filter(ClassSchedule.semester == scope["semester"])
    if scope.get("section"): query = query.filter(ClassSchedule.section == scope["section"])
    if scope.get("teacher_id"): query = query.filter(ClassSchedule.teacher_id == scope["teacher_id"])
    if scope.get("academic_year"): query = query.filter(ClassSchedule.academic_year == scope["academic_year"])
    if scope.get("student_id"):
        query = query.join(Enrollment, (Enrollment.course_id == ClassSchedule.course_id) & (Enrollment.academic_year == ClassSchedule.academic_year) & (Enrollment.semester == ClassSchedule.semester) & (Enrollment.section == ClassSchedule.section)).filter(Enrollment.student_id == scope["student_id"], Enrollment.enrollment_status == "Enrolled")
    return query.order_by(ClassSchedule.day_of_week, ClassSchedule.start_time).all()

def serialize_schedule(s):
    return {"schedule_id":s.schedule_id, "course_id":s.course_id, "course_code":s.course.course_code, "course_title":s.course.course_title, "credit_hours":s.course.credit_hours, "department_id":s.course.department_id, "department":s.course.department.department_name, "teacher_id":s.teacher_id, "teacher":f"{s.teacher.first_name} {s.teacher.last_name}", "semester":s.semester, "section":s.section, "academic_year":s.academic_year, "day":s.day_of_week, "start_time":s.start_time, "end_time":s.end_time, "room":s.room_location, "class_type":s.class_type}


def collect_agent_context(db: Session, scope: dict) -> dict:
    """Build verified facts for the agent; this packet never contains write authority."""
    schedules = scoped_schedules(db, scope)
    all_active_schedules = db.query(ClassSchedule).filter(ClassSchedule.status == "Active").all()
    teacher_ids = {row.teacher_id for row in schedules}
    courses = db.query(Course).filter(Course.status == "Active")
    if scope.get("department_id"):
        courses = courses.filter(Course.department_id == scope["department_id"])
    if scope.get("semester"):
        courses = courses.filter(Course.semester == scope["semester"])
    course_rows = courses.order_by(Course.course_code).all()
    if scope.get("department_id") or scope.get("semester") or scope.get("section") or scope.get("student_id") or scope.get("teacher_id"):
        teacher_ids.update(course.teacher_id for course in course_rows if course.teacher_id is not None)
    teachers = db.query(Teacher).filter(Teacher.status == "Active").order_by(Teacher.first_name, Teacher.last_name).all()
    if any(scope.get(key) is not None for key in ("department_id", "semester", "section", "student_id", "teacher_id")):
        teachers = [teacher for teacher in teachers if teacher.teacher_id in teacher_ids or teacher.department_id == scope.get("department_id")]
    teacher_context = []
    for teacher in teachers:
        assigned = [course for course in teacher.courses if course.status == "Active"]
        weekly = [row for row in db.query(ClassSchedule).filter(ClassSchedule.teacher_id == teacher.teacher_id, ClassSchedule.status == "Active").all()]
        evidence_year = scope.get('academic_year') or max((row.academic_year for row in weekly), default=None)
        weekly = [row for row in weekly if row.academic_year == evidence_year]
        if scope.get("department_id") and teacher.department_id != scope["department_id"] and not assigned:
            continue
        teacher_context.append({
            "teacher_id": teacher.teacher_id,
            "name": f"{teacher.first_name} {teacher.last_name}".strip(),
            "department": teacher.department.department_name,
            "specialization": teacher.specialization,
            "assigned_courses": [{"course_id": course.course_id, "code": course.course_code, "title": course.course_title} for course in assigned],
            "weekly_sessions": len(weekly),
            "academic_year": evidence_year,
            "current_slots": [{"day": row.day_of_week, "start": row.start_time, "end": row.end_time, "course_id": row.course_id} for row in weekly],
        })
    return {
        "scope": {key: value for key, value in scope.items() if key in {"department_id", "semester", "section", "teacher_id", "student_id", "academic_year"} and value is not None},
        "teacher_count": len(teacher_context),
        "teachers": teacher_context,
        "courses": [{"course_id": course.course_id, "code": course.course_code, "title": course.course_title, "credit_hours": course.credit_hours, "semester": course.semester, "teacher_id": course.teacher_id} for course in course_rows],
        "active_schedule_count": len(schedules),
        # A zero scoped count means this target has no current entry; it must not
        # be interpreted as an empty university or an absence of planning rooms.
        "global_active_schedule_count": len(all_active_schedules),
        "available_rooms": sorted({row.room_location for row in all_active_schedules if row.room_location}),
        "scoped_teacher_ids": sorted(teacher_ids),
    }

def analyze(db: Session, scope: dict):
    schedules = scoped_schedules(db, scope)
    from app.services.timetable_constraints import ConstraintSnapshot
    snapshot = ConstraintSnapshot(db)
    issues, seen = [], set()
    for left in schedules:
        for right in snapshot.rows:
            pair = tuple(sorted((left.schedule_id, right.schedule_id)))
            if left.schedule_id == right.schedule_id or pair in seen: continue
            seen.add(pair)
            for kind in snapshot.conflicts(left,right):
                issues.append({"type":kind,"severity":"critical","message":f"{kind}: move one class to a free slot.",
                               "affected":[serialize_schedule(left),serialize_schedule(right)],
                               "department":left.course.department.department_name,"semester":left.semester,"section":left.section})
    def add(kind,severity,rows,recommendation):
        issues.append({"type":kind,"severity":severity,"message":recommendation,"affected":[serialize_schedule(x) for x in rows]})
    workloads = defaultdict(int)
    for s in snapshot.rows: workloads[(s.teacher_id,s.academic_year)] += 1
    for (teacher_id, year), count in workloads.items():
        if count > 18:
            s = next((x for x in schedules if x.teacher_id == teacher_id and x.academic_year == year), None)
            if s is None: continue
            add("Workload imbalance", "medium", [s], f"{s.teacher.first_name} {s.teacher.last_name} has {count} weekly sessions in {year}; review distribution.")
    enrollments = db.query(Enrollment, Course).join(Course).filter(Enrollment.enrollment_status == "Enrolled", Course.status == "Active")
    if scope.get("department_id"): enrollments = enrollments.filter(Course.department_id == scope["department_id"])
    if scope.get("semester"): enrollments = enrollments.filter(Enrollment.semester == scope["semester"])
    if scope.get("section"): enrollments = enrollments.filter(Enrollment.section == scope["section"])
    if scope.get("academic_year"): enrollments = enrollments.filter(Enrollment.academic_year == scope["academic_year"])
    seen = set()
    for enrollment, course in enrollments.all():
        key = (course.course_id, enrollment.academic_year, enrollment.semester, enrollment.section)
        if key in seen: continue
        seen.add(key)
        if not db.query(ClassSchedule.schedule_id).filter_by(course_id=course.course_id, academic_year=enrollment.academic_year, semester=enrollment.semester, section=enrollment.section, status="Active").first():
            issues.append({"type":"Missing timetable entry", "severity":"high", "message":f"{course.course_code} has enrolled students but no active class schedule.", "affected":[], "department":course.department.department_name, "semester":enrollment.semester, "section":enrollment.section, "recommendation":"Generate a reviewed draft using the assigned teacher and an available slot."})
    return {"summary":f"Analyzed {len(schedules)} active timetable entries and found {len(issues)} issue(s).", "issues":issues, "schedules":[serialize_schedule(s) for s in schedules], "metrics":{"active_schedules":len(schedules), "issues":len(issues), "teachers":len({s.teacher_id for s in schedules}), "rooms":len({s.room_location for s in schedules}), "global_active_schedules":len(snapshot.rows), "global_rooms":len(snapshot.rooms)}}


def generate_draft(db, scope):
    from app.services.timetable_constraints import ConstraintSnapshot
    changes, warnings = ConstraintSnapshot(db).plan(scope)
    return {**analyze(db, scope), "changes": changes, "warning": " ".join(warnings) or None}


def validate_draft(db, changes):
    from app.services.timetable_constraints import ConstraintSnapshot
    errors = ConstraintSnapshot(db).validate(changes)
    return [] if errors else changes


from app.services.timetable_agent import run_generation_workflow, run_chat_workflow
