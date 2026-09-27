"""Canonical timetable integrity helpers shared by publication routes."""

from fastapi import HTTPException

from app.models.class_schedule import ClassSchedule
from app.models.enrollment import Enrollment
from app.models.student_timetable import StudentTimetable


def overlapping(left_start: str, left_end: str, right_start: str, right_end: str) -> bool:
    return left_start < right_end and left_end > right_start


def assert_schedule_is_available(db, schedule: ClassSchedule) -> None:
    """Reject a teacher, room, or enrolled-student double booking."""
    active = db.query(ClassSchedule).filter(
        ClassSchedule.status == "Active",
        ClassSchedule.academic_year == schedule.academic_year,
        ClassSchedule.day_of_week == schedule.day_of_week,
    ).all()
    candidate_students = {
        student_id for student_id, in db.query(Enrollment.student_id).filter(
            Enrollment.course_id == schedule.course_id,
            Enrollment.academic_year == schedule.academic_year,
            Enrollment.semester == schedule.semester,
            Enrollment.section == schedule.section,
            Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
        ).all()
    }
    for other in active:
        if other.schedule_id == schedule.schedule_id or not overlapping(schedule.start_time, schedule.end_time, other.start_time, other.end_time):
            continue
        if other.teacher_id == schedule.teacher_id:
            raise HTTPException(409, "Teacher already has an active class in this time slot")
        if other.room_location.casefold() == schedule.room_location.casefold():
            raise HTTPException(409, "Room is already booked in this time slot")
        if candidate_students:
            other_students = {
                student_id for student_id, in db.query(Enrollment.student_id).filter(
                    Enrollment.course_id == other.course_id,
                    Enrollment.academic_year == other.academic_year,
                    Enrollment.semester == other.semester,
                    Enrollment.section == other.section,
                    Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
                ).all()
            }
            if candidate_students.intersection(other_students):
                raise HTTPException(409, "An enrolled student already has an active class in this time slot")


def sync_student_timetable(db, schedule: ClassSchedule) -> int:
    """Link every eligible enrollment to its canonical schedule row."""
    if schedule.status != "Active":
        return 0
    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == schedule.course_id,
        Enrollment.academic_year == schedule.academic_year,
        Enrollment.semester == schedule.semester,
        Enrollment.section == schedule.section,
        Enrollment.enrollment_status.notin_(["Dropped", "Withdrawn"]),
    ).all()
    existing_ids = {enrollment_id for enrollment_id, in db.query(StudentTimetable.enrollment_id).filter(StudentTimetable.schedule_id == schedule.schedule_id).all()}
    added = 0
    for enrollment in enrollments:
        if enrollment.enrollment_id not in existing_ids:
            db.add(StudentTimetable(student_id=enrollment.student_id, enrollment_id=enrollment.enrollment_id, schedule_id=schedule.schedule_id))
            added += 1
    return added
