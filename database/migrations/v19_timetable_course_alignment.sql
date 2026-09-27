-- Align timetable ownership with Courses.teacher_id and cover enrolled terms.
-- Class_Schedules remains the source of truth for teacher and student timetables.
PRAGMA foreign_keys = ON;

UPDATE Class_Schedules
SET teacher_id = (
    SELECT teacher_id FROM Courses
    WHERE Courses.course_id = Class_Schedules.course_id
)
WHERE EXISTS (
    SELECT 1 FROM Courses
    WHERE Courses.course_id = Class_Schedules.course_id
      AND Courses.teacher_id <> Class_Schedules.teacher_id
);

INSERT OR IGNORE INTO Class_Schedules
    (course_id, teacher_id, academic_year, semester, section, day_of_week,
     start_time, end_time, room_location, class_type, status)
SELECT DISTINCT source.course_id, c.teacher_id, e.academic_year, e.semester,
       e.section, source.day_of_week, source.start_time, source.end_time,
       source.room_location, source.class_type, 'Active'
FROM Enrollments e
JOIN Courses c ON c.course_id = e.course_id AND c.teacher_id IS NOT NULL
JOIN Class_Schedules source
  ON source.course_id = e.course_id
 AND source.teacher_id = c.teacher_id
 AND source.section = e.section
 AND source.status = 'Active'
WHERE e.enrollment_status NOT IN ('Dropped', 'Withdrawn')
  AND NOT EXISTS (
    SELECT 1 FROM Class_Schedules current
    WHERE current.course_id = e.course_id
      AND current.academic_year = e.academic_year
      AND current.semester = e.semester
      AND current.section = e.section
      AND current.status = 'Active'
  );

DELETE FROM Student_Timetable;
INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
SELECT e.student_id, e.enrollment_id, cs.schedule_id
FROM Enrollments e
JOIN Class_Schedules cs
  ON cs.course_id = e.course_id
 AND cs.academic_year = e.academic_year
 AND cs.semester = e.semester
 AND cs.section = e.section
 AND cs.status = 'Active'
JOIN Courses c ON c.course_id = cs.course_id AND c.teacher_id = cs.teacher_id
WHERE e.enrollment_status NOT IN ('Dropped', 'Withdrawn');
