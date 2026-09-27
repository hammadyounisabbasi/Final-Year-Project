"""Expand each course timetable according to its credit-hour teaching load."""

from sqlalchemy import text

from app.core.database import engine


def _weekly_sessions(credit_hours: int) -> int:
    # 4-credit courses have three lectures and one lab; other courses receive
    # one one-hour teaching session for each credit hour.
    return 4 if credit_hours == 4 else credit_hours


def ensure_weekly_session_counts() -> None:
    with engine.begin() as connection:
        courses = connection.execute(text("""
            SELECT cs.course_id, cs.academic_year, cs.semester, cs.section,
                   c.credit_hours
            FROM Class_Schedules cs JOIN Courses c ON c.course_id=cs.course_id
            WHERE cs.status='Active'
            GROUP BY cs.course_id, cs.academic_year, cs.semester, cs.section
        """)).mappings().all()
        for course in courses:
            schedules = connection.execute(text("""
                SELECT schedule_id, teacher_id, room_location
                FROM Class_Schedules
                WHERE course_id=:course_id AND academic_year=:academic_year
                  AND semester=:semester AND section=:section AND status='Active'
                ORDER BY schedule_id
            """), course).mappings().all()
            target = _weekly_sessions(course["credit_hours"])
            template = schedules[0]
            # Cancelled placeholders bypass the insert overlap guard.  They
            # become Active together before the normalizer assigns final slots.
            for position in range(len(schedules), target):
                connection.execute(text("""
                    INSERT INTO Class_Schedules
                    (course_id, teacher_id, academic_year, semester, section,
                     day_of_week, start_time, end_time, room_location, class_type, status)
                    VALUES (:course_id, :teacher_id, :academic_year, :semester, :section,
                            'Sunday', :start_time, :end_time, :room_location, :class_type, 'Cancelled')
                """), {
                    **course,
                    "teacher_id": template["teacher_id"],
                    "room_location": template["room_location"],
                    "start_time": f"0{position}:00",
                    "end_time": f"0{position + 1}:00",
                    "class_type": "Lab" if course["credit_hours"] == 4 and position == target - 1 else "Lecture",
                })
            connection.execute(text("""
                UPDATE Class_Schedules
                SET class_type = CASE
                    WHEN :credit_hours = 4 AND schedule_id = (
                        SELECT MAX(schedule_id) FROM Class_Schedules
                        WHERE course_id=:course_id AND academic_year=:academic_year
                          AND semester=:semester AND section=:section AND status IN ('Active', 'Cancelled')
                    ) THEN 'Lab'
                    ELSE 'Lecture'
                END,
                status='Active', updated_at=CURRENT_TIMESTAMP
                WHERE course_id=:course_id AND academic_year=:academic_year
                  AND semester=:semester AND section=:section AND status IN ('Active', 'Cancelled')
            """), course)
