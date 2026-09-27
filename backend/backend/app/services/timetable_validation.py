"""Authoritative validation for data-driven timetable drafts.

AI output and UI edits must both pass this service.  It returns structured
issues and never mutates or publishes timetable records.
"""
from collections import defaultdict
import re

from app.models.class_schedule import ClassSchedule
from app.models.enrollment import Enrollment
from app.models.timetable import RoomAvailability, TeacherAvailability, Timetable, TimetableSession


TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


def time_minutes(value: str) -> int:
    if not isinstance(value, str) or not TIME_PATTERN.fullmatch(value):
        raise ValueError("Time must use HH:MM")
    hour, minute = (int(part) for part in value.split(":"))
    return hour * 60 + minute


def overlaps(left_start: str, left_end: str, right_start: str, right_end: str) -> bool:
    return time_minutes(left_start) < time_minutes(right_end) and time_minutes(left_end) > time_minutes(right_start)


def default_weekly_sessions(credit_hours: int) -> int:
    """Credit hours supply a default; TimetableCourse.weekly_sessions wins."""
    return max(1, int(credit_hours))


def _issue(code, message, session_ids=(), course_ids=()):
    return {
        "code": code,
        "message": message,
        "session_ids": sorted(set(session_ids)),
        "course_ids": sorted(set(course_ids)),
    }


def validate_timetable(db, timetable: Timetable) -> list[dict]:
    """Validate one complete draft/approved timetable without changing it."""
    issues = []
    configuration = timetable.configuration
    working_days = set(configuration.working_day_list)
    if not working_days:
        issues.append(_issue("working_days_missing", "At least one working day must be configured."))

    try:
        opening = time_minutes(configuration.day_start_time)
        closing = time_minutes(configuration.day_end_time)
        if opening >= closing:
            issues.append(_issue("working_hours_invalid", "Configured day start must be before day end."))
    except ValueError as error:
        opening = closing = None
        issues.append(_issue("working_hours_invalid", str(error)))

    course_rows = list(timetable.courses)
    sessions = [session for item in course_rows for session in item.sessions]
    for item in course_rows:
        if item.course.status != "Active":
            issues.append(_issue("course_inactive", f"{item.course.course_code} is not active.", course_ids=[item.course_id]))
        if item.teacher.status != "Active":
            issues.append(_issue("teacher_inactive", f"The teacher assigned to {item.course.course_code} is not active.", course_ids=[item.course_id]))
        if len(item.sessions) != item.weekly_sessions:
            issues.append(_issue(
                "weekly_session_count",
                f"{item.course.course_code} requires {item.weekly_sessions} weekly session(s), but has {len(item.sessions)}.",
                [row.timetable_session_id for row in item.sessions],
                [item.course_id],
            ))

    availability, room_availability = defaultdict(list), defaultdict(list)
    teacher_ids = {item.teacher_id for item in course_rows}
    if teacher_ids:
        for window in db.query(TeacherAvailability).filter(TeacherAvailability.teacher_id.in_(teacher_ids)).all():
            availability[(window.teacher_id, window.day_of_week)].append(window)
    room_ids = {session.room_id for session in sessions}
    if room_ids:
        for window in db.query(RoomAvailability).filter(RoomAvailability.room_id.in_(room_ids)).all():
            room_availability[(window.room_id, window.day_of_week)].append(window)

    academic_year = timetable.term.academic_year
    cohort_size = db.query(Enrollment.student_id).filter(
        Enrollment.course_id.in_([item.course_id for item in course_rows] or [-1]),
        Enrollment.academic_year == academic_year,
        Enrollment.semester == timetable.semester,
        Enrollment.section == timetable.section,
        Enrollment.enrollment_status == "Enrolled",
    ).distinct().count()

    for session in sessions:
        item = session.timetable_course
        session_id = session.timetable_session_id
        try:
            start, end = time_minutes(session.start_time), time_minutes(session.end_time)
            if start >= end:
                issues.append(_issue("session_time_invalid", "Session start must be before its end.", [session_id], [item.course_id]))
            if opening is not None and (start < opening or end > closing):
                issues.append(_issue("outside_working_hours", f"{item.course.course_code} is outside configured working hours.", [session_id], [item.course_id]))
            if end - start != item.session_duration_minutes:
                issues.append(_issue("duration_mismatch", f"{item.course.course_code} session duration does not match its configured duration.", [session_id], [item.course_id]))
        except ValueError as error:
            issues.append(_issue("session_time_invalid", str(error), [session_id], [item.course_id]))

        if session.day_of_week not in working_days:
            issues.append(_issue("working_day_invalid", f"{session.day_of_week} is not a configured working day.", [session_id], [item.course_id]))
        if session.room.status != "Active":
            issues.append(_issue("room_inactive", f"Room {session.room.room_code} is inactive.", [session_id], [item.course_id]))
        if session.room.room_type != item.required_room_type:
            issues.append(_issue("room_type", f"{item.course.course_code} requires {item.required_room_type}, not {session.room.room_type}.", [session_id], [item.course_id]))
        if cohort_size and session.room.capacity < cohort_size:
            issues.append(_issue("room_capacity", f"Room {session.room.room_code} seats {session.room.capacity}; the cohort has {cohort_size} enrolled students.", [session_id], [item.course_id]))

        eligible_room_ids = {choice.room_id for choice in item.eligible_rooms}
        if session.room_id not in eligible_room_ids:
            issues.append(_issue("room_not_eligible", f"Room {session.room.room_code} was not selected as eligible for {item.course.course_code}.", [session_id], [item.course_id]))
        windows = availability[(item.teacher_id, session.day_of_week)]
        if windows:
            positive = [window for window in windows if window.is_available]
            allowed = not positive or any(window.start_time <= session.start_time and window.end_time >= session.end_time for window in positive)
            blocked = any(not window.is_available and overlaps(session.start_time, session.end_time, window.start_time, window.end_time) for window in windows)
            if not allowed or blocked:
                issues.append(_issue("teacher_unavailable", f"The assigned teacher is unavailable for {item.course.course_code} at this time.", [session_id], [item.course_id]))
        windows = room_availability[(session.room_id, session.day_of_week)]
        if windows:
            positive = [window for window in windows if window.is_available]
            allowed = not positive or any(window.start_time <= session.start_time and window.end_time >= session.end_time for window in positive)
            blocked = any(not window.is_available and overlaps(session.start_time, session.end_time, window.start_time, window.end_time) for window in windows)
            if not allowed or blocked:
                issues.append(_issue("room_unavailable", f"Room {session.room.room_code} is unavailable at this time.", [session_id], [item.course_id]))

    for index, left in enumerate(sessions):
        for right in sessions[index + 1:]:
            if left.day_of_week != right.day_of_week or not overlaps(left.start_time, left.end_time, right.start_time, right.end_time):
                continue
            left_course, right_course = left.timetable_course, right.timetable_course
            ids = [left.timetable_session_id, right.timetable_session_id]
            course_ids = [left_course.course_id, right_course.course_id]
            if left_course.teacher_id == right_course.teacher_id:
                issues.append(_issue("teacher_conflict", "A teacher has overlapping sessions.", ids, course_ids))
            if left.room_id == right.room_id:
                issues.append(_issue("room_conflict", "A room has overlapping sessions.", ids, course_ids))
            # Every course within one Timetable belongs to the same department,
            # semester and section cohort.
            issues.append(_issue("cohort_conflict", "The student cohort has overlapping sessions.", ids, course_ids))

    # Published timetables outside this aggregate still reserve teachers/rooms.
    external = db.query(TimetableSession).join(TimetableSession.timetable_course).join(Timetable).filter(
        Timetable.timetable_id != timetable.timetable_id,
        Timetable.term_id == timetable.term_id,
        Timetable.status == "Published",
    ).all()
    for session in sessions:
        for other in external:
            if session.day_of_week != other.day_of_week or not overlaps(session.start_time, session.end_time, other.start_time, other.end_time):
                continue
            if session.room_id == other.room_id:
                issues.append(_issue("published_room_conflict", "The room is occupied by a published timetable.", [session.timetable_session_id], [session.timetable_course.course_id]))
            if session.timetable_course.teacher_id == other.timetable_course.teacher_id:
                issues.append(_issue("published_teacher_conflict", "The teacher is occupied by a published timetable.", [session.timetable_session_id], [session.timetable_course.course_id]))
            other_timetable = other.timetable_course.timetable
            if (timetable.department_id, timetable.semester, timetable.section) == (other_timetable.department_id, other_timetable.semester, other_timetable.section):
                issues.append(_issue("published_cohort_conflict", "The cohort is occupied by a published timetable.", [session.timetable_session_id], [session.timetable_course.course_id]))

    selected_course_ids = {item.course_id for item in course_rows}
    legacy = db.query(ClassSchedule).filter(ClassSchedule.status == "Active", ClassSchedule.academic_year == academic_year).all()
    legacy = [row for row in legacy if not (row.course_id in selected_course_ids and row.semester == timetable.semester and row.section == timetable.section)]
    legacy_students = defaultdict(set)
    for enrollment in db.query(Enrollment).filter(Enrollment.enrollment_status == "Enrolled", Enrollment.academic_year == academic_year).all():
        legacy_students[(enrollment.course_id, enrollment.semester, enrollment.section)].add(enrollment.student_id)
    room_codes = {session.room_id: session.room.room_code.strip().casefold() for session in sessions}
    cohort_students = {student_id for student_id, in db.query(Enrollment.student_id).filter(
        Enrollment.course_id.in_(selected_course_ids or [-1]), Enrollment.academic_year == academic_year,
        Enrollment.semester == timetable.semester, Enrollment.section == timetable.section,
        Enrollment.enrollment_status == "Enrolled",
    ).distinct().all()}
    for session in sessions:
        for other in legacy:
            if session.day_of_week != other.day_of_week or not overlaps(session.start_time, session.end_time, other.start_time, other.end_time):
                continue
            if session.timetable_course.teacher_id == other.teacher_id:
                issues.append(_issue("legacy_teacher_conflict", "The teacher is occupied by an existing schedule.", [session.timetable_session_id], [session.timetable_course.course_id]))
            if room_codes[session.room_id] == other.room_location.strip().casefold():
                issues.append(_issue("legacy_room_conflict", "The room is occupied by an existing schedule.", [session.timetable_session_id], [session.timetable_course.course_id]))
            if cohort_students & legacy_students[(other.course_id, other.semester, other.section)]:
                issues.append(_issue("legacy_student_conflict", "An enrolled student is occupied by an existing schedule.", [session.timetable_session_id], [session.timetable_course.course_id]))

    unique = {}
    for issue in issues:
        key = (issue["code"], issue["message"], tuple(issue["session_ids"]), tuple(issue["course_ids"]))
        unique[key] = issue
    return list(unique.values())


def assert_timetable_valid(db, timetable: Timetable):
    issues = validate_timetable(db, timetable)
    if issues:
        raise ValueError({"message": "Timetable validation failed", "issues": issues})
