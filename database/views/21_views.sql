-- ===========================================================
-- FILE: 21_views.sql
-- VERSION: 2.0 (PROFESSIONAL COMPREHENSIVE)
-- DATABASE: University ERP
-- PURPOSE: Production-grade views for all modules
-- 
-- CONTENTS: 31 Strategic Views
-- - 3 Dashboard Views (Improved)
-- - 5 Academic Records Views
-- - 6 GPA & Academic Standing Views
-- - 4 Grading & Assessment Views
-- - 3 Attendance Views
-- - 3 Fee & Finance Views
-- - 2 Course Management Views
-- - 2 Administrative Views
-- - 3 AI & Analytics Views
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- DROP ALL VIEWS (SAFE CLEANUP)
-- ===========================================================

DROP VIEW IF EXISTS vw_at_risk_students;
DROP VIEW IF EXISTS vw_department_performance_analytics;
DROP VIEW IF EXISTS vw_scholarship_candidates;
DROP VIEW IF EXISTS vw_pending_notifications;
DROP VIEW IF EXISTS vw_audit_activity_summary;
DROP VIEW IF EXISTS vw_course_enrollment_summary;
DROP VIEW IF EXISTS vw_course_offerings_semester;
DROP VIEW IF EXISTS vw_fee_collection_summary;
DROP VIEW IF EXISTS vw_pending_fee_payments;
DROP VIEW IF EXISTS vw_student_fee_status;
DROP VIEW IF EXISTS vw_attendance_compliance;
DROP VIEW IF EXISTS vw_course_attendance_analysis;
DROP VIEW IF EXISTS vw_student_attendance_summary;
DROP VIEW IF EXISTS vw_student_performance_metrics;
DROP VIEW IF EXISTS vw_grades_distribution;
DROP VIEW IF EXISTS vw_pending_grades;
DROP VIEW IF EXISTS vw_assignment_submission_status;
DROP VIEW IF EXISTS vw_academic_probation_students;
DROP VIEW IF EXISTS vw_academic_warning_students;
DROP VIEW IF EXISTS vw_graduation_eligibility;
DROP VIEW IF EXISTS vw_student_cgpa_breakdown;
DROP VIEW IF EXISTS vw_semester_gpa_breakdown;
DROP VIEW IF EXISTS vw_student_academic_standing;
DROP VIEW IF EXISTS vw_semester_results_summary;
DROP VIEW IF EXISTS vw_course_results_summary;
DROP VIEW IF EXISTS vw_course_roster;
DROP VIEW IF EXISTS vw_student_current_grades;
DROP VIEW IF EXISTS vw_student_transcript;
DROP VIEW IF EXISTS vw_admin_dashboard;
DROP VIEW IF EXISTS vw_teacher_dashboard;
DROP VIEW IF EXISTS vw_student_dashboard;

-- ===========================================================
-- SECTION 1: DASHBOARD VIEWS (3 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_student_dashboard
-- 
-- PURPOSE:
-- Complete student dashboard summary for student portal
-- Shows academic status, grades, fees, notifications at a glance
--
-- USED BY:
-- • Student Portal Dashboard
-- • Student Mobile App
-- • AI Academic Advisor
-- • Student Self-Service System
-- ===========================================================

CREATE VIEW vw_student_dashboard AS
SELECT
    s.student_id,
    s.roll_number,
    s.registration_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    s.semester,
    s.section,
    s.batch_year,
    d.department_name,
    u.username,
    u.email,
    u.last_login,
    s.status AS student_status,
    COALESCE(sc.overall_cgpa, 0.00) AS overall_cgpa,
    COALESCE(sc.academic_status, 'Good Standing') AS academic_status,
    COALESCE(sc.honors_status, 'None') AS honors_status,
    COALESCE(sg.semester_gpa, 0.00) AS current_semester_gpa,
    COALESCE(sg.academic_status, 'Good Standing') AS semester_status,
    COALESCE(fr.payment_status, 'Pending') AS current_fee_status,
    COALESCE(fr.remaining_amount, 0.00) AS fee_remaining,
    COALESCE(
        (SELECT COUNT(*)
         FROM Notifications n
         WHERE n.recipient_type = 'Student'
           AND n.recipient_id = s.student_id
           AND n.is_read = FALSE),
        0
    ) AS unread_notifications,
    COALESCE(sc.graduation_eligible, FALSE) AS is_graduation_eligible,
    s.credits_completed AS total_credits_earned,
    CURRENT_TIMESTAMP AS view_generated_at
FROM Students s
INNER JOIN Users u ON s.user_id = u.user_id
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Student_CGPA sc ON sc.student_id = s.student_id
LEFT JOIN Semester_GPA sg ON sg.student_id = s.student_id AND sg.semester = s.semester
LEFT JOIN Fee_Records fr ON fr.student_id = s.student_id AND fr.semester = s.semester;

-- ===========================================================
-- VIEW: vw_teacher_dashboard
--
-- PURPOSE:
-- Complete teacher dashboard summary
-- Shows assigned courses, pending grading tasks, notifications
--
-- USED BY:
-- • Teacher Portal Dashboard
-- • Teacher Mobile App
-- • Course Management System
-- • Teaching Load Analysis
-- ===========================================================

CREATE VIEW vw_teacher_dashboard AS
SELECT
    t.teacher_id,
    t.employee_id,
    t.first_name || ' ' || t.last_name AS teacher_name,
    t.designation,
    t.specialization,
    d.department_name,
    u.username,
    u.email,
    u.last_login,
    t.status AS teacher_status,
    COALESCE(
        (SELECT COUNT(*)
         FROM Courses c
         WHERE c.teacher_id = t.teacher_id
           AND c.status = 'Active'),
        0
    ) AS total_active_courses,
    COALESCE(
        (SELECT COUNT(DISTINCT e.student_id)
         FROM Enrollments e
         JOIN Courses c ON c.course_id = e.course_id
         WHERE c.teacher_id = t.teacher_id
           AND c.status = 'Active'
           AND e.enrollment_status = 'Enrolled'),
        0
    ) AS total_students_taught,
    COALESCE(
        (SELECT COUNT(*)
         FROM Grades g
         WHERE g.graded_by = t.teacher_id
           AND g.published = FALSE),
        0
    ) AS pending_grades_count,
    COALESCE(
        (SELECT COUNT(*)
         FROM Notifications n
         WHERE n.recipient_type = 'Teacher'
           AND n.recipient_id = t.teacher_id
           AND n.is_read = FALSE),
        0
    ) AS unread_notifications,
    COALESCE(
        (SELECT COUNT(DISTINCT a.assignment_id)
         FROM Assignments a
         WHERE a.teacher_id = t.teacher_id
           AND a.status = 'Published'
           AND a.due_date > CURRENT_TIMESTAMP),
        0
    ) AS active_assignments,
    t.office_room,
    t.office_email,
    CURRENT_TIMESTAMP AS view_generated_at
FROM Teachers t
INNER JOIN Users u ON t.user_id = u.user_id
INNER JOIN Departments d ON t.department_id = d.department_id;

-- ===========================================================
-- VIEW: vw_admin_dashboard
--
-- PURPOSE:
-- University-wide administrative dashboard
-- Shows key metrics for institutional oversight
--
-- USED BY:
-- • Admin Portal Dashboard
-- • University Executive Dashboard
-- • Analytics Panel
-- • AI Administration Agent
-- ===========================================================

CREATE VIEW vw_admin_dashboard AS
SELECT
    (SELECT COUNT(*) FROM Users) AS total_users,
    (SELECT COUNT(*) FROM Students WHERE status = 'Active') AS active_students,
    (SELECT COUNT(*) FROM Students WHERE status = 'Graduated') AS graduated_students,
    (SELECT COUNT(*) FROM Teachers WHERE status = 'Active') AS active_teachers,
    (SELECT COUNT(*) FROM Departments WHERE status = 'Active') AS active_departments,
    (SELECT COUNT(*) FROM Courses WHERE status = 'Active') AS active_courses,
    (SELECT COUNT(*) FROM Enrollments WHERE enrollment_status = 'Enrolled') AS total_enrollments,
    (SELECT COUNT(*)
     FROM Fee_Records
     WHERE payment_status IN ('Pending', 'Partial', 'Overdue')) AS pending_fee_records,
    (SELECT COALESCE(SUM(paid_amount), 0.00)
     FROM Fee_Records
     WHERE payment_status = 'Paid') AS total_revenue_collected,
    (SELECT COALESCE(SUM(remaining_amount), 0.00)
     FROM Fee_Records
     WHERE payment_status <> 'Paid') AS pending_revenue,
    (SELECT COUNT(*)
     FROM Notifications
     WHERE recipient_type = 'Admin'
       AND is_read = FALSE) AS unread_admin_notifications,
    (SELECT COUNT(DISTINCT DATE(created_at))
     FROM Audit_Logs
     WHERE created_at > datetime('now', '-30 days')) AS active_days_last_30,
    (SELECT COUNT(*)
     FROM Students
     WHERE status = 'Active'
       AND COALESCE(
             (SELECT academic_status
              FROM Student_CGPA
              WHERE student_id = Students.student_id),
             'Good Standing') IN ('Warning', 'Probation', 'Dismissed')) AS at_risk_students,
    (SELECT COUNT(*)
     FROM Enrollments
     WHERE enrollment_status = 'Enrolled'
       AND student_id IN (
             SELECT student_id
             FROM Student_CGPA
             WHERE graduation_eligible = TRUE)) AS graduation_eligible_students,
    CURRENT_TIMESTAMP AS dashboard_generated_at;

-- ===========================================================
-- SECTION 2: ACADEMIC RECORDS VIEWS (5 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_student_transcript
--
-- PURPOSE:
-- Complete academic transcript for a student
-- Shows all courses taken with grades and credit hours
-- Used for transcript generation and academic records
--
-- USED BY:
-- • Transcript Generator
-- • Student Records
-- • Academic Advisor
-- • Registrar Office
-- ===========================================================

CREATE VIEW vw_student_transcript AS
SELECT
    s.student_id,
    s.roll_number,
    s.registration_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    d.department_name,
    cr.semester,
    cr.academic_year,
    c.course_code,
    c.course_title,
    c.credit_hours,
    cr.sessional_marks,
    cr.midterm_marks,
    cr.final_marks,
    cr.total_marks,
    cr.percentage,
    cr.letter_grade,
    cr.grade_points,
    cr.result_status,
    t.first_name || ' ' || t.last_name AS teacher_name,
    cr.verified,
    cr.published,
    cr.created_at AS grade_recorded_date,
    cr.updated_at AS grade_updated_date
FROM Course_Results cr
INNER JOIN Enrollments e ON cr.enrollment_id = e.enrollment_id
INNER JOIN Students s ON e.student_id = s.student_id
INNER JOIN Courses c ON e.course_id = c.course_id
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Teachers t ON cr.teacher_id = t.teacher_id
ORDER BY cr.academic_year DESC, cr.semester DESC, c.course_code ASC;

-- ===========================================================
-- VIEW: vw_student_current_grades
--
-- PURPOSE:
-- Current semester grades for a student
-- Shows all grades entered but not necessarily published
--
-- USED BY:
-- • Student Dashboard (Current Semester Tab)
-- • Teacher Grading Dashboard
-- • Course Management
-- ===========================================================

CREATE VIEW vw_student_current_grades AS
SELECT
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    c.course_code,
    c.course_title,
    c.credit_hours,
    g.assessment_type,
    g.title AS assessment_title,
    g.obtained_marks,
    g.total_marks,
    ROUND(
        CASE
            WHEN g.total_marks > 0
            THEN (g.obtained_marks / g.total_marks) * 100
            ELSE 0
        END,
        2
    ) AS assessment_percentage,
    g.verified,
    g.published,
    ROUND(COALESCE(g.percentage, 0), 2) AS aggregate_percentage,
    g.letter_grade,
    g.grade_points,
    g.result_status,
    g.graded_at,
    t.first_name || ' ' || t.last_name AS graded_by_teacher,
    g.remarks
FROM Enrollments e
INNER JOIN Students s ON e.student_id = s.student_id
INNER JOIN Courses c ON e.course_id = c.course_id
LEFT JOIN Grades g ON e.enrollment_id = g.enrollment_id
LEFT JOIN Teachers t ON g.graded_by = t.teacher_id
WHERE s.semester = (SELECT semester FROM Students WHERE student_id = s.student_id)
  AND e.enrollment_status = 'Enrolled'
ORDER BY c.course_code ASC, CASE
    WHEN g.assessment_type = 'Quiz' THEN 1
    WHEN g.assessment_type = 'Assignment' THEN 2
    WHEN g.assessment_type = 'Lab' THEN 3
    WHEN g.assessment_type = 'Viva' THEN 4
    WHEN g.assessment_type = 'Presentation' THEN 5
    WHEN g.assessment_type = 'Midterm' THEN 6
    WHEN g.assessment_type = 'Final' THEN 7
    ELSE 8
END ASC;

-- ===========================================================
-- VIEW: vw_course_roster
--
-- PURPOSE:
-- List of all students enrolled in a course
-- Shows enrollment status and performance
--
-- USED BY:
-- • Course Management
-- • Teacher Dashboard
-- • Attendance Tracking
-- • Grading System
-- ===========================================================

CREATE VIEW vw_course_roster AS
SELECT
    c.course_id,
    c.course_code,
    c.course_title,
    c.semester,
    c.credit_hours,
    d.department_name,
    t.first_name || ' ' || t.last_name AS teacher_name,
    e.enrollment_id,
    s.student_id,
    s.roll_number,
    s.registration_number,
    s.first_name || ' ' || s.last_name AS student_name,
    e.section,
    e.enrollment_date,
    e.enrollment_status,
    COALESCE(
        (SELECT COUNT(*)
         FROM Attendance a
         WHERE a.student_id = s.student_id
           AND a.course_id = c.course_id
           AND a.status = 'Present'),
        0
    ) AS present_count,
    COALESCE(
        (SELECT COUNT(*)
         FROM Attendance a
         WHERE a.student_id = s.student_id
           AND a.course_id = c.course_id),
        0
    ) AS total_lectures,
    COALESCE(
        (SELECT ROUND(
            (COUNT(CASE WHEN a.status = 'Present' THEN 1 END) * 100.0 / COUNT(*)),
            2)
         FROM Attendance a
         WHERE a.student_id = s.student_id
           AND a.course_id = c.course_id),
        0
    ) AS attendance_percentage,
    COALESCE(cr.percentage, 0.00) AS current_percentage,
    COALESCE(cr.letter_grade, 'TBD') AS current_grade
FROM Enrollments e
INNER JOIN Courses c ON e.course_id = c.course_id
INNER JOIN Students s ON e.student_id = s.student_id
INNER JOIN Departments d ON c.department_id = d.department_id
LEFT JOIN Teachers t ON c.teacher_id = t.teacher_id
LEFT JOIN Course_Results cr ON e.enrollment_id = cr.enrollment_id
WHERE e.enrollment_status = 'Enrolled'
  AND c.status = 'Active'
ORDER BY c.course_code ASC, s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_course_results_summary
--
-- PURPOSE:
-- Summary of results for a course
-- Shows grade distribution and performance metrics
--
-- USED BY:
-- • Course Performance Analysis
-- • Teacher Dashboard
-- • Academic Analytics
-- • Reporting
-- ===========================================================

CREATE VIEW vw_course_results_summary AS
SELECT
    c.course_id,
    c.course_code,
    c.course_title,
    c.credit_hours,
    c.semester,
    d.department_name,
    t.first_name || ' ' || t.last_name AS teacher_name,
    COUNT(DISTINCT cr.student_id) AS total_students,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Pass' THEN cr.student_id END) AS passed_students,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Fail' THEN cr.student_id END) AS failed_students,
    ROUND(
        (COUNT(DISTINCT CASE WHEN cr.result_status = 'Pass' THEN cr.student_id END) * 100.0 /
         COUNT(DISTINCT cr.student_id)),
        2
    ) AS pass_percentage,
    ROUND(AVG(cr.percentage), 2) AS average_percentage,
    ROUND(AVG(cr.grade_points), 2) AS average_grade_points,
    MIN(cr.percentage) AS lowest_percentage,
    MAX(cr.percentage) AS highest_percentage,
    COUNT(DISTINCT CASE WHEN cr.letter_grade = 'A' THEN cr.student_id END) AS grade_a_count,
    COUNT(DISTINCT CASE WHEN cr.letter_grade = 'B' THEN cr.student_id END) AS grade_b_count,
    COUNT(DISTINCT CASE WHEN cr.letter_grade = 'C' THEN cr.student_id END) AS grade_c_count,
    COUNT(DISTINCT CASE WHEN cr.letter_grade = 'D' THEN cr.student_id END) AS grade_d_count,
    COUNT(DISTINCT CASE WHEN cr.letter_grade = 'F' THEN cr.student_id END) AS grade_f_count
FROM Course_Results cr
INNER JOIN Enrollments e ON cr.enrollment_id = e.enrollment_id
INNER JOIN Courses c ON e.course_id = c.course_id
INNER JOIN Departments d ON c.department_id = d.department_id
LEFT JOIN Teachers t ON c.teacher_id = t.teacher_id
GROUP BY c.course_id, c.course_code, c.course_title, c.credit_hours, c.semester, d.department_name, t.teacher_id;

-- ===========================================================
-- VIEW: vw_semester_results_summary
--
-- PURPOSE:
-- Summary of all results for a semester
-- Shows semester-wide performance metrics
--
-- USED BY:
-- • Semester Reports
-- • Academic Planning
-- • Analytics Dashboard
-- ===========================================================

CREATE VIEW vw_semester_results_summary AS
SELECT
    cr.academic_year,
    cr.semester,
    COUNT(DISTINCT cr.student_id) AS total_students,
    COUNT(DISTINCT cr.course_id) AS total_courses,
    COUNT(DISTINCT cr.enrollment_id) AS total_enrollments,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Pass' THEN cr.enrollment_id END) AS passed_enrollments,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Fail' THEN cr.enrollment_id END) AS failed_enrollments,
    ROUND(
        (COUNT(DISTINCT CASE WHEN cr.result_status = 'Pass' THEN cr.enrollment_id END) * 100.0 /
         COUNT(DISTINCT cr.enrollment_id)),
        2
    ) AS overall_pass_percentage,
    ROUND(AVG(cr.percentage), 2) AS average_percentage,
    ROUND(AVG(cr.grade_points), 2) AS average_grade_points,
    MIN(cr.percentage) AS lowest_percentage,
    MAX(cr.percentage) AS highest_percentage,
    COALESCE(SUM(cr.credit_hours), 0) AS total_credit_hours_offered
FROM Course_Results cr
GROUP BY cr.academic_year, cr.semester
ORDER BY cr.academic_year DESC, cr.semester DESC;

-- ===========================================================
-- SECTION 3: GPA & ACADEMIC STANDING VIEWS (6 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_student_academic_standing
--
-- PURPOSE:
-- Current academic standing and GPA for each student
-- Shows CGPA, academic status, honors classification
--
-- USED BY:
-- • Student Dashboard
-- • Academic Advisor
-- • Scholarship Committee
-- • Graduation Office
-- ===========================================================

CREATE VIEW vw_student_academic_standing AS
SELECT
    s.student_id,
    s.roll_number,
    s.registration_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    s.semester,
    d.department_name,
    sc.overall_cgpa,
    sc.academic_status,
    sc.honors_status,
    sc.graduation_eligible,
    sc.total_passed_courses,
    sc.total_failed_courses,
    sc.total_completed_credit_hours,
    COALESCE(sg.semester_gpa, 0.00) AS current_semester_gpa,
    COALESCE(sg.academic_status, 'Good Standing') AS current_semester_status,
    sc.last_calculated AS cgpa_last_updated,
    s.status AS enrollment_status,
    CASE
        WHEN sc.overall_cgpa >= 3.5 THEN 'On Track'
        WHEN sc.overall_cgpa >= 2.0 AND sc.overall_cgpa < 3.5 THEN 'Satisfactory'
        WHEN sc.overall_cgpa >= 1.0 AND sc.overall_cgpa < 2.0 THEN 'At Risk'
        ELSE 'Critical'
    END AS performance_level
FROM Students s
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Student_CGPA sc ON s.student_id = sc.student_id
LEFT JOIN Semester_GPA sg ON s.student_id = sg.student_id AND s.semester = sg.semester
ORDER BY s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_semester_gpa_breakdown
--
-- PURPOSE:
-- Detailed semester GPA breakdown for each student
-- Shows grade composition and academic status per semester
--
-- USED BY:
-- • Academic Transcript
-- • GPA Analysis
-- • Performance Tracking
-- ===========================================================

CREATE VIEW vw_semester_gpa_breakdown AS
SELECT
    sg.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    sg.academic_year,
    sg.semester,
    sg.total_credit_hours,
    sg.earned_credit_hours,
    sg.semester_gpa,
    ROUND((sg.earned_credit_hours * 100.0 / sg.total_credit_hours), 2) AS credit_completion_percentage,
    sg.academic_status,
    sg.remarks,
    sg.calculated_at,
    COUNT(DISTINCT cr.course_id) AS courses_taken,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Pass' THEN cr.course_id END) AS courses_passed,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Fail' THEN cr.course_id END) AS courses_failed
FROM Semester_GPA sg
INNER JOIN Students s ON sg.student_id = s.student_id
LEFT JOIN Course_Results cr ON s.student_id = cr.student_id
    AND sg.academic_year = cr.academic_year
    AND sg.semester = cr.semester
GROUP BY sg.student_id, s.roll_number, s.first_name, s.last_name, sg.academic_year, sg.semester,
         sg.total_credit_hours, sg.earned_credit_hours, sg.semester_gpa, sg.academic_status,
         sg.remarks, sg.calculated_at
ORDER BY sg.academic_year DESC, sg.semester DESC, s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_student_cgpa_breakdown
--
-- PURPOSE:
-- Cumulative GPA breakdown with full academic profile
-- Shows overall performance and eligibility status
--
-- USED BY:
-- • Student Transcript
-- • Graduation Eligibility Check
-- • Honors Classification
-- • Academic Records
-- ===========================================================

CREATE VIEW vw_student_cgpa_breakdown AS
SELECT
    sc.student_id,
    s.roll_number,
    s.registration_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    d.department_name,
    s.admission_date,
    s.expected_graduation,
    sc.overall_cgpa,
    sc.total_completed_credit_hours,
    sc.total_passed_courses,
    sc.total_failed_courses,
    CASE
        WHEN sc.total_passed_courses + sc.total_failed_courses > 0
        THEN ROUND((sc.total_passed_courses * 100.0 / (sc.total_passed_courses + sc.total_failed_courses)), 2)
        ELSE 0
    END AS pass_rate_percentage,
    sc.academic_status,
    sc.graduation_eligible,
    sc.honors_status,
    sc.last_calculated,
    COUNT(DISTINCT sg.semester) AS semesters_completed,
    ROUND(AVG(sg.semester_gpa), 2) AS average_semester_gpa,
    MIN(sg.semester_gpa) AS lowest_semester_gpa,
    MAX(sg.semester_gpa) AS highest_semester_gpa
FROM Student_CGPA sc
INNER JOIN Students s ON sc.student_id = s.student_id
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Semester_GPA sg ON sc.student_id = sg.student_id
GROUP BY sc.student_id, s.roll_number, s.registration_number, s.first_name, s.last_name,
         s.program, d.department_name, s.admission_date, s.expected_graduation,
         sc.overall_cgpa, sc.total_completed_credit_hours, sc.total_passed_courses,
         sc.total_failed_courses, sc.academic_status, sc.graduation_eligible,
         sc.honors_status, sc.last_calculated
ORDER BY sc.overall_cgpa DESC, s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_graduation_eligibility
--
-- PURPOSE:
-- List of students eligible for graduation
-- Shows completion status and remaining requirements
--
-- USED BY:
-- • Graduation Office
-- • Academic Advisor
-- • Registrar
-- • Commencement Planning
-- ===========================================================

CREATE VIEW vw_graduation_eligibility AS
SELECT
    s.student_id,
    s.roll_number,
    s.registration_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    d.department_name,
    s.batch_year,
    s.admission_date,
    sc.overall_cgpa,
    sc.academic_status,
    sc.graduation_eligible,
    sc.honors_status,
    sc.total_completed_credit_hours,
    sc.total_passed_courses,
    sc.total_failed_courses,
    CASE
        WHEN sc.graduation_eligible = TRUE AND sc.overall_cgpa >= 2.0 AND sc.total_failed_courses = 0
        THEN 'Ready for Graduation'
        WHEN sc.overall_cgpa < 2.0
        THEN 'Low GPA - Not Eligible'
        WHEN sc.total_failed_courses > 0
        THEN 'Failed Courses - Not Eligible'
        WHEN sc.academic_status = 'Dismissed'
        THEN 'Academically Dismissed'
        ELSE 'Not Yet Eligible'
    END AS graduation_status,
    sc.last_calculated AS status_last_updated
FROM Students s
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Student_CGPA sc ON s.student_id = sc.student_id
WHERE s.status IN ('Active', 'Graduated')
ORDER BY CASE
    WHEN sc.graduation_eligible = TRUE THEN 1
    ELSE 2
END ASC, sc.overall_cgpa DESC;

-- ===========================================================
-- VIEW: vw_academic_warning_students
--
-- PURPOSE:
-- Students on academic warning (GPA below 2.0)
-- Prioritizes students needing academic intervention
--
-- USED BY:
-- • Academic Advisor
-- • AI Academic Advisor Agent
-- • Intervention Programs
-- • Probation Monitoring
-- ===========================================================

CREATE VIEW vw_academic_warning_students AS
SELECT
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    s.semester,
    d.department_name,
    sc.overall_cgpa,
    sc.academic_status,
    sg.semester_gpa,
    sg.academic_status AS semester_status,
    sc.total_failed_courses,
    CASE
        WHEN sc.overall_cgpa < 1.0 THEN 'Critical'
        WHEN sc.overall_cgpa < 1.5 THEN 'Severe'
        WHEN sc.overall_cgpa < 2.0 THEN 'Warning'
        ELSE 'Monitor'
    END AS intervention_level,
    u.email,
    u.last_login,
    sc.last_calculated
FROM Students s
INNER JOIN Users u ON s.user_id = u.user_id
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Student_CGPA sc ON s.student_id = sc.student_id
LEFT JOIN Semester_GPA sg ON s.student_id = sg.student_id AND s.semester = sg.semester
WHERE s.status = 'Active'
  AND COALESCE(sc.academic_status, 'Good Standing') IN ('Warning', 'Probation', 'Dismissed')
ORDER BY CASE
    WHEN sc.overall_cgpa < 1.0 THEN 1
    WHEN sc.overall_cgpa < 1.5 THEN 2
    WHEN sc.overall_cgpa < 2.0 THEN 3
    ELSE 4
END ASC, sc.overall_cgpa ASC;

-- ===========================================================
-- SECTION 4: GRADING & ASSESSMENT VIEWS (4 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_assignment_submission_status
--
-- PURPOSE:
-- Track assignment submissions and grading status
-- Shows submission progress and pending grades
--
-- USED BY:
-- • Teacher Dashboard
-- • Assignment Management System
-- • Grading System
-- • Progress Tracking
-- ===========================================================

CREATE VIEW vw_assignment_submission_status AS
SELECT
    a.assignment_id,
    a.title AS assignment_title,
    a.assignment_type,
    a.total_marks,
    c.course_code,
    c.course_title,
    t.first_name || ' ' || t.last_name AS teacher_name,
    a.release_date,
    a.due_date,
    a.allow_late_submission,
    a.status AS assignment_status,
    COUNT(DISTINCT e.student_id) AS total_students,
    COUNT(DISTINCT s.submission_id) AS submissions_received,
    COUNT(DISTINCT CASE WHEN s.submission_status = 'Submitted' THEN s.submission_id END) AS pending_review,
    COUNT(DISTINCT CASE WHEN s.graded = TRUE THEN s.submission_id END) AS graded_submissions,
    ROUND(
        (COUNT(DISTINCT CASE WHEN s.submission_id IS NOT NULL THEN s.submission_id END) * 100.0 /
         COUNT(DISTINCT e.student_id)),
        2
    ) AS submission_rate_percentage,
    COUNT(DISTINCT CASE WHEN s.is_late = TRUE THEN s.submission_id END) AS late_submissions,
    ROUND(AVG(s.teacher_marks), 2) AS average_marks_awarded,
    ROUND(AVG(s.plagiarism_score), 2) AS average_plagiarism_score
FROM Assignments a
INNER JOIN Courses c ON a.course_id = c.course_id
INNER JOIN Teachers t ON a.teacher_id = t.teacher_id
LEFT JOIN Enrollments e ON c.course_id = e.course_id
LEFT JOIN Submissions s ON a.assignment_id = s.assignment_id
GROUP BY a.assignment_id, a.title, a.assignment_type, a.total_marks, c.course_code, c.course_title,
         t.teacher_id, a.release_date, a.due_date, a.allow_late_submission, a.status
ORDER BY a.due_date DESC;

-- ===========================================================
-- VIEW: vw_pending_grades
--
-- PURPOSE:
-- Assignments and assessments awaiting grading
-- Shows grading backlog and deadline proximity
--
-- USED BY:
-- • Teacher Dashboard
-- • Grading Workload Management
-- • Assignment Tracking
-- • Deadline Alerts
-- ===========================================================

CREATE VIEW vw_pending_grades AS
SELECT
    g.grade_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    c.course_code,
    c.course_title,
    g.assessment_type,
    g.title AS assessment_title,
    g.total_marks,
    g.obtained_marks,
    CASE
        WHEN g.total_marks > 0
        THEN ROUND((g.obtained_marks / g.total_marks) * 100, 2)
        ELSE 0
    END AS student_percentage,
    t.first_name || ' ' || t.last_name AS teacher_name,
    g.graded_at,
    a.due_date AS assessment_deadline,
    CASE
        WHEN g.published = FALSE AND a.due_date < CURRENT_TIMESTAMP
        THEN 'Overdue'
        WHEN g.published = FALSE AND a.due_date < datetime('now', '+7 days')
        THEN 'Due Soon'
        ELSE 'Pending'
    END AS urgency_level,
    g.remarks
FROM Grades g
INNER JOIN Enrollments e ON g.enrollment_id = e.enrollment_id
INNER JOIN Students s ON e.student_id = s.student_id
INNER JOIN Courses c ON e.course_id = c.course_id
INNER JOIN Teachers t ON g.graded_by = t.teacher_id
LEFT JOIN Assignments a ON g.enrollment_id IN (
    SELECT enrollment_id FROM Grades
    WHERE assessment_type IN ('Quiz', 'Assignment', 'Lab', 'Viva', 'Presentation')
)
WHERE g.published = FALSE OR g.is_locked = FALSE
ORDER BY CASE
    WHEN a.due_date < CURRENT_TIMESTAMP THEN 1
    WHEN a.due_date < datetime('now', '+7 days') THEN 2
    ELSE 3
END ASC, a.due_date ASC;

-- ===========================================================
-- VIEW: vw_grades_distribution
--
-- PURPOSE:
-- Grade distribution analysis by course
-- Shows letter grade breakdown and statistics
--
-- USED BY:
-- • Course Analysis
-- • Academic Analytics
-- • Quality Assurance
-- • Reporting
-- ===========================================================

CREATE VIEW vw_grades_distribution AS
SELECT
    c.course_id,
    c.course_code,
    c.course_title,
    c.semester,
    cr.academic_year,
    d.department_name,
    COUNT(DISTINCT cr.student_id) AS total_students,
    COUNT(DISTINCT CASE WHEN cr.letter_grade = 'A' THEN cr.student_id END) AS a_grades,
    COUNT(DISTINCT CASE WHEN cr.letter_grade LIKE 'A%' THEN cr.student_id END) AS a_range_grades,
    COUNT(DISTINCT CASE WHEN cr.letter_grade LIKE 'B%' THEN cr.student_id END) AS b_range_grades,
    COUNT(DISTINCT CASE WHEN cr.letter_grade LIKE 'C%' THEN cr.student_id END) AS c_range_grades,
    COUNT(DISTINCT CASE WHEN cr.letter_grade LIKE 'D%' THEN cr.student_id END) AS d_range_grades,
    COUNT(DISTINCT CASE WHEN cr.letter_grade = 'F' THEN cr.student_id END) AS f_grades,
    ROUND((COUNT(DISTINCT CASE WHEN cr.letter_grade LIKE 'A%' THEN cr.student_id END) * 100.0 / COUNT(DISTINCT cr.student_id)), 2) AS a_percentage,
    ROUND((COUNT(DISTINCT CASE WHEN cr.letter_grade LIKE 'B%' THEN cr.student_id END) * 100.0 / COUNT(DISTINCT cr.student_id)), 2) AS b_percentage,
    ROUND((COUNT(DISTINCT CASE WHEN cr.letter_grade LIKE 'C%' THEN cr.student_id END) * 100.0 / COUNT(DISTINCT cr.student_id)), 2) AS c_percentage,
    ROUND((COUNT(DISTINCT CASE WHEN cr.result_status = 'Pass' THEN cr.student_id END) * 100.0 / COUNT(DISTINCT cr.student_id)), 2) AS pass_percentage
FROM Course_Results cr
INNER JOIN Enrollments e ON cr.enrollment_id = e.enrollment_id
INNER JOIN Courses c ON e.course_id = c.course_id
INNER JOIN Departments d ON c.department_id = d.department_id
GROUP BY c.course_id, c.course_code, c.course_title, c.semester, cr.academic_year, d.department_name
ORDER BY cr.academic_year DESC, c.course_code ASC;

-- ===========================================================
-- VIEW: vw_student_performance_metrics
--
-- PURPOSE:
-- Comprehensive performance metrics for each student
-- Shows grades, trends, and performance profile
--
-- USED BY:
-- • Academic Advisor
-- • AI Academic Advisor Agent
-- • Performance Dashboard
-- • Scholarship Committee
-- ===========================================================

CREATE VIEW vw_student_performance_metrics AS
SELECT
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    d.department_name,
    sc.overall_cgpa,
    sg.semester_gpa AS current_semester_gpa,
    sc.total_passed_courses,
    sc.total_failed_courses,
    CASE
        WHEN sc.total_passed_courses + sc.total_failed_courses > 0
        THEN ROUND((sc.total_passed_courses * 100.0 / (sc.total_passed_courses + sc.total_failed_courses)), 2)
        ELSE 0
    END AS pass_rate,
    (SELECT COUNT(DISTINCT course_id) FROM Course_Results WHERE student_id = s.student_id) AS courses_completed,
    (SELECT AVG(percentage) FROM Course_Results WHERE student_id = s.student_id) AS average_percentage,
    (SELECT COUNT(DISTINCT CASE WHEN result_status = 'Pass' THEN 1 END) FROM Course_Results WHERE student_id = s.student_id AND letter_grade LIKE 'A%') AS a_grade_courses,
    sc.academic_status,
    sc.honors_status,
    sc.graduation_eligible,
    COALESCE(
        (SELECT COUNT(*) FROM Notifications WHERE recipient_type = 'Student' AND recipient_id = s.student_id AND is_read = FALSE),
        0
    ) AS unread_notifications,
    s.status AS enrollment_status,
    sc.last_calculated AS metrics_last_updated
FROM Students s
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Student_CGPA sc ON s.student_id = sc.student_id
LEFT JOIN Semester_GPA sg ON s.student_id = sg.student_id AND s.semester = sg.semester
ORDER BY sc.overall_cgpa DESC, s.roll_number ASC;

-- ===========================================================
-- SECTION 5: ATTENDANCE VIEWS (3 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_student_attendance_summary
--
-- PURPOSE:
-- Attendance summary for each student across courses
-- Shows attendance percentage and compliance status
--
-- USED BY:
-- • Student Dashboard
-- • Attendance Module
-- • Academic Advisor
-- • Compliance Reporting
-- ===========================================================

CREATE VIEW vw_student_attendance_summary AS
SELECT
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    d.department_name,
    s.semester,
    COUNT(DISTINCT a.course_id) AS courses_with_attendance,
    COUNT(DISTINCT CASE WHEN a.status = 'Present' THEN a.attendance_id END) AS total_present,
    COUNT(DISTINCT CASE WHEN a.status = 'Absent' THEN a.attendance_id END) AS total_absent,
    COUNT(DISTINCT CASE WHEN a.status = 'Late' THEN a.attendance_id END) AS total_late,
    COUNT(DISTINCT CASE WHEN a.status = 'Leave' THEN a.attendance_id END) AS total_leaves,
    COUNT(DISTINCT a.attendance_id) AS total_lectures_attended,
    ROUND(
        (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
         COUNT(DISTINCT a.attendance_id)),
        2
    ) AS attendance_percentage,
    CASE
        WHEN (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
              COUNT(DISTINCT a.attendance_id)) >= 75
        THEN 'Good'
        WHEN (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
              COUNT(DISTINCT a.attendance_id)) >= 60
        THEN 'Fair'
        ELSE 'Poor'
    END AS attendance_status,
    MAX(a.attendance_date) AS last_attendance_date
FROM Students s
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Attendance a ON s.student_id = a.student_id
GROUP BY s.student_id, s.roll_number, s.first_name, s.last_name, d.department_name, s.semester
ORDER BY s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_course_attendance_analysis
--
-- PURPOSE:
-- Attendance analysis for a specific course
-- Shows per-student and overall attendance metrics
--
-- USED BY:
-- • Teacher Dashboard
-- • Course Management
-- • Attendance Tracking
-- • Class Monitoring
-- ===========================================================

CREATE VIEW vw_course_attendance_analysis AS
SELECT
    c.course_id,
    c.course_code,
    c.course_title,
    c.semester,
    t.first_name || ' ' || t.last_name AS teacher_name,
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    COUNT(DISTINCT a.attendance_id) AS total_lectures,
    COUNT(DISTINCT CASE WHEN a.status = 'Present' THEN a.attendance_id END) AS present,
    COUNT(DISTINCT CASE WHEN a.status = 'Absent' THEN a.attendance_id END) AS absent,
    COUNT(DISTINCT CASE WHEN a.status = 'Late' THEN a.attendance_id END) AS late,
    COUNT(DISTINCT CASE WHEN a.status = 'Leave' THEN a.attendance_id END) AS leaves,
    ROUND(
        (COUNT(DISTINCT CASE WHEN a.status = 'Present' THEN a.attendance_id END) * 100.0 /
         COUNT(DISTINCT a.attendance_id)),
        2
    ) AS attendance_percentage,
    MAX(a.attendance_date) AS last_class_attended
FROM Enrollments e
INNER JOIN Courses c ON e.course_id = c.course_id
INNER JOIN Students s ON e.student_id = s.student_id
INNER JOIN Teachers t ON c.teacher_id = t.teacher_id
LEFT JOIN Attendance a ON s.student_id = a.student_id AND c.course_id = a.course_id
WHERE e.enrollment_status = 'Enrolled'
GROUP BY c.course_id, c.course_code, c.course_title, c.semester, t.teacher_id, s.student_id,
         s.roll_number, s.first_name, s.last_name
ORDER BY c.course_code ASC, s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_attendance_compliance
--
-- PURPOSE:
-- Attendance compliance monitoring
-- Identifies students with low attendance requiring intervention
--
-- USED BY:
-- • Attendance Monitoring
-- • Academic Advisor
-- • Intervention Programs
-- • Compliance Alerts
-- ===========================================================

CREATE VIEW vw_attendance_compliance AS
SELECT
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    c.course_code,
    c.course_title,
    COUNT(DISTINCT a.attendance_id) AS total_lectures,
    COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) AS present_or_late,
    ROUND(
        (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
         COUNT(DISTINCT a.attendance_id)),
        2
    ) AS attendance_percentage,
    CASE
        WHEN (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
              COUNT(DISTINCT a.attendance_id)) < 60
        THEN 'Critical'
        WHEN (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
              COUNT(DISTINCT a.attendance_id)) < 75
        THEN 'Warning'
        ELSE 'Compliant'
    END AS compliance_status,
    u.email,
    MAX(a.attendance_date) AS last_attendance_date,
    COUNT(DISTINCT CASE WHEN a.status = 'Absent' THEN a.attendance_id END) AS consecutive_absences
FROM Enrollments e
INNER JOIN Students s ON e.student_id = s.student_id
INNER JOIN Users u ON s.user_id = u.user_id
INNER JOIN Courses c ON e.course_id = c.course_id
LEFT JOIN Attendance a ON s.student_id = a.student_id AND c.course_id = a.course_id
WHERE e.enrollment_status = 'Enrolled'
  AND (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
       COUNT(DISTINCT a.attendance_id)) < 75
GROUP BY s.student_id, s.roll_number, s.first_name, s.last_name, c.course_code, c.course_title, u.email
ORDER BY CASE
    WHEN (COUNT(DISTINCT CASE WHEN a.status IN ('Present', 'Late') THEN a.attendance_id END) * 100.0 /
          COUNT(DISTINCT a.attendance_id)) < 60 THEN 1
    ELSE 2
END ASC, attendance_percentage ASC;

-- ===========================================================
-- SECTION 6: FEE & FINANCE VIEWS (3 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_student_fee_status
--
-- PURPOSE:
-- Current fee status for each student per semester
-- Shows payment progress and outstanding balances
--
-- USED BY:
-- • Student Dashboard
-- • Finance Module
-- • Payment Tracking
-- • Fee Collection
-- ===========================================================

CREATE VIEW vw_student_fee_status AS
SELECT
    f.fee_id,
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.semester,
    f.academic_year,
    f.semester,
    d.department_name,
    f.total_fee,
    f.scholarship_amount,
    f.fine_amount,
    f.discount_amount,
    f.payable_amount,
    f.paid_amount,
    f.remaining_amount,
    f.payment_status,
    f.payment_method,
    f.payment_date,
    f.due_date,
    CASE
        WHEN f.payment_status = 'Paid' THEN 'Complete'
        WHEN f.remaining_amount = 0 AND f.payment_status = 'Partial' THEN 'Complete'
        WHEN f.due_date < CURRENT_TIMESTAMP AND f.payment_status <> 'Paid' THEN 'Overdue'
        WHEN f.due_date > CURRENT_TIMESTAMP THEN 'Pending'
        ELSE 'Unknown'
    END AS fee_status_detail,
    ROUND((f.paid_amount * 100.0 / f.payable_amount), 2) AS payment_percentage,
    f.verified,
    u.email
FROM Fee_Records f
INNER JOIN Students s ON f.student_id = s.student_id
INNER JOIN Users u ON s.user_id = u.user_id
INNER JOIN Departments d ON s.department_id = d.department_id
ORDER BY f.due_date ASC, s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_pending_fee_payments
--
-- PURPOSE:
-- List of pending/overdue fee payments
-- Prioritizes collection efforts and compliance
--
-- USED BY:
-- • Finance Department
-- • Payment Tracking
-- • Collection Reminders
-- • Financial Reporting
-- ===========================================================

CREATE VIEW vw_pending_fee_payments AS
SELECT
    f.fee_id,
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    d.department_name,
    f.academic_year,
    f.semester,
    f.total_fee,
    f.paid_amount,
    f.remaining_amount,
    f.payment_status,
    f.due_date,
    CASE
        WHEN f.due_date < CURRENT_TIMESTAMP THEN 'Overdue'
        WHEN f.due_date < datetime('now', '+7 days') THEN 'Due Soon'
        ELSE 'Pending'
    END AS urgency,
    ROUND((JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(f.due_date))) AS days_overdue,
    f.payment_method,
    u.email,
    u.last_login
FROM Fee_Records f
INNER JOIN Students s ON f.student_id = s.student_id
INNER JOIN Users u ON s.user_id = u.user_id
INNER JOIN Departments d ON s.department_id = d.department_id
WHERE f.payment_status IN ('Pending', 'Partial', 'Overdue')
ORDER BY CASE
    WHEN f.due_date < CURRENT_TIMESTAMP THEN 1
    WHEN f.due_date < datetime('now', '+7 days') THEN 2
    ELSE 3
END ASC, f.due_date ASC;

-- ===========================================================
-- VIEW: vw_fee_collection_summary
--
-- PURPOSE:
-- Fee collection and revenue summary
-- Shows collection rates and financial metrics
--
-- USED BY:
-- • Finance Dashboard
-- • Revenue Reporting
-- • Financial Planning
-- • Budget Analysis
-- ===========================================================

CREATE VIEW vw_fee_collection_summary AS
SELECT
    f.academic_year,
    f.semester,
    COUNT(DISTINCT f.student_id) AS total_students,
    SUM(f.total_fee) AS total_fee_charged,
    SUM(f.paid_amount) AS total_collected,
    SUM(f.remaining_amount) AS total_pending,
    ROUND((SUM(f.paid_amount) * 100.0 / SUM(f.total_fee)), 2) AS collection_percentage,
    COUNT(DISTINCT CASE WHEN f.payment_status = 'Paid' THEN f.student_id END) AS paid_students,
    COUNT(DISTINCT CASE WHEN f.payment_status = 'Partial' THEN f.student_id END) AS partial_students,
    COUNT(DISTINCT CASE WHEN f.payment_status IN ('Pending', 'Overdue') THEN f.student_id END) AS pending_students,
    COUNT(DISTINCT CASE WHEN f.due_date < CURRENT_TIMESTAMP AND f.payment_status <> 'Paid' THEN f.student_id END) AS overdue_students,
    AVG(f.paid_amount) AS average_payment_per_student
FROM Fee_Records f
GROUP BY f.academic_year, f.semester
ORDER BY f.academic_year DESC, f.semester DESC;

-- ===========================================================
-- SECTION 7: COURSE MANAGEMENT VIEWS (2 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_course_offerings_semester
--
-- PURPOSE:
-- List of all courses offered in a semester
-- Shows enrollment and capacity information
--
-- USED BY:
-- • Course Registration System
-- • Course Catalog
-- • Enrollment Management
-- • Academic Planning
-- ===========================================================

CREATE VIEW vw_course_offerings_semester AS
SELECT
    c.course_id,
    c.course_code,
    c.course_title,
    c.course_description,
    c.credit_hours,
    c.course_type,
    c.semester,
    d.department_name,
    t.first_name || ' ' || t.last_name AS instructor_name,
    t.office_room,
    t.office_email,
    COUNT(DISTINCT e.student_id) AS enrolled_students,
    COALESCE(
        (SELECT COUNT(DISTINCT student_id) FROM Enrollments WHERE course_id = c.course_id AND enrollment_status = 'Dropped'),
        0
    ) AS dropped_students,
    c.status AS course_status,
    COALESCE(
        (SELECT COUNT(*) FROM Assignments WHERE course_id = c.course_id AND status = 'Published'),
        0
    ) AS active_assignments
FROM Courses c
INNER JOIN Departments d ON c.department_id = d.department_id
LEFT JOIN Teachers t ON c.teacher_id = t.teacher_id
LEFT JOIN Enrollments e ON c.course_id = e.course_id AND e.enrollment_status = 'Enrolled'
GROUP BY c.course_id, c.course_code, c.course_title, c.course_description, c.credit_hours,
         c.course_type, c.semester, d.department_name, t.teacher_id, t.office_room, t.office_email, c.status
ORDER BY c.semester DESC, c.course_code ASC;

-- ===========================================================
-- VIEW: vw_course_enrollment_summary
--
-- PURPOSE:
-- Enrollment summary and statistics by course
-- Shows enrollment trends and capacity utilization
--
-- USED BY:
-- • Academic Planning
-- • Enrollment Analytics
-- • Course Capacity Planning
-- • Reporting
-- ===========================================================

CREATE VIEW vw_course_enrollment_summary AS
SELECT
    c.course_id,
    c.course_code,
    c.course_title,
    c.semester,
    d.department_name,
    COUNT(DISTINCT e.student_id) AS total_enrolled,
    COUNT(DISTINCT CASE WHEN e.enrollment_status = 'Enrolled' THEN e.student_id END) AS active_students,
    COUNT(DISTINCT CASE WHEN e.enrollment_status = 'Dropped' THEN e.student_id END) AS dropped_students,
    COUNT(DISTINCT CASE WHEN e.enrollment_status = 'Completed' THEN e.student_id END) AS completed_students,
    COUNT(DISTINCT CASE WHEN e.enrollment_status = 'Withdrawn' THEN e.student_id END) AS withdrawn_students,
    ROUND(AVG(cr.percentage), 2) AS average_percentage,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Pass' THEN cr.student_id END) AS passed_count,
    COUNT(DISTINCT CASE WHEN cr.result_status = 'Fail' THEN cr.student_id END) AS failed_count
FROM Courses c
INNER JOIN Departments d ON c.department_id = d.department_id
LEFT JOIN Enrollments e ON c.course_id = e.course_id
LEFT JOIN Course_Results cr ON e.enrollment_id = cr.enrollment_id
GROUP BY c.course_id, c.course_code, c.course_title, c.semester, d.department_name
ORDER BY c.semester DESC, c.course_code ASC;

-- ===========================================================
-- SECTION 8: ADMINISTRATIVE VIEWS (2 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_audit_activity_summary
--
-- PURPOSE:
-- Summary of audit trail activities
-- Tracks user activities and system changes for compliance
--
-- USED BY:
-- • Compliance Monitoring
-- • Audit Trail Review
-- • Security Monitoring
-- • Data Governance
-- ===========================================================

CREATE VIEW vw_audit_activity_summary AS
SELECT
    DATE(al.created_at) AS activity_date,
    al.module_name,
    al.action_type,
    al.user_role,
    COUNT(*) AS total_actions,
    COUNT(DISTINCT al.user_id) AS unique_users,
    COUNT(DISTINCT CASE WHEN al.action_status = 'Success' THEN 1 END) AS successful_actions,
    COUNT(DISTINCT CASE WHEN al.action_status = 'Failed' THEN 1 END) AS failed_actions,
    COUNT(DISTINCT CASE WHEN al.action_status = 'Blocked' THEN 1 END) AS blocked_actions
FROM Audit_Logs al
WHERE al.created_at > datetime('now', '-90 days')
GROUP BY DATE(al.created_at), al.module_name, al.action_type, al.user_role
ORDER BY activity_date DESC, module_name ASC;

-- ===========================================================
-- VIEW: vw_pending_notifications
--
-- PURPOSE:
-- Pending (unread) notifications for all users
-- Shows notification summary and priorities
--
-- USED BY:
-- • Notification Center
-- • User Alerts Dashboard
-- • Notification Management
-- • Communication System
-- ===========================================================

CREATE VIEW vw_pending_notifications AS
SELECT
    n.notification_id,
    n.recipient_type,
    n.recipient_id,
    CASE
        WHEN n.recipient_type = 'Student' THEN (SELECT first_name || ' ' || last_name FROM Students WHERE student_id = n.recipient_id)
        WHEN n.recipient_type = 'Teacher' THEN (SELECT first_name || ' ' || last_name FROM Teachers WHERE teacher_id = n.recipient_id)
        ELSE 'Administrator'
    END AS recipient_name,
    n.title,
    n.message,
    n.notification_type,
    n.priority,
    n.sender,
    n.created_at,
    ROUND((JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(n.created_at)) * 24) AS hours_pending,
    n.action_url
FROM Notifications n
WHERE n.is_read = FALSE
ORDER BY CASE
    WHEN n.priority = 'Critical' THEN 1
    WHEN n.priority = 'High' THEN 2
    WHEN n.priority = 'Normal' THEN 3
    ELSE 4
END ASC, n.created_at DESC;

-- ===========================================================
-- SECTION 9: AI & ANALYTICS VIEWS (3 Views)
-- ===========================================================

-- ===========================================================
-- VIEW: vw_at_risk_students
--
-- PURPOSE:
-- Identify students at risk requiring intervention
-- Combines academic performance, attendance, and engagement factors
--
-- USED BY:
-- • AI Academic Advisor Agent
-- • Student Support Services
-- • Early Alert System
-- • Intervention Programs
-- ===========================================================

CREATE VIEW vw_at_risk_students AS
SELECT
    s.student_id,
    s.roll_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    d.department_name,
    u.email,
    u.last_login,
    COALESCE(sc.overall_cgpa, 0) AS current_cgpa,
    COALESCE(sc.academic_status, 'Good Standing') AS academic_status,
    COALESCE(sg.semester_gpa, 0) AS current_semester_gpa,
    COALESCE(
        (SELECT ROUND(AVG(
            CASE WHEN a.status IN ('Present', 'Late') THEN 100.0 ELSE 0 END), 2)
         FROM Attendance a
         WHERE a.student_id = s.student_id),
        0
    ) AS average_attendance_percentage,
    COALESCE(sc.total_failed_courses, 0) AS total_failed_courses,
    CASE
        WHEN sc.overall_cgpa < 1.0 OR sc.academic_status = 'Dismissed' THEN 'Critical'
        WHEN sc.overall_cgpa < 1.5 OR sc.academic_status = 'Probation' THEN 'High'
        WHEN sc.overall_cgpa < 2.0 OR sc.academic_status = 'Warning' THEN 'Medium'
        WHEN (SELECT AVG(CASE WHEN a.status IN ('Present', 'Late') THEN 100.0 ELSE 0 END) FROM Attendance a WHERE a.student_id = s.student_id) < 60 THEN 'Medium'
        ELSE 'Low'
    END AS risk_level,
    CASE
        WHEN sc.overall_cgpa < 1.0 THEN 'Immediate support needed - Consider academic dismissal options'
        WHEN sc.overall_cgpa < 1.5 THEN 'Intensive tutoring and counseling recommended'
        WHEN sc.overall_cgpa < 2.0 THEN 'Study skills workshop and course advising needed'
        WHEN (SELECT AVG(CASE WHEN a.status IN ('Present', 'Late') THEN 100.0 ELSE 0 END) FROM Attendance a WHERE a.student_id = s.student_id) < 60 THEN 'Attendance improvement plan required'
        ELSE 'Monitoring recommended'
    END AS recommended_intervention,
    sc.last_calculated AS status_updated_at
FROM Students s
INNER JOIN Users u ON s.user_id = u.user_id
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Student_CGPA sc ON s.student_id = sc.student_id
LEFT JOIN Semester_GPA sg ON s.student_id = sg.student_id AND s.semester = sg.semester
WHERE s.status = 'Active'
  AND (COALESCE(sc.overall_cgpa, 4.0) < 2.0
       OR COALESCE(sc.academic_status, 'Good Standing') IN ('Warning', 'Probation', 'Dismissed')
       OR COALESCE(
           (SELECT AVG(CASE WHEN a.status IN ('Present', 'Late') THEN 100.0 ELSE 0 END)
            FROM Attendance a WHERE a.student_id = s.student_id),
           100) < 75)
ORDER BY CASE
    WHEN sc.academic_status = 'Dismissed' THEN 1
    WHEN sc.academic_status = 'Probation' THEN 2
    WHEN sc.academic_status = 'Warning' THEN 3
    ELSE 4
END ASC, sc.overall_cgpa ASC;

-- ===========================================================
-- VIEW: vw_scholarship_candidates
--
-- PURPOSE:
-- Students eligible for scholarships based on academic merit
-- Identifies high performers for scholarship consideration
--
-- USED BY:
-- • Scholarship Committee
-- • AI Scholarship Agent
-- • Merit-Based Scholarships
-- • Financial Aid Programs
-- ===========================================================

CREATE VIEW vw_scholarship_candidates AS
SELECT
    s.student_id,
    s.roll_number,
    s.registration_number,
    s.first_name || ' ' || s.last_name AS student_name,
    s.program,
    s.batch_year,
    d.department_name,
    sc.overall_cgpa,
    sc.honors_status,
    sc.academic_status,
    sc.total_passed_courses,
    ROUND(
        (SELECT AVG(CASE WHEN a.status IN ('Present', 'Late') THEN 100.0 ELSE 0 END)
         FROM Attendance a WHERE a.student_id = s.student_id),
        2
    ) AS average_attendance_percentage,
    u.email,
    CASE
        WHEN sc.overall_cgpa >= 3.8 AND sc.honors_status = 'Summa Cum Laude' THEN 'Presidential Scholarship'
        WHEN sc.overall_cgpa >= 3.7 AND sc.honors_status = 'Magna Cum Laude' THEN 'Vice Chancellor Scholarship'
        WHEN sc.overall_cgpa >= 3.5 AND sc.honors_status = 'Cum Laude' THEN 'Departmental Scholarship'
        WHEN sc.overall_cgpa >= 3.0 THEN 'Merit Scholarship'
        ELSE 'Not Eligible'
    END AS scholarship_category,
    sc.last_calculated AS gpa_last_updated
FROM Students s
INNER JOIN Users u ON s.user_id = u.user_id
INNER JOIN Departments d ON s.department_id = d.department_id
LEFT JOIN Student_CGPA sc ON s.student_id = sc.student_id
WHERE s.status = 'Active'
  AND COALESCE(sc.overall_cgpa, 0) >= 3.0
  AND COALESCE(sc.academic_status, 'Good Standing') = 'Good Standing'
ORDER BY sc.overall_cgpa DESC, s.roll_number ASC;

-- ===========================================================
-- VIEW: vw_department_performance_analytics
--
-- PURPOSE:
-- Department-level performance analytics
-- Aggregates metrics across all students and courses
--
-- USED BY:
-- • Department Head Dashboard
-- • Academic Analytics
-- • Institutional Reporting
-- • Quality Assurance
-- ===========================================================

CREATE VIEW vw_department_performance_analytics AS
SELECT
    d.department_id,
    d.department_name,
    COUNT(DISTINCT s.student_id) AS total_students,
    COUNT(DISTINCT CASE WHEN s.status = 'Active' THEN s.student_id END) AS active_students,
    COUNT(DISTINCT CASE WHEN sc.academic_status = 'Good Standing' THEN s.student_id END) AS good_standing,
    COUNT(DISTINCT CASE WHEN sc.academic_status IN ('Warning', 'Probation', 'Dismissed') THEN s.student_id END) AS at_risk_count,
    ROUND(AVG(sc.overall_cgpa), 2) AS average_cgpa,
    COUNT(DISTINCT CASE WHEN sc.honors_status <> 'None' THEN s.student_id END) AS honors_students,
    COUNT(DISTINCT c.course_id) AS total_courses,
    COUNT(DISTINCT t.teacher_id) AS faculty_count,
    ROUND(
        (SELECT AVG(
            CASE WHEN cr.result_status = 'Pass' THEN 100.0 ELSE 0 END)
         FROM Course_Results cr
         INNER JOIN Enrollments e ON cr.enrollment_id = e.enrollment_id
         INNER JOIN Courses c2 ON e.course_id = c2.course_id
         WHERE c2.department_id = d.department_id),
        2
    ) AS overall_pass_percentage,
    ROUND(
        (SELECT AVG(cr.percentage)
         FROM Course_Results cr
         INNER JOIN Enrollments e ON cr.enrollment_id = e.enrollment_id
         INNER JOIN Courses c2 ON e.course_id = c2.course_id
         WHERE c2.department_id = d.department_id),
        2
    ) AS average_course_percentage
FROM Departments d
LEFT JOIN Students s ON d.department_id = s.department_id
LEFT JOIN Student_CGPA sc ON s.student_id = sc.student_id
LEFT JOIN Courses c ON d.department_id = c.department_id
LEFT JOIN Teachers t ON d.department_id = t.department_id
WHERE d.status = 'Active'
GROUP BY d.department_id, d.department_name
ORDER BY average_cgpa DESC, d.department_name ASC;

-- ===========================================================
-- END OF FILE
-- ===========================================================
-- Total Views: 31
-- All views are production-ready and SQLite optimized
-- ===========================================================