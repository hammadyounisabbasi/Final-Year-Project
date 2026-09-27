-- ===========================================================
-- MIGRATION: v16_balanced_timetable.sql
-- PURPOSE: Interdisciplinary Teacher Balancing & Conflict-Free Timetable
-- ===========================================================

PRAGMA foreign_keys = ON;

-- 1. Ensure past completed student enrollments are marked as 'Completed'
UPDATE Enrollments
SET enrollment_status = 'Enrolled'
WHERE EXISTS (
    SELECT 1 FROM Students s
    WHERE s.student_id = Enrollments.student_id
      AND s.semester = Enrollments.semester
);

UPDATE Enrollments
SET enrollment_status = 'Completed'
WHERE EXISTS (
    SELECT 1 FROM Students s
    WHERE s.student_id = Enrollments.student_id
      AND s.semester > Enrollments.semester
);

-- 2. Update Courses with Interdisciplinary Teachers across Departments
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-002') WHERE course_code = 'CSE-101';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-002') WHERE course_code = 'CSE-102';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-001') WHERE course_code = 'CSE-103';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-005') WHERE course_code = 'CSE-104';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-BBA-005') WHERE course_code = 'CSE-105';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-001')  WHERE course_code = 'CSE-106';

UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-002') WHERE course_code = 'CSE-201';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-003') WHERE course_code = 'CSE-202';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-002') WHERE course_code = 'CSE-203';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-PHY-001') WHERE course_code = 'CSE-204';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-PSY-001') WHERE course_code = 'CSE-205';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-003') WHERE course_code = 'CSE-206';

UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-001') WHERE course_code = 'CSE-301';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-001') WHERE course_code = 'CSE-302';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-ENG-005') WHERE course_code = 'CSE-303';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-BBA-003') WHERE course_code = 'CSE-304';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-EE-005')  WHERE course_code = 'CSE-305';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-002') WHERE course_code = 'CSE-306';

UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-MTH-004') WHERE course_code = 'CSE-401';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-004') WHERE course_code = 'CSE-402';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CY-001')  WHERE course_code = 'CSE-403';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-002')  WHERE course_code = 'CSE-404';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-001')  WHERE course_code = 'CSE-405';

UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-EE-001')  WHERE course_code = 'CSE-501';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-003') WHERE course_code = 'CSE-502';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-005') WHERE course_code = 'CSE-503';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-003')  WHERE course_code = 'CSE-504';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-003')  WHERE course_code = 'CSE-505';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-002') WHERE course_code = 'CSE-506';

UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-001') WHERE course_code = 'CSE-601';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CSE-003') WHERE course_code = 'CSE-602';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-DS-003')  WHERE course_code = 'CSE-603';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-002')  WHERE course_code = 'CSE-604';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-IT-004')  WHERE course_code = 'CSE-605';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-001')  WHERE course_code = 'CSE-606';

UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-SE-001')  WHERE course_code = 'CSE-701';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-003')  WHERE course_code = 'CSE-702';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-CY-003')  WHERE course_code = 'CSE-703';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-DS-001')  WHERE course_code = 'CSE-704';

UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-DS-001')  WHERE course_code = 'CSE-801';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-002')  WHERE course_code = 'CSE-802';
UPDATE Courses SET teacher_id = (SELECT teacher_id FROM Teachers WHERE employee_id = 'UOH-AI-005')  WHERE course_code = 'CSE-803';

-- 3. Synchronize Class_Schedules teacher_id with Courses teacher_id
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

-- 4. Re-link Student_Timetable
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
JOIN Courses c 
  ON c.course_id = cs.course_id 
 AND c.teacher_id = cs.teacher_id
WHERE e.enrollment_status = 'Enrolled';
