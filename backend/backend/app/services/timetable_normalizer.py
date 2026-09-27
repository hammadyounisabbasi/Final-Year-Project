"""Keep teacher and student timetable slots conflict-free and one hour long."""

from collections import defaultdict
from datetime import datetime

from sqlalchemy import text

from app.core.database import engine


DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
# Prefer alternate-hour starts so a student's same-day sessions have a break.
START_TIMES = ("08:00", "10:00", "12:00", "14:00", "16:00", "09:00", "11:00", "13:00", "15:00")


def _needs_normalization(rows: list[dict]) -> bool:
    occupied_teachers: set[tuple[str, int, str, str]] = set()
    occupied_students: set[tuple[str, int, int, str, str]] = set()
    for row in rows:
        start = datetime.strptime(row["start_time"], "%H:%M")
        end = datetime.strptime(row["end_time"], "%H:%M")
        if (end - start).seconds != 3600:
            return True
        teacher_key = (row["academic_year"], row["teacher_id"], row["day_of_week"], row["start_time"])
        if teacher_key in occupied_teachers:
            return True
        occupied_teachers.add(teacher_key)
        for student_id in row["student_ids"].split(",") if row["student_ids"] else ():
            student_key = (row["academic_year"], row["semester"], int(student_id), row["day_of_week"], row["start_time"])
            if student_key in occupied_students:
                return True
            occupied_students.add(student_key)
    return False


def normalize_timetable(force: bool = False) -> None:
    """Assign every active class one non-overlapping one-hour weekly slot."""
    with engine.begin() as connection:
        rows = [dict(row) for row in connection.execute(text("""
            SELECT cs.schedule_id, cs.course_id, cs.academic_year, cs.semester,
                   cs.section, cs.teacher_id, cs.day_of_week, cs.start_time, cs.end_time,
                   COALESCE(GROUP_CONCAT(DISTINCT st.student_id), '') AS student_ids
            FROM Class_Schedules cs
            LEFT JOIN Student_Timetable st ON st.schedule_id = cs.schedule_id
            WHERE cs.status = 'Active'
            GROUP BY cs.schedule_id
            ORDER BY cs.academic_year, cs.teacher_id, cs.course_id, cs.schedule_id
        """)).mappings().all()]
        if not rows or (not force and not _needs_normalization(rows)):
            return

        teacher_slots: set[tuple[str, int, str, str]] = set()
        student_slots: set[tuple[str, int, int, str, str]] = set()
        course_days: defaultdict[tuple, set[str]] = defaultdict(set)
        student_day_load: defaultdict[tuple, int] = defaultdict(int)
        assignments: list[dict] = []
        for row in rows:
            student_ids = tuple(int(value) for value in row["student_ids"].split(",") if value)
            available = []
            for day in DAY_NAMES:
                for start in START_TIMES:
                    teacher_key = (row["academic_year"], row["teacher_id"], day, start)
                    if teacher_key in teacher_slots:
                        continue
                    if any((row["academic_year"], row["semester"], student_id, day, start) in student_slots for student_id in student_ids):
                        continue
                    course_key = (row["course_id"], row["academic_year"], row["semester"], row["section"])
                    student_load = sum(student_day_load[(row["academic_year"], row["semester"], student_id, day)] for student_id in student_ids)
                    # Spread a course across days first, then balance each
                    # cohort's daily load; START_TIMES preserves teaching gaps.
                    available.append((day in course_days[course_key], student_load, START_TIMES.index(start), DAY_NAMES.index(day), day, start))
            if not available:
                raise RuntimeError(f"No conflict-free timetable slot available for schedule {row['schedule_id']}")
            _, _, _, _, day, start = min(available)
            course_key = (row["course_id"], row["academic_year"], row["semester"], row["section"])
            course_days[course_key].add(day)
            teacher_slots.add((row["academic_year"], row["teacher_id"], day, start))
            for student_id in student_ids:
                student_slots.add((row["academic_year"], row["semester"], student_id, day, start))
                student_day_load[(row["academic_year"], row["semester"], student_id, day)] += 1
            assignments.append({"schedule_id": row["schedule_id"], "day": day, "start": start})

        # Move every row through a temporary unique value first.  This avoids
        # hitting the per-course unique slot constraint while two sessions swap
        # their final day/time during redistribution.
        for assignment in assignments:
            connection.execute(text("""
                UPDATE Class_Schedules
                SET day_of_week = 'Sunday', start_time = :temporary,
                    end_time = :temporary, updated_at = CURRENT_TIMESTAMP
                WHERE schedule_id = :schedule_id
            """), {"schedule_id": assignment["schedule_id"], "temporary": f"TMP-{assignment['schedule_id']}"})

        for assignment in assignments:
            start_hour = int(assignment["start"][:2])
            connection.execute(text("""
                UPDATE Class_Schedules
                SET day_of_week = :day, start_time = :start, end_time = :end,
                    updated_at = CURRENT_TIMESTAMP
                WHERE schedule_id = :schedule_id
            """), {
                **assignment,
                "end": f"{start_hour + 1:02d}:00",
            })
