-- Align active cohort records with the admission-date academic calendar.
-- Historical enrollment and result records remain unchanged.
PRAGMA foreign_keys = ON;

UPDATE Enrollments
SET academic_year = CASE semester
    WHEN 1 THEN '2026-2027'
    WHEN 2 THEN '2025-2026'
    WHEN 3 THEN '2025-2026'
    WHEN 4 THEN '2024-2025'
    WHEN 5 THEN '2024-2025'
    WHEN 6 THEN '2023-2024'
    WHEN 7 THEN '2023-2024'
    WHEN 8 THEN '2022-2023'
END,
updated_at = CURRENT_TIMESTAMP
WHERE EXISTS (
    SELECT 1
    FROM Students
    WHERE Students.student_id = Enrollments.student_id
      AND Students.semester = Enrollments.semester
);

UPDATE Class_Schedules
SET academic_year = CASE semester
    WHEN 1 THEN '2026-2027'
    WHEN 2 THEN '2025-2026'
    WHEN 3 THEN '2025-2026'
    WHEN 4 THEN '2024-2025'
    WHEN 5 THEN '2024-2025'
    WHEN 6 THEN '2023-2024'
    WHEN 7 THEN '2023-2024'
    WHEN 8 THEN '2022-2023'
END,
updated_at = CURRENT_TIMESTAMP;

UPDATE Assignments
SET academic_year = CASE semester
    WHEN 1 THEN '2026-2027'
    WHEN 2 THEN '2025-2026'
    WHEN 3 THEN '2025-2026'
    WHEN 4 THEN '2024-2025'
    WHEN 5 THEN '2024-2025'
    WHEN 6 THEN '2023-2024'
    WHEN 7 THEN '2023-2024'
    WHEN 8 THEN '2022-2023'
END,
updated_at = CURRENT_TIMESTAMP;
