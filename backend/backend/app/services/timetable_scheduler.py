"""Deterministic constraint scheduler for persisted timetable drafts."""
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import joinedload

from app.models import ClassSchedule, Course, Enrollment
from app.models.timetable import RoomAvailability, TeacherAvailability, Timetable, TimetableSession
from app.services.timetable_validation import overlaps, time_minutes, validate_timetable


def hhmm(minutes):
    return f"{minutes // 60:02}:{minutes % 60:02}"


@dataclass(frozen=True)
class Candidate:
    timetable_course_id: int
    course_id: int
    teacher_id: int
    room_id: int
    day: str
    start: str
    end: str


def _availability_ok(windows, entity_id, day, start, end):
    matches = windows.get((entity_id, day), [])
    if not matches:
        return True
    positive = [row for row in matches if row.is_available]
    allowed = not positive or any(row.start_time <= start and row.end_time >= end for row in positive)
    blocked = any(not row.is_available and overlaps(start, end, row.start_time, row.end_time) for row in matches)
    return allowed and not blocked


def _cohort_student_ids(db, timetable):
    return {student_id for student_id, in db.query(Enrollment.student_id).filter(
        Enrollment.course_id.in_([row.course_id for row in timetable.courses] or [-1]),
        Enrollment.academic_year == timetable.term.academic_year,
        Enrollment.semester == timetable.semester,
        Enrollment.section == timetable.section,
        Enrollment.enrollment_status == "Enrolled",
    ).distinct().all()}


def generate_timetable(db, timetable: Timetable):
    if timetable.status != "Draft":
        return {"success": False, "conflicts": [{"reason": "Only draft timetables can be generated.", "possible_adjustment": "Create or return to a draft before generating."}]}
    configuration = timetable.configuration
    days = configuration.working_day_list
    opening, closing = time_minutes(configuration.day_start_time), time_minutes(configuration.day_end_time)
    teacher_ids = {row.teacher_id for row in timetable.courses}
    room_ids = {choice.room_id for row in timetable.courses for choice in row.eligible_rooms}
    teacher_windows, room_windows = defaultdict(list), defaultdict(list)
    for row in db.query(TeacherAvailability).filter(TeacherAvailability.teacher_id.in_(teacher_ids or [-1])).all():
        teacher_windows[(row.teacher_id, row.day_of_week)].append(row)
    for row in db.query(RoomAvailability).filter(RoomAvailability.room_id.in_(room_ids or [-1])).all():
        room_windows[(row.room_id, row.day_of_week)].append(row)

    cohort_students = _cohort_student_ids(db, timetable)
    cohort_size = len(cohort_students)
    selected_course_ids = {row.course_id for row in timetable.courses}
    legacy = db.query(ClassSchedule).filter(ClassSchedule.status == "Active", ClassSchedule.academic_year == timetable.term.academic_year).all()
    # Exact legacy rows in this scope are replacement candidates. Other legacy
    # rows remain reservations and are never silently overwritten.
    legacy = [row for row in legacy if not (row.course_id in selected_course_ids and row.semester == timetable.semester and row.section == timetable.section)]
    legacy_students = defaultdict(set)
    for enrollment in db.query(Enrollment).filter(Enrollment.enrollment_status == "Enrolled", Enrollment.academic_year == timetable.term.academic_year).all():
        legacy_students[(enrollment.course_id, enrollment.semester, enrollment.section)].add(enrollment.student_id)

    external = db.query(TimetableSession).join(TimetableSession.timetable_course).join(Timetable).options(joinedload(TimetableSession.timetable_course)).filter(
        Timetable.timetable_id != timetable.timetable_id,
        Timetable.term_id == timetable.term_id,
        Timetable.status == "Published",
    ).all()
    staged = []
    course_day_counts, teacher_day_counts, cohort_day_counts = defaultdict(int), defaultdict(int), defaultdict(int)
    failures = []

    def conflict(candidate):
        for other in staged:
            if candidate.day != other.day or not overlaps(candidate.start, candidate.end, other.start, other.end):
                continue
            if candidate.teacher_id == other.teacher_id:
                return "teacher is already assigned to another generated session"
            if candidate.room_id == other.room_id:
                return "selected room is already assigned to another generated session"
            return "the student cohort already has another generated session"
        for other in external:
            if candidate.day != other.day_of_week or not overlaps(candidate.start, candidate.end, other.start_time, other.end_time):
                continue
            if candidate.teacher_id == other.timetable_course.teacher_id:
                return "teacher is occupied by a published timetable"
            if candidate.room_id == other.room_id:
                return "room is occupied by a published timetable"
        for other in legacy:
            if candidate.day != other.day_of_week or not overlaps(candidate.start, candidate.end, other.start_time, other.end_time):
                continue
            if candidate.teacher_id == other.teacher_id:
                return "teacher is occupied by an existing legacy schedule"
            room = next((choice.room for item in timetable.courses for choice in item.eligible_rooms if choice.room_id == candidate.room_id), None)
            if room and room.room_code.strip().casefold() == other.room_location.strip().casefold():
                return "room is occupied by an existing legacy schedule"
            if cohort_students & legacy_students[(other.course_id, other.semester, other.section)]:
                return "an enrolled student is occupied by an existing schedule"
        return None

    ordered = sorted(timetable.courses, key=lambda row: (len(row.eligible_rooms), -row.session_duration_minutes, -row.weekly_sessions, row.course.course_code))
    for item in ordered:
        rooms = sorted((choice.room for choice in item.eligible_rooms if choice.room.status == "Active" and choice.room.room_type == item.required_room_type and choice.room.capacity >= max(1, cohort_size)), key=lambda room: (room.capacity, room.room_code))
        if item.course.status != "Active" or item.teacher.status != "Active":
            failures.append({"course": item.course.course_code, "teacher": f"{item.teacher.first_name} {item.teacher.last_name}", "cohort": f"Semester {timetable.semester} Section {timetable.section}", "reason": "course or assigned teacher is inactive", "possible_adjustment": "Select an active course and teacher."})
            continue
        if not rooms:
            failures.append({"course": item.course.course_code, "teacher": f"{item.teacher.first_name} {item.teacher.last_name}", "cohort": f"Semester {timetable.semester} Section {timetable.section}", "reason": f"no active {item.required_room_type} has capacity for {cohort_size} enrolled students", "possible_adjustment": "Select a larger compatible room or correct room capacity/type."})
            continue
        for meeting in range(item.weekly_sessions):
            choices = []
            for day_index, day in enumerate(days):
                for start_minute in range(opening, closing - item.session_duration_minutes + 1, configuration.slot_minutes):
                    end_minute = start_minute + item.session_duration_minutes
                    start, end = hhmm(start_minute), hhmm(end_minute)
                    if not _availability_ok(teacher_windows, item.teacher_id, day, start, end):
                        continue
                    for room in rooms:
                        if not _availability_ok(room_windows, room.room_id, day, start, end):
                            continue
                        candidate = Candidate(item.timetable_course_id, item.course_id, item.teacher_id, room.room_id, day, start, end)
                        reason = conflict(candidate)
                        if reason is None:
                            score = (course_day_counts[(item.course_id, day)] * 100, teacher_day_counts[(item.teacher_id, day)] * 10, cohort_day_counts[day] * 2, day_index, start_minute, room.capacity, room.room_code)
                            choices.append((score, candidate))
            if not choices:
                failures.append({"course": item.course.course_code, "teacher": f"{item.teacher.first_name} {item.teacher.last_name}", "room": ", ".join(room.room_code for room in rooms), "cohort": f"Semester {timetable.semester} Section {timetable.section}", "reason": f"session {meeting + 1} of {item.weekly_sessions} has no conflict-free eligible slot within availability and operating hours", "possible_adjustment": "Expand working hours/days, teacher availability, eligible rooms, or reduce session duration."})
                break
            candidate = min(choices, key=lambda value: value[0])[1]
            staged.append(candidate)
            course_day_counts[(item.course_id, candidate.day)] += 1
            teacher_day_counts[(item.teacher_id, candidate.day)] += 1
            cohort_day_counts[candidate.day] += 1

    if failures:
        return {"success": False, "conflicts": failures, "scheduled": len(staged), "required": sum(row.weekly_sessions for row in timetable.courses)}

    for item in timetable.courses:
        item.sessions.clear()
    db.flush()
    items_by_id = {item.timetable_course_id: item for item in timetable.courses}
    for row in staged:
        items_by_id[row.timetable_course_id].sessions.append(TimetableSession(room_id=row.room_id, day_of_week=row.day, start_time=row.start, end_time=row.end))
    db.flush()
    issues = validate_timetable(db, timetable)
    if issues:
        db.rollback()
        return {"success": False, "conflicts": [{"reason": issue["message"], "code": issue["code"], "possible_adjustment": "Review the affected course, availability, room, or time configuration."} for issue in issues]}
    db.commit()
    db.refresh(timetable)
    return {"success": True, "scheduled": len(staged), "required": len(staged), "conflicts": []}
