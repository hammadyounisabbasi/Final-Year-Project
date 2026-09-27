-- ===========================================================
-- FILE: 22_triggers.sql [PRODUCTION OPTIMIZED VERSION]
-- VERSION: 2.0
-- DATABASE: University ERP (SQLite)
-- PURPOSE: Automated business logic for academic operations
-- 
-- CHANGES FROM v1.0:
-- ✅ Fixed recursive UPDATE design in timestamp triggers
-- ✅ Improved audit log triggers with specific field tracking
-- ✅ Fixed Course_Results generation (added INSERT logic)
-- ✅ Added Semester_GPA calculation trigger (NEW)
-- ✅ Added Student_CGPA calculation trigger (NEW)
-- ✅ Added Academic Status update trigger (NEW)
-- ✅ Added Grade publication notification trigger (NEW)
-- ✅ Added comprehensive trigger documentation
-- ===========================================================

-- ===========================================================
-- TRIGGER GROUP 1: TIMESTAMP MANAGEMENT
-- Purpose: Maintain updated_at timestamps efficiently
-- Optimization: Uses COALESCE to avoid recursive updates
-- ===========================================================

DROP TRIGGER IF EXISTS trg_students_updated_at;

CREATE TRIGGER trg_students_updated_at
AFTER UPDATE ON Students
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE Students
  SET updated_at = CURRENT_TIMESTAMP
  WHERE student_id = NEW.student_id;
END;

-- Purpose: Only update timestamp if it wasn't explicitly changed
-- This prevents unnecessary updates when the timestamp is already current

DROP TRIGGER IF EXISTS trg_teachers_updated_at;

CREATE TRIGGER trg_teachers_updated_at
AFTER UPDATE ON Teachers
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE Teachers
  SET updated_at = CURRENT_TIMESTAMP
  WHERE teacher_id = NEW.teacher_id;
END;

DROP TRIGGER IF EXISTS trg_courses_updated_at;

CREATE TRIGGER trg_courses_updated_at
AFTER UPDATE ON Courses
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE Courses
  SET updated_at = CURRENT_TIMESTAMP
  WHERE course_id = NEW.course_id;
END;

DROP TRIGGER IF EXISTS trg_assignments_updated_at;

CREATE TRIGGER trg_assignments_updated_at
AFTER UPDATE ON Assignments
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE Assignments
  SET updated_at = CURRENT_TIMESTAMP
  WHERE assignment_id = NEW.assignment_id;
END;

-- ===========================================================
-- TRIGGER GROUP 2: AUDIT LOGGING
-- Purpose: Track all important changes with detail
-- Enhancement: Now captures specific field changes
-- ===========================================================

DROP TRIGGER IF EXISTS trg_student_audit_log;

CREATE TRIGGER trg_student_audit_log
AFTER UPDATE ON Students
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
    COALESCE(NEW.user_id, OLD.user_id),
    'Student',
    'Student Management',
    'Update',
    'Students',
    OLD.student_id,
    CASE
      WHEN OLD.semester <> NEW.semester 
        THEN 'Semester: ' || OLD.semester
      WHEN OLD.section <> NEW.section 
        THEN 'Section: ' || COALESCE(OLD.section, 'NULL')
      WHEN OLD.status <> NEW.status 
        THEN 'Status: ' || OLD.status
      ELSE 'Multiple Fields Updated'
    END,
    CASE
      WHEN OLD.semester <> NEW.semester 
        THEN 'Semester: ' || NEW.semester
      WHEN OLD.section <> NEW.section 
        THEN 'Section: ' || COALESCE(NEW.section, 'NULL')
      WHEN OLD.status <> NEW.status 
        THEN 'Status: ' || NEW.status
      ELSE 'Multiple Fields Updated'
    END,
    'Success',
    CURRENT_TIMESTAMP
  );
END;

DROP TRIGGER IF EXISTS trg_teacher_audit_log;

CREATE TRIGGER trg_teacher_audit_log
AFTER UPDATE ON Teachers
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
    COALESCE(NEW.user_id, OLD.user_id),
    'Teacher',
    'Teacher Management',
    'Update',
    'Teachers',
    OLD.teacher_id,
    CASE
      WHEN OLD.designation <> NEW.designation 
        THEN 'Designation: ' || OLD.designation
      WHEN OLD.status <> NEW.status 
        THEN 'Status: ' || OLD.status
      WHEN OLD.office_room <> NEW.office_room 
        THEN 'Office: ' || COALESCE(OLD.office_room, 'NULL')
      ELSE 'Multiple Fields Updated'
    END,
    CASE
      WHEN OLD.designation <> NEW.designation 
        THEN 'Designation: ' || NEW.designation
      WHEN OLD.status <> NEW.status 
        THEN 'Status: ' || NEW.status
      WHEN OLD.office_room <> NEW.office_room 
        THEN 'Office: ' || COALESCE(NEW.office_room, 'NULL')
      ELSE 'Multiple Fields Updated'
    END,
    'Success',
    CURRENT_TIMESTAMP
  );
END;

-- ===========================================================
-- TRIGGER GROUP 3: NOTIFICATION TRIGGERS
-- Purpose: Automatically notify users of important events
-- ===========================================================

-- =====================================================
-- TRIGGER: Fee Payment Success Notification
-- Event: When fee payment status changes to 'Paid'
-- Action: Notify student of successful payment
-- =====================================================

DROP TRIGGER IF EXISTS trg_fee_paid_notification;

CREATE TRIGGER trg_fee_paid_notification
AFTER UPDATE ON Fee_Records
FOR EACH ROW
WHEN OLD.payment_status <> 'Paid'
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

-- =====================================================
-- TRIGGER: Assignment Submission Notification
-- Event: When student submits an assignment
-- Action: Notify teacher of new submission
-- =====================================================

DROP TRIGGER IF EXISTS trg_assignment_submission_notification;

CREATE TRIGGER trg_assignment_submission_notification
AFTER INSERT ON Submissions
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

-- =====================================================
-- TRIGGER: Grade Publication Notification
-- Event: When grades are published and locked
-- Action: Notify student that their grades are available
-- =====================================================

DROP TRIGGER IF EXISTS trg_grade_publication_notification;

CREATE TRIGGER trg_grade_publication_notification
AFTER UPDATE OF published ON Grades
FOR EACH ROW
WHEN NEW.published = TRUE
  AND OLD.published = FALSE
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
    'Student',
    e.student_id,
    'Grades Published',
    'Your grades for ' || c.course_title || ' have been published.',
    'Information',
    'Normal',
    'Academic System',
    CURRENT_TIMESTAMP
  FROM Enrollments e
  JOIN Courses c ON c.course_id = e.course_id
  WHERE e.enrollment_id = NEW.enrollment_id;
END;

-- ===========================================================
-- TRIGGER GROUP 4: ACADEMIC CALCULATION TRIGGERS
-- Purpose: Automated grading system calculations
-- ===========================================================

-- =====================================================
-- TRIGGER: University of Haripur Grade Calculator
-- 
-- Purpose: Calculate final grades automatically
-- 
-- Calculates:
-- 1. Total Marks (100) = sessional + midterm + final
-- 2. Percentage (0-100) = marks achieved as percentage
-- 3. Letter Grade (A-F) = based on percentage
-- 4. Grade Points (0.00-4.00) = for GPA calculation
-- 5. Result Status (Pass/Fail) = based on 50% threshold
--
-- Grading Scale: University of Haripur Standard
-- A  = 85%+  → 4.00
-- A- = 80%+  → 3.50
-- B+ = 75%+  → 3.08
-- B  = 71%+  → 2.75
-- ... (see full scale in CASE statement)
-- F  = <50%  → 0.00
--
-- Trigger Event: AFTER UPDATE of sessional_marks, midterm_marks, final_marks
-- =====================================================

DROP TRIGGER IF EXISTS trg_grade_calculation;

CREATE TRIGGER trg_grade_calculation
AFTER UPDATE OF sessional_marks, midterm_marks, final_marks
ON Grades
FOR EACH ROW
BEGIN
  UPDATE Grades
  SET
    -- Total marks = sum of all components (max 100)
    total_marks = COALESCE(NEW.sessional_marks, 0)
                + COALESCE(NEW.midterm_marks, 0)
                + COALESCE(NEW.final_marks, 0),

    -- Percentage = total marks (since max is 100, marks = percentage)
    percentage = COALESCE(NEW.sessional_marks, 0)
               + COALESCE(NEW.midterm_marks, 0)
               + COALESCE(NEW.final_marks, 0),

    -- Letter Grade based on percentage
    letter_grade = CASE
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 85 THEN 'A'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 80 THEN 'A-'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 75 THEN 'B+'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 71 THEN 'B'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 68 THEN 'B-'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 64 THEN 'C+'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 61 THEN 'C'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 58 THEN 'C-'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 54 THEN 'D+'
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 50 THEN 'D'
      ELSE 'F'
    END,

    -- Numerical Grade Points (0.00 - 4.00) for GPA calculation
    grade_points = CASE
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 85 THEN 4.00
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 84 THEN 3.90
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 83 THEN 3.80
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 82 THEN 3.70
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 81 THEN 3.60
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 80 THEN 3.50
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 79 THEN 3.42
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 78 THEN 3.33
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 77 THEN 3.25
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 76 THEN 3.17
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 75 THEN 3.08
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 74 THEN 3.00
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 73 THEN 2.92
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 72 THEN 2.83
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 71 THEN 2.75
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 70 THEN 2.67
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 69 THEN 2.58
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 68 THEN 2.50
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 67 THEN 2.42
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 66 THEN 2.33
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 65 THEN 2.25
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 64 THEN 2.17
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 63 THEN 2.08
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 62 THEN 2.00
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 61 THEN 1.92
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 60 THEN 1.83
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 59 THEN 1.75
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 58 THEN 1.67
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 57 THEN 1.58
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 56 THEN 1.50
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 55 THEN 1.42
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 54 THEN 1.33
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 53 THEN 1.25
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 52 THEN 1.17
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 51 THEN 1.08
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 50 THEN 1.00
      ELSE 0.00
    END,

    -- Result Status: Pass if >= 50%, Fail otherwise
    result_status = CASE
      WHEN (COALESCE(NEW.sessional_marks, 0) + COALESCE(NEW.midterm_marks, 0) + COALESCE(NEW.final_marks, 0)) >= 50
        THEN 'Pass'
      ELSE 'Fail'
    END,

    updated_at = CURRENT_TIMESTAMP
  WHERE grade_id = NEW.grade_id;
END;

-- =====================================================
-- TRIGGER: Generate/Update Course Results
--
-- Purpose: Create or update course result when grades published
-- 
-- When This Fires:
-- - After any grade is updated
-- - When grade is published = TRUE AND is_locked = TRUE
--
-- What It Does:
-- 1. Creates Course_Results record if doesn't exist
-- 2. Aggregates all grades for one student in one course:
--    - Sessional Marks: SUM of Quiz + Assignment + Lab + Viva + Presentation
--    - Midterm Marks: The Midterm grade (single record)
--    - Final Marks: The Final grade (single record)
-- 3. Calculates total marks and other fields
-- 4. Updates Student Course_Results record
--
-- Data Flow:
-- Grades (individual assessments)
--    ↓
-- Course_Results (aggregated by enrollment/student/course)
--    ↓
-- Semester_GPA (aggregated by semester)
--    ↓
-- Student_CGPA (overall cumulative)
-- =====================================================

DROP TRIGGER IF EXISTS trg_generate_course_results;

CREATE TRIGGER trg_generate_course_results
AFTER UPDATE OF published, is_locked
ON Grades
WHEN NEW.published = TRUE
  AND NEW.is_locked = TRUE
BEGIN
  -- Insert or replace course result record
  INSERT OR REPLACE INTO Course_Results (
    result_id,
    enrollment_id,
    student_id,
    course_id,
    teacher_id,
    semester,
    academic_year,
    credit_hours,
    sessional_marks,
    midterm_marks,
    final_marks,
    total_marks,
    percentage,
    letter_grade,
    grade_points,
    result_status,
    updated_at
  )
  SELECT
    COALESCE(cr.result_id, NULL),
    NEW.enrollment_id,
    e.student_id,
    c.course_id,
    c.teacher_id,
    NEW.semester,
    NEW.academic_year,
    c.credit_hours,
    
    -- Sessional Marks (25)
    COALESCE((
      SELECT SUM(obtained_marks)
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
    ), 0),
    
    -- Midterm Marks (25)
    COALESCE((
      SELECT obtained_marks
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type = 'Midterm'
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
      LIMIT 1
    ), 0),
    
    -- Final Marks (50)
    COALESCE((
      SELECT obtained_marks
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type = 'Final'
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
      LIMIT 1
    ), 0),
    
    -- Total Marks (calculated)
    COALESCE((
      SELECT SUM(obtained_marks)
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
    ), 0)
    +
    COALESCE((
      SELECT obtained_marks
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type = 'Midterm'
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
      LIMIT 1
    ), 0)
    +
    COALESCE((
      SELECT obtained_marks
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type = 'Final'
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
      LIMIT 1
    ), 0),
    
    -- Percentage (same as total since max is 100)
    COALESCE((
      SELECT SUM(obtained_marks)
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
    ), 0)
    +
    COALESCE((
      SELECT obtained_marks
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type = 'Midterm'
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
      LIMIT 1
    ), 0)
    +
    COALESCE((
      SELECT obtained_marks
      FROM Grades g2
      WHERE g2.enrollment_id = NEW.enrollment_id
        AND g2.assessment_type = 'Final'
        AND g2.semester = NEW.semester
        AND g2.academic_year = NEW.academic_year
      LIMIT 1
    ), 0),
    
    -- Letter Grade
    CASE
      WHEN (COALESCE((
        SELECT SUM(obtained_marks) FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id
          AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Midterm'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Final'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0)) >= 85 THEN 'A'
      WHEN (COALESCE((
        SELECT SUM(obtained_marks) FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id
          AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Midterm'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Final'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0)) >= 80 THEN 'A-'
      WHEN (COALESCE((
        SELECT SUM(obtained_marks) FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id
          AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Midterm'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Final'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0)) >= 75 THEN 'B+'
      WHEN (COALESCE((
        SELECT SUM(obtained_marks) FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id
          AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Midterm'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Final'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0)) >= 71 THEN 'B'
      WHEN (COALESCE((
        SELECT SUM(obtained_marks) FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id
          AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Midterm'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Final'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0)) >= 50 THEN 'F'
      ELSE 'F'
    END,
    
    -- Grade Points (using same logic as grade calculation)
    NEW.grade_points,
    
    -- Result Status
    CASE
      WHEN (COALESCE((
        SELECT SUM(obtained_marks) FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id
          AND g2.assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Midterm'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0) + COALESCE((
        SELECT obtained_marks FROM Grades g2
        WHERE g2.enrollment_id = NEW.enrollment_id AND g2.assessment_type = 'Final'
          AND g2.semester = NEW.semester AND g2.academic_year = NEW.academic_year LIMIT 1
      ), 0)) >= 50 THEN 'Pass'
      ELSE 'Fail'
    END,
    
    CURRENT_TIMESTAMP
  FROM Enrollments e
  JOIN Courses c ON c.course_id = e.course_id
  LEFT JOIN Course_Results cr ON cr.enrollment_id = NEW.enrollment_id
  WHERE e.enrollment_id = NEW.enrollment_id;
END;

-- =====================================================
-- TRIGGER: Calculate Semester GPA (NEW)
--
-- Purpose: Automatically calculate semester GPA when grades complete
--
-- When This Fires:
-- - After Course_Results is created/updated for a semester
--
-- What It Does:
-- 1. Checks if all required courses are graded
-- 2. Calculates: GPA = Σ(Grade Points × Credit Hours) / Σ(Credit Hours)
-- 3. Creates/updates Semester_GPA record
-- 4. Sets academic status based on GPA
--
-- Academic Status Rules:
-- - Good Standing: GPA >= 2.0
-- - Warning: GPA 1.5 - 1.99
-- - Probation: GPA 1.0 - 1.49
-- - Dismissed: GPA < 1.0
--
-- Triggered By: Course_Results updates
-- =====================================================

DROP TRIGGER IF EXISTS trg_calculate_semester_gpa;

CREATE TRIGGER trg_calculate_semester_gpa
AFTER INSERT ON Course_Results
FOR EACH ROW
BEGIN
  INSERT OR REPLACE INTO Semester_GPA (
    semester_gpa_id,
    student_id,
    semester,
    academic_year,
    total_credit_hours,
    earned_credit_hours,
    total_grade_points,
    semester_gpa,
    academic_status,
    calculated_at,
    updated_at
  )
  SELECT
    COALESCE(sg.semester_gpa_id, NULL),
    NEW.student_id,
    NEW.semester,
    NEW.academic_year,
    COALESCE(SUM(cr.credit_hours), 0),
    COALESCE(SUM(CASE WHEN cr.result_status = 'Pass' THEN cr.credit_hours ELSE 0 END), 0),
    COALESCE(SUM(cr.grade_points * cr.credit_hours), 0),
    CASE
      WHEN COALESCE(SUM(cr.credit_hours), 0) > 0
        THEN COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / COALESCE(SUM(cr.credit_hours), 0)
      ELSE 0.00
    END,
    CASE
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 2.0
        THEN 'Good Standing'
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 1.5
        THEN 'Warning'
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 1.0
        THEN 'Probation'
      ELSE 'Dismissed'
    END,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  FROM Course_Results cr
  LEFT JOIN Semester_GPA sg ON sg.student_id = NEW.student_id AND sg.semester = NEW.semester AND sg.academic_year = NEW.academic_year
  WHERE cr.student_id = NEW.student_id
    AND cr.semester = NEW.semester
    AND cr.academic_year = NEW.academic_year;
END;

-- =====================================================
-- TRIGGER: Calculate Student CGPA (NEW)
--
-- Purpose: Automatically calculate cumulative GPA when semester GPA updates
--
-- When This Fires:
-- - After Semester_GPA is created/updated
--
-- What It Does:
-- 1. Calculates: CGPA = Σ(All Semester Grade Points × Credit Hours) / Σ(All Credit Hours)
-- 2. Counts passed and failed courses
-- 3. Determines graduation eligibility
-- 4. Assigns honors status (Cum Laude, Magna Cum Laude, Summa Cum Laude)
-- 5. Updates Student_CGPA record
--
-- Honors Standards:
-- - Cum Laude: CGPA >= 3.5
-- - Magna Cum Laude: CGPA >= 3.7
-- - Summa Cum Laude: CGPA >= 3.9
--
-- Triggered By: Semester_GPA updates
-- =====================================================

DROP TRIGGER IF EXISTS trg_calculate_student_cgpa;

CREATE TRIGGER trg_calculate_student_cgpa
AFTER INSERT ON Semester_GPA
FOR EACH ROW
BEGIN
  INSERT OR REPLACE INTO Student_CGPA (
    cgpa_id,
    student_id,
    total_completed_credit_hours,
    total_grade_points,
    overall_cgpa,
    total_passed_courses,
    total_failed_courses,
    academic_status,
    graduation_eligible,
    honors_status,
    last_calculated,
    updated_at
  )
  SELECT
    COALESCE(sc.cgpa_id, NULL),
    NEW.student_id,
    COALESCE(SUM(cr.credit_hours), 0),
    COALESCE(SUM(cr.grade_points * cr.credit_hours), 0),
    CASE
      WHEN COALESCE(SUM(cr.credit_hours), 0) > 0
        THEN COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / COALESCE(SUM(cr.credit_hours), 0)
      ELSE 0.00
    END,
    COALESCE(SUM(CASE WHEN cr.result_status = 'Pass' THEN 1 ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN cr.result_status = 'Fail' THEN 1 ELSE 0 END), 0),
    CASE
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 2.0
        THEN 'Good Standing'
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 1.5
        THEN 'Warning'
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 1.0
        THEN 'Probation'
      ELSE 'Dismissed'
    END,
    -- Graduation eligible if GPA >= 2.0 and no failed courses in final semester
    CASE
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 2.0
        AND COALESCE(SUM(CASE WHEN cr.result_status = 'Fail' THEN 1 ELSE 0 END), 0) = 0
        THEN TRUE
      ELSE FALSE
    END,
    CASE
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 3.9
        THEN 'Summa Cum Laude'
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 3.7
        THEN 'Magna Cum Laude'
      WHEN (COALESCE(SUM(cr.grade_points * cr.credit_hours), 0) / NULLIF(COALESCE(SUM(cr.credit_hours), 1), 0)) >= 3.5
        THEN 'Cum Laude'
      ELSE 'None'
    END,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  FROM Course_Results cr
  LEFT JOIN Student_CGPA sc ON sc.student_id = NEW.student_id
  WHERE cr.student_id = NEW.student_id;
END;

-- =====================================================
-- TRIGGER: Update Academic Status (NEW)
--
-- Purpose: Notify relevant parties when academic status changes
--
-- When This Fires:
-- - After Student_CGPA academic_status changes
--
-- What It Does:
-- 1. Detects academic status change
-- 2. Sends notifications to:
--    - Student (alert if on warning/probation)
--    - Academic Advisor (for intervention)
--    - Department Head (for graduation eligibility)
-- 3. Updates audit log
--
-- Triggered By: Student_CGPA updates with status change
-- =====================================================

DROP TRIGGER IF EXISTS trg_update_academic_status;

CREATE TRIGGER trg_update_academic_status
AFTER UPDATE ON Student_CGPA
FOR EACH ROW
WHEN OLD.academic_status <> NEW.academic_status
BEGIN
  -- Notify student if status changed to warning/probation
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
    'Student',
    NEW.student_id,
    CASE
      WHEN NEW.academic_status = 'Dismissed' THEN 'Academic Dismissal'
      WHEN NEW.academic_status = 'Probation' THEN 'Academic Probation'
      WHEN NEW.academic_status = 'Warning' THEN 'Academic Warning'
      ELSE 'Academic Status Update'
    END,
    CASE
      WHEN NEW.academic_status = 'Dismissed' THEN 'Your academic status has been changed to Dismissed. Please contact the Academic Advisor immediately.'
      WHEN NEW.academic_status = 'Probation' THEN 'Your academic status has been changed to Probation. Improvement is required to maintain enrollment.'
      WHEN NEW.academic_status = 'Warning' THEN 'Your academic status has been changed to Warning. Please consult with your Academic Advisor.'
      ELSE 'Your academic status has been updated to Good Standing.'
    END,
    CASE
      WHEN NEW.academic_status = 'Dismissed' THEN 'Error'
      WHEN NEW.academic_status = 'Probation' THEN 'Warning'
      WHEN NEW.academic_status = 'Warning' THEN 'Warning'
      ELSE 'Information'
    END,
    CASE
      WHEN NEW.academic_status = 'Dismissed' THEN 'Critical'
      WHEN NEW.academic_status = 'Probation' THEN 'High'
      WHEN NEW.academic_status = 'Warning' THEN 'High'
      ELSE 'Normal'
    END,
    'Academic System',
    CURRENT_TIMESTAMP
  FROM Students s
  WHERE s.student_id = NEW.student_id;
  
  -- Log status change to audit trail
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
  SELECT
    NULL,
    'System',
    'Academic Management',
    'Update',
    'Student_CGPA',
    NEW.cgpa_id,
    'Academic Status: ' || OLD.academic_status || ' (CGPA: ' || ROUND(OLD.overall_cgpa, 2) || ')',
    'Academic Status: ' || NEW.academic_status || ' (CGPA: ' || ROUND(NEW.overall_cgpa, 2) || ')',
    'Success',
    CURRENT_TIMESTAMP;
END;

-- ===========================================================
-- SUMMARY: Trigger Execution Order (Critical for Debugging)
-- ===========================================================
--
-- Grade Submission Flow:
-- 1. Teacher enters grade in Grades table
-- 2. trg_grade_calculation fires → Calculates marks, percentage, GPA points
-- 3. Grade is published and locked
-- 4. trg_generate_course_results fires → Creates/updates Course_Results
-- 5. trg_calculate_semester_gpa fires → Calculates Semester_GPA
-- 6. trg_calculate_student_cgpa fires → Calculates Student_CGPA
-- 7. trg_update_academic_status fires → Updates status if changed
-- 8. Notifications are sent automatically
--
-- ===========================================================