-- Fill timetable coverage from the only authoritative input available here:
-- the assigned teacher's existing course schedule.  A separate row is kept
-- for each academic year/section, so historical and current terms never
-- overwrite each other.
PRAGMA foreign_keys = ON;

DROP TRIGGER IF EXISTS trg_class_schedule_prevent_teacher_overlap;
DROP TRIGGER IF EXISTS trg_student_timetable_prevent_student_overlap;
DROP TRIGGER IF EXISTS trg_student_timetable_after_enrollment_insert;
DROP TRIGGER IF EXISTS trg_student_timetable_after_enrollment_update;
DROP TRIGGER IF EXISTS trg_student_timetable_after_schedule_insert;
DROP TRIGGER IF EXISTS trg_student_timetable_after_schedule_update;

-- Clone an existing teacher-owned template only where an enrolled course has
-- no schedule for that exact academic year and section.
INSERT OR IGNORE INTO Class_Schedules
    (course_id, teacher_id, academic_year, semester, section, day_of_week,
     start_time, end_time, room_location, class_type, status)
SELECT DISTINCT source.course_id, source.teacher_id, e.academic_year,
       e.semester, e.section, source.day_of_week, source.start_time,
       source.end_time, source.room_location, source.class_type, 'Active'
FROM Enrollments e
JOIN Courses c ON c.course_id = e.course_id AND c.teacher_id IS NOT NULL
JOIN Class_Schedules source
  ON source.course_id = e.course_id AND source.teacher_id = c.teacher_id
 AND source.section = e.section AND source.status = 'Active'
WHERE e.enrollment_status NOT IN ('Dropped', 'Withdrawn')
  AND NOT EXISTS (
    SELECT 1 FROM Class_Schedules current
    WHERE current.course_id = e.course_id AND current.academic_year = e.academic_year
      AND current.semester = e.semester AND current.section = e.section
      AND current.status = 'Active'
  );

-- Include current and completed terms, but never dropped/withdrawn records.
INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
SELECT e.student_id, e.enrollment_id, cs.schedule_id
FROM Enrollments e
JOIN Class_Schedules cs ON cs.course_id=e.course_id AND cs.academic_year=e.academic_year
 AND cs.semester=e.semester AND cs.section=e.section AND cs.status='Active'
JOIN Courses c ON c.course_id=cs.course_id AND c.teacher_id=cs.teacher_id
WHERE e.enrollment_status NOT IN ('Dropped', 'Withdrawn');

CREATE TRIGGER trg_student_timetable_after_enrollment_insert
AFTER INSERT ON Enrollments
WHEN NEW.enrollment_status NOT IN ('Dropped', 'Withdrawn')
BEGIN
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT NEW.student_id, NEW.enrollment_id, cs.schedule_id
  FROM Class_Schedules cs JOIN Courses c ON c.course_id=cs.course_id
  WHERE cs.course_id=NEW.course_id AND cs.academic_year=NEW.academic_year
    AND cs.semester=NEW.semester AND cs.section=NEW.section AND cs.status='Active'
    AND cs.teacher_id=c.teacher_id;
END;

CREATE TRIGGER trg_student_timetable_after_enrollment_update
AFTER UPDATE OF student_id, course_id, academic_year, semester, section, enrollment_status ON Enrollments
BEGIN
  DELETE FROM Student_Timetable WHERE enrollment_id=NEW.enrollment_id;
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT NEW.student_id, NEW.enrollment_id, cs.schedule_id
  FROM Class_Schedules cs JOIN Courses c ON c.course_id=cs.course_id
  WHERE NEW.enrollment_status NOT IN ('Dropped', 'Withdrawn') AND cs.course_id=NEW.course_id
    AND cs.academic_year=NEW.academic_year AND cs.semester=NEW.semester
    AND cs.section=NEW.section AND cs.status='Active' AND cs.teacher_id=c.teacher_id;
END;

CREATE TRIGGER trg_student_timetable_after_schedule_insert
AFTER INSERT ON Class_Schedules WHEN NEW.status='Active'
BEGIN
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT e.student_id, e.enrollment_id, NEW.schedule_id FROM Enrollments e JOIN Courses c ON c.course_id=NEW.course_id
  WHERE e.course_id=NEW.course_id AND e.academic_year=NEW.academic_year AND e.semester=NEW.semester
    AND e.section=NEW.section AND e.enrollment_status NOT IN ('Dropped', 'Withdrawn') AND NEW.teacher_id=c.teacher_id;
END;

CREATE TRIGGER trg_student_timetable_after_schedule_update
AFTER UPDATE OF course_id, teacher_id, academic_year, semester, section, status ON Class_Schedules
BEGIN
  DELETE FROM Student_Timetable WHERE schedule_id=NEW.schedule_id;
  INSERT OR IGNORE INTO Student_Timetable (student_id, enrollment_id, schedule_id)
  SELECT e.student_id, e.enrollment_id, NEW.schedule_id FROM Enrollments e JOIN Courses c ON c.course_id=NEW.course_id
  WHERE NEW.status='Active' AND e.course_id=NEW.course_id AND e.academic_year=NEW.academic_year
    AND e.semester=NEW.semester AND e.section=NEW.section AND e.enrollment_status NOT IN ('Dropped', 'Withdrawn') AND NEW.teacher_id=c.teacher_id;
END;

CREATE TRIGGER trg_class_schedule_prevent_teacher_overlap
BEFORE INSERT ON Class_Schedules
WHEN NEW.status='Active' AND EXISTS (
  SELECT 1 FROM Class_Schedules cs WHERE cs.teacher_id=NEW.teacher_id
    AND cs.academic_year=NEW.academic_year AND cs.status='Active' AND cs.day_of_week=NEW.day_of_week
    AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
)
BEGIN SELECT RAISE(ABORT, 'Teacher already has an active class in this time slot'); END;
