-- Enforce one canonical, conflict-free timetable for teachers and students.
-- Existing Student_Timetable links remain the student portal's source of truth.
PRAGMA foreign_keys = ON;

DROP TRIGGER IF EXISTS trg_class_schedule_prevent_teacher_overlap;
DROP TRIGGER IF EXISTS trg_class_schedule_prevent_overlap_insert;
DROP TRIGGER IF EXISTS trg_class_schedule_prevent_overlap_update;

CREATE TRIGGER trg_class_schedule_prevent_overlap_insert
BEFORE INSERT ON Class_Schedules
WHEN NEW.status = 'Active'
BEGIN
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM Class_Schedules cs
    WHERE cs.status = 'Active' AND cs.academic_year = NEW.academic_year
      AND cs.day_of_week = NEW.day_of_week
      AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
      AND cs.teacher_id = NEW.teacher_id
  ) THEN RAISE(ABORT, 'Teacher already has an active class in this time slot') END;

  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM Class_Schedules cs
    WHERE cs.status = 'Active' AND cs.academic_year = NEW.academic_year
      AND cs.day_of_week = NEW.day_of_week
      AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
      AND lower(cs.room_location) = lower(NEW.room_location)
  ) THEN RAISE(ABORT, 'Room already has an active class in this time slot') END;

  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM Enrollments candidate
    JOIN Enrollments existing ON existing.student_id = candidate.student_id
    JOIN Class_Schedules cs ON cs.course_id = existing.course_id
      AND cs.academic_year = existing.academic_year
      AND cs.semester = existing.semester
      AND cs.section = existing.section
    WHERE candidate.course_id = NEW.course_id
      AND candidate.academic_year = NEW.academic_year
      AND candidate.semester = NEW.semester AND candidate.section = NEW.section
      AND candidate.enrollment_status NOT IN ('Dropped', 'Withdrawn')
      AND existing.enrollment_status NOT IN ('Dropped', 'Withdrawn')
      AND cs.status = 'Active' AND cs.academic_year = NEW.academic_year
      AND cs.day_of_week = NEW.day_of_week
      AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
  ) THEN RAISE(ABORT, 'An enrolled student already has an active class in this time slot') END;
END;

CREATE TRIGGER trg_class_schedule_prevent_overlap_update
BEFORE UPDATE OF course_id, teacher_id, academic_year, semester, section, day_of_week, start_time, end_time, room_location, status ON Class_Schedules
WHEN NEW.status = 'Active'
BEGIN
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM Class_Schedules cs
    WHERE cs.schedule_id <> NEW.schedule_id AND cs.status = 'Active'
      AND cs.academic_year = NEW.academic_year AND cs.day_of_week = NEW.day_of_week
      AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
      AND cs.teacher_id = NEW.teacher_id
  ) THEN RAISE(ABORT, 'Teacher already has an active class in this time slot') END;

  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM Class_Schedules cs
    WHERE cs.schedule_id <> NEW.schedule_id AND cs.status = 'Active'
      AND cs.academic_year = NEW.academic_year AND cs.day_of_week = NEW.day_of_week
      AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
      AND lower(cs.room_location) = lower(NEW.room_location)
  ) THEN RAISE(ABORT, 'Room already has an active class in this time slot') END;

  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM Enrollments candidate
    JOIN Enrollments existing ON existing.student_id = candidate.student_id
    JOIN Class_Schedules cs ON cs.course_id = existing.course_id
      AND cs.academic_year = existing.academic_year
      AND cs.semester = existing.semester AND cs.section = existing.section
    WHERE candidate.course_id = NEW.course_id
      AND candidate.academic_year = NEW.academic_year
      AND candidate.semester = NEW.semester AND candidate.section = NEW.section
      AND candidate.enrollment_status NOT IN ('Dropped', 'Withdrawn')
      AND existing.enrollment_status NOT IN ('Dropped', 'Withdrawn')
      AND cs.schedule_id <> NEW.schedule_id AND cs.status = 'Active'
      AND cs.academic_year = NEW.academic_year AND cs.day_of_week = NEW.day_of_week
      AND NEW.start_time < cs.end_time AND NEW.end_time > cs.start_time
  ) THEN RAISE(ABORT, 'An enrolled student already has an active class in this time slot') END;
END;
