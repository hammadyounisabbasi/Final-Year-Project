-- ===========================================================
-- TRIGGER:
-- Students Updated Timestamp
-- ===========================================================
DROP TRIGGER IF EXISTS trg_students_updated_at;
CREATE TRIGGER trg_students_updated_at
AFTER UPDATE
ON Students
FOR EACH ROW
BEGIN
UPDATE Students
SET updated_at = CURRENT_TIMESTAMP
WHERE student_id = NEW.student_id;
END;
DROP TRIGGER IF EXISTS trg_teachers_updated_at;
CREATE TRIGGER trg_teachers_updated_at
AFTER UPDATE
ON Teachers
FOR EACH ROW
BEGIN
UPDATE Teachers
SET updated_at = CURRENT_TIMESTAMP
WHERE teacher_id = NEW.teacher_id;
END;
DROP TRIGGER IF EXISTS trg_courses_updated_at;
CREATE TRIGGER trg_courses_updated_at
AFTER UPDATE
ON Courses
FOR EACH ROW
BEGIN
UPDATE Courses
SET updated_at = CURRENT_TIMESTAMP
WHERE course_id = NEW.course_id;
END;
DROP TRIGGER IF EXISTS trg_assignments_updated_at;
CREATE TRIGGER trg_assignments_updated_at
AFTER UPDATE
ON Assignments
FOR EACH ROW
BEGIN
UPDATE Assignments
SET updated_at = CURRENT_TIMESTAMP
WHERE assignment_id = NEW.assignment_id;
END;
-- ===========================================================
-- TRIGGER:
-- Student Update Audit Log
-- ===========================================================
DROP TRIGGER IF EXISTS trg_student_audit_log;
CREATE TRIGGER trg_student_audit_log
AFTER UPDATE
ON Students
FOR EACH ROW
BEGIN
INSERT INTO Audit_Logs (
    user_id,
    user_role,
    module_name,
    action_type,
    table_name,
    record_id,
    old_value,
    new_value,
    action_status,
    created_at
)
VALUES (
    OLD.user_id,
    'Student',
    'Student Management',
    'Update',
    'Students',
    OLD.student_id,
    'Record Updated',
    'Student information modified',
    'Success',
    CURRENT_TIMESTAMP
);
END;
DROP TRIGGER IF EXISTS trg_teacher_audit_log;
CREATE TRIGGER trg_teacher_audit_log
AFTER UPDATE
ON Teachers
FOR EACH ROW
BEGIN
INSERT INTO Audit_Logs (
    user_id,
    user_role,
    module_name,
    action_type,
    table_name,
    record_id,
    old_value,
    new_value,
    action_status,
    created_at
)
VALUES (
    OLD.user_id,
    'Teacher',
    'Teacher Management',
    'Update',
    'Teachers',
    OLD.teacher_id,
    'Record Updated',
    'Teacher information modified',
    'Success',
    CURRENT_TIMESTAMP
);
END;
-- ===========================================================
-- TRIGGER:
-- Fee Payment Success Notification
-- PURPOSE:
-- Automatically notifies the student when fee status
-- changes from Pending/Partial to Paid.
-- ===========================================================
DROP TRIGGER IF EXISTS trg_fee_paid_notification;
CREATE TRIGGER trg_fee_paid_notification
AFTER UPDATE
ON Fee_Records
FOR EACH ROW
WHEN
    OLD.payment_status <> 'Paid'
    AND NEW.payment_status = 'Paid'
BEGIN
INSERT INTO Notifications (
    recipient_type,
    recipient_id,
    title,
    message,
    notification_type,
    priority,
    sender,
    created_at
)
VALUES (
    'Student',
    NEW.student_id,
    'Fee Payment Successful',
    'Your semester fee has been successfully received and verified.',
    'Success',
    'Normal',
    'Finance Department',
    CURRENT_TIMESTAMP
);
END;
-- ===========================================================
-- TRIGGER: 8
-- Assignment Submission Notification
-- PURPOSE:
-- Automatically notify the teacher when a student submits
-- an assignment.
-- ===========================================================
DROP TRIGGER IF EXISTS trg_assignment_submission_notification;
CREATE TRIGGER trg_assignment_submission_notification
AFTER INSERT
ON Submissions
FOR EACH ROW
BEGIN
INSERT INTO Notifications (
    recipient_type,
    recipient_id,
    title,
    message,
    notification_type,
    priority,
    sender,
    created_at
)
SELECT
    'Teacher',
    a.teacher_id,
    'New Assignment Submission',
    'A student has submitted the assignment "' || a.title || '".',
    'Information',
    'Normal',
    'Assignment System',
    CURRENT_TIMESTAMP
FROM Assignments a
WHERE a.assignment_id = NEW.assignment_id;
END;
-- ===========================================================
-- TRIGGER:9
-- University of Haripur Grade Calculator
--
-- PURPOSE:
-- Automatically calculates:
-- 1. Total Marks (100)
-- 2. Percentage
-- 3. Letter Grade
-- 4. Grade Points (NG)
-- 5. Result Status
-- ===========================================================
DROP TRIGGER IF EXISTS trg_grade_calculation;
CREATE TRIGGER trg_grade_calculation
AFTER UPDATE OF
sessional_marks,
midterm_marks,
final_marks
ON Grades
FOR EACH ROW
BEGIN
UPDATE Grades
SET
---------------------------------------------------------
-- TOTAL MARKS
---------------------------------------------------------
total_marks =
COALESCE(NEW.sessional_marks,0)
+
COALESCE(NEW.midterm_marks,0)
+
COALESCE(NEW.final_marks,0),
---------------------------------------------------------
-- PERCENTAGE
---------------------------------------------------------
percentage =
COALESCE(NEW.sessional_marks,0)
+
COALESCE(NEW.midterm_marks,0)
+
COALESCE(NEW.final_marks,0),
---------------------------------------------------------
-- LETTER GRADE
---------------------------------------------------------
letter_grade =
CASE
WHEN percentage >= 85 THEN 'A'
WHEN percentage >= 80 THEN 'A-'
WHEN percentage >= 75 THEN 'B+'
WHEN percentage >= 71 THEN 'B'
WHEN percentage >= 68 THEN 'B-'
WHEN percentage >= 64 THEN 'C+'
WHEN percentage >= 61 THEN 'C'
WHEN percentage >= 58 THEN 'C-'
WHEN percentage >= 54 THEN 'D+'
WHEN percentage >= 50 THEN 'D'
ELSE 'F'
END,
---------------------------------------------------------
-- NUMERICAL GRADE (GRADE POINTS)
---------------------------------------------------------
grade_points =
CASE
WHEN percentage >= 85 THEN 4.00
WHEN percentage >= 84 THEN 3.90
WHEN percentage >= 83 THEN 3.80
WHEN percentage >= 82 THEN 3.70
WHEN percentage >= 81 THEN 3.60
WHEN percentage >= 80 THEN 3.50
WHEN percentage >= 79 THEN 3.42
WHEN percentage >= 78 THEN 3.33
WHEN percentage >= 77 THEN 3.25
WHEN percentage >= 76 THEN 3.17
WHEN percentage >= 75 THEN 3.08
WHEN percentage >= 74 THEN 3.00
WHEN percentage >= 73 THEN 2.92
WHEN percentage >= 72 THEN 2.83
WHEN percentage >= 71 THEN 2.75
WHEN percentage >= 70 THEN 2.67
WHEN percentage >= 69 THEN 2.58
WHEN percentage >= 68 THEN 2.50
WHEN percentage >= 67 THEN 2.42
WHEN percentage >= 66 THEN 2.33
WHEN percentage >= 65 THEN 2.25
WHEN percentage >= 64 THEN 2.17
WHEN percentage >= 63 THEN 2.08
WHEN percentage >= 62 THEN 2.00
WHEN percentage >= 61 THEN 1.92
WHEN percentage >= 60 THEN 1.83
WHEN percentage >= 59 THEN 1.75
WHEN percentage >= 58 THEN 1.67
WHEN percentage >= 57 THEN 1.58
WHEN percentage >= 56 THEN 1.50
WHEN percentage >= 55 THEN 1.42
WHEN percentage >= 54 THEN 1.33
WHEN percentage >= 53 THEN 1.25
WHEN percentage >= 52 THEN 1.17
WHEN percentage >= 51 THEN 1.08
WHEN percentage >= 50 THEN 1.00
ELSE 0.00
END,
---------------------------------------------------------
-- RESULT
---------------------------------------------------------
result_status =
CASE
WHEN percentage >= 50
THEN 'Pass'
ELSE 'Fail'
END,
updated_at = CURRENT_TIMESTAMP
WHERE grade_id = NEW.grade_id;
END;
-- ===========================================================
-- FILE : 25_trigger_10_course_results.sql
-- TRIGGER : 10
--
-- PURPOSE
-- Automatically generate/update Course Results
-- whenever all assessments are published & locked.
--
-- FLOW
-- Grades
--      ↓
-- Course_Results
--
-- NOTE
-- Part 1
--   • Trigger Header
--   • Existing Result Update
--   • Aggregate Raw Marks
-- ===========================================================
DROP TRIGGER IF EXISTS trg_generate_course_results;
CREATE TRIGGER trg_generate_course_results
AFTER UPDATE OF published, is_locked
ON Grades
WHEN
    NEW.published = TRUE
    AND NEW.is_locked = TRUE
BEGIN
------------------------------------------------------------
-- UPDATE EXISTING COURSE RESULT
------------------------------------------------------------
UPDATE Course_Results
SET
------------------------------------------------------------
-- Teacher
------------------------------------------------------------
teacher_id =
(
    SELECT c.teacher_id
    FROM Enrollments e
    JOIN Courses c
        ON c.course_id = e.course_id
    WHERE
    e.enrollment_id = NEW.enrollment_id
),
------------------------------------------------------------
-- SESSIONAL MARKS (25)
------------------------------------------------------------
sessional_marks =
COALESCE
(
(
SELECT
SUM(obtained_marks)
FROM Grades
WHERE
enrollment_id = NEW.enrollment_id
AND assessment_type IN
(
'Quiz',
'Assignment',
'Lab',
'Viva',
'Presentation'
)
)
,0
),
------------------------------------------------------------
-- MIDTERM (25)
------------------------------------------------------------
midterm_marks =
COALESCE
(
(
SELECT
obtained_marks
FROM Grades
WHERE
enrollment_id = NEW.enrollment_id
AND assessment_type='Midterm'
LIMIT 1
)
,0
),
------------------------------------------------------------
-- FINAL (50)
------------------------------------------------------------
final_marks =
COALESCE
(
(
SELECT
obtained_marks
FROM Grades
WHERE
enrollment_id = NEW.enrollment_id
AND assessment_type='Final'
LIMIT 1
)
,0
),
updated_at = CURRENT_TIMESTAMP
WHERE
enrollment_id = NEW.enrollment_id;