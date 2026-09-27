-- Student timetable is a link table, not a second copy of class details.
-- Class_Schedules remains the single source of truth for time, room and teacher.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Student_Timetable (
    student_timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES Students(student_id) ON DELETE CASCADE,
    enrollment_id INTEGER NOT NULL REFERENCES Enrollments(enrollment_id) ON DELETE CASCADE,
    schedule_id INTEGER NOT NULL REFERENCES Class_Schedules(schedule_id) ON DELETE CASCADE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(enrollment_id, schedule_id)
);

CREATE INDEX IF NOT EXISTS idx_student_timetable_student
    ON Student_Timetable(student_id, schedule_id);
CREATE INDEX IF NOT EXISTS idx_student_timetable_enrollment
    ON Student_Timetable(enrollment_id);

-- Create links for existing active enrolments.  The teacher must match the
-- course owner, preventing an unrelated teacher's class from being exposed.
INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
SELECT e.student_id, e.enrollment_id, cs.schedule_id
FROM Enrollments AS e
JOIN Class_Schedules AS cs
  ON cs.course_id = e.course_id
 AND cs.academic_year = e.academic_year
 AND cs.semester = e.semester
 AND cs.section = e.section
 AND cs.status = 'Active'
JOIN Courses AS c ON c.course_id = cs.course_id
WHERE e.enrollment_status = 'Enrolled'
  AND cs.teacher_id = c.teacher_id;

CREATE TRIGGER IF NOT EXISTS trg_student_timetable_after_enrollment_insert
AFTER INSERT ON Enrollments
WHEN NEW.enrollment_status = 'Enrolled'
BEGIN
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT NEW.student_id, NEW.enrollment_id, cs.schedule_id
  FROM Class_Schedules cs JOIN Courses c ON c.course_id = cs.course_id
  WHERE cs.course_id = NEW.course_id AND cs.academic_year = NEW.academic_year
    AND cs.semester = NEW.semester AND cs.section = NEW.section
    AND cs.status = 'Active' AND cs.teacher_id = c.teacher_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_student_timetable_after_enrollment_update
AFTER UPDATE OF student_id, course_id, academic_year, semester, section, enrollment_status ON Enrollments
BEGIN
  DELETE FROM Student_Timetable WHERE enrollment_id = NEW.enrollment_id;
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT NEW.student_id, NEW.enrollment_id, cs.schedule_id
  FROM Class_Schedules cs JOIN Courses c ON c.course_id = cs.course_id
  WHERE NEW.enrollment_status = 'Enrolled' AND cs.course_id = NEW.course_id
    AND cs.academic_year = NEW.academic_year AND cs.semester = NEW.semester
    AND cs.section = NEW.section AND cs.status = 'Active' AND cs.teacher_id = c.teacher_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_student_timetable_after_schedule_insert
AFTER INSERT ON Class_Schedules
WHEN NEW.status = 'Active'
BEGIN
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT e.student_id, e.enrollment_id, NEW.schedule_id
  FROM Enrollments e JOIN Courses c ON c.course_id = NEW.course_id
  WHERE e.course_id = NEW.course_id AND e.academic_year = NEW.academic_year
    AND e.semester = NEW.semester AND e.section = NEW.section
    AND e.enrollment_status = 'Enrolled' AND NEW.teacher_id = c.teacher_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_student_timetable_after_schedule_update
AFTER UPDATE OF course_id, teacher_id, academic_year, semester, section, status ON Class_Schedules
BEGIN
  DELETE FROM Student_Timetable WHERE schedule_id = NEW.schedule_id;
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT e.student_id, e.enrollment_id, NEW.schedule_id
  FROM Enrollments e JOIN Courses c ON c.course_id = NEW.course_id
  WHERE NEW.status = 'Active' AND e.course_id = NEW.course_id
    AND e.academic_year = NEW.academic_year AND e.semester = NEW.semester
    AND e.section = NEW.section AND e.enrollment_status = 'Enrolled'
    AND NEW.teacher_id = c.teacher_id;
END;

-- Reject future double-bookings while retaining existing records for review.
CREATE TRIGGER IF NOT EXISTS trg_class_schedule_prevent_teacher_overlap
BEFORE INSERT ON Class_Schedules
WHEN NEW.status = 'Active' AND EXISTS (
  SELECT 1 FROM Class_Schedules cs
  WHERE cs.teacher_id = NEW.teacher_id AND cs.status = 'Active'
    AND cs.day_of_week = NEW.day_of_week
    AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
)
BEGIN
  SELECT RAISE(ABORT, 'Teacher already has an active class in this time slot');
END;

CREATE TRIGGER IF NOT EXISTS trg_student_timetable_prevent_student_overlap
BEFORE INSERT ON Student_Timetable
WHEN EXISTS (
  SELECT 1
  FROM Student_Timetable existing
  JOIN Class_Schedules current_schedule ON current_schedule.schedule_id = NEW.schedule_id
  JOIN Class_Schedules existing_schedule ON existing_schedule.schedule_id = existing.schedule_id
  WHERE existing.student_id = NEW.student_id
    AND current_schedule.day_of_week = existing_schedule.day_of_week
    AND current_schedule.start_time < existing_schedule.end_time
    AND current_schedule.end_time > existing_schedule.start_time
)
BEGIN
  SELECT RAISE(ABORT, 'Student already has an active class in this time slot');
END;
