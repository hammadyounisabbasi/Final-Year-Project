-- ===========================================================
-- PROJECT:
-- Zero-Trust Autonomous Campus Ecosystem
--
-- MASTER DATABASE INITIALIZATION SCRIPT
--
-- PURPOSE:
-- Creates the complete University Database.
--
-- NOTE:
-- Execute this file FIRST.
-- ===========================================================
PRAGMA foreign_keys = ON;
.read 01_users.sql
.read 02_departments.sql
.read 03_students.sql
.read 04_teachers.sql
.read 05_courses.sql
.read 06_enrollments.sql
.read 07_attendance.sql
.read 08_grades.sql
.read 09_assignments.sql
.read 10_submissions.sql
.read 11_fee_records.sql
.read 12_documents.sql
.read 13_library.sql
.read 14_hostels.sql
.read 15_transport.sql
.read 16_notifications.sql
.read 17_research.sql
.read 18_security.sql
.read 19_ai_agents.sql
.read 20_audit.sql
.read 21_course_results.sql
.read 22_semester_gpa.sql
.read 23_student_cgpa.sql