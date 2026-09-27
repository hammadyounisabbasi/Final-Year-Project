-- Repair the first 60 CSE student records without changing their registrations.
-- A student's current semester is in progress: it must not have Grades,
-- Course_Results, or a finalized Semester_GPA record.
PRAGMA foreign_keys = ON;

-- Keep teacher-course assignments and student registrations intact.  Only remove
-- assessments/results for the active semester (and any impossible later term).
DELETE FROM Grades
WHERE enrollment_id IN (
    SELECT enrollment_id
    FROM Enrollments
    WHERE student_id BETWEEN 1 AND 60
      AND semester >= CASE
          WHEN student_id BETWEEN 1 AND 8 THEN 1
          WHEN student_id BETWEEN 9 AND 16 THEN 2
          WHEN student_id BETWEEN 17 AND 24 THEN 3
          WHEN student_id BETWEEN 25 AND 32 THEN 4
          WHEN student_id BETWEEN 33 AND 40 THEN 5
          WHEN student_id BETWEEN 41 AND 48 THEN 6
          WHEN student_id BETWEEN 49 AND 56 THEN 7
          WHEN student_id BETWEEN 57 AND 60 THEN 8
      END
);

DELETE FROM Course_Results
WHERE student_id BETWEEN 1 AND 60
  AND semester >= CASE
      WHEN student_id BETWEEN 1 AND 8 THEN 1
      WHEN student_id BETWEEN 9 AND 16 THEN 2
      WHEN student_id BETWEEN 17 AND 24 THEN 3
      WHEN student_id BETWEEN 25 AND 32 THEN 4
      WHEN student_id BETWEEN 33 AND 40 THEN 5
      WHEN student_id BETWEEN 41 AND 48 THEN 6
      WHEN student_id BETWEEN 49 AND 56 THEN 7
      WHEN student_id BETWEEN 57 AND 60 THEN 8
  END;

DELETE FROM Semester_GPA
WHERE student_id BETWEEN 1 AND 60
  AND semester >= CASE
      WHEN student_id BETWEEN 1 AND 8 THEN 1
      WHEN student_id BETWEEN 9 AND 16 THEN 2
      WHEN student_id BETWEEN 17 AND 24 THEN 3
      WHEN student_id BETWEEN 25 AND 32 THEN 4
      WHEN student_id BETWEEN 33 AND 40 THEN 5
      WHEN student_id BETWEEN 41 AND 48 THEN 6
      WHEN student_id BETWEEN 49 AND 56 THEN 7
      WHEN student_id BETWEEN 57 AND 60 THEN 8
  END;

UPDATE Students
SET semester = CASE
        WHEN student_id BETWEEN 1 AND 8 THEN 1
        WHEN student_id BETWEEN 9 AND 16 THEN 2
        WHEN student_id BETWEEN 17 AND 24 THEN 3
        WHEN student_id BETWEEN 25 AND 32 THEN 4
        WHEN student_id BETWEEN 33 AND 40 THEN 5
        WHEN student_id BETWEEN 41 AND 48 THEN 6
        WHEN student_id BETWEEN 49 AND 56 THEN 7
        WHEN student_id BETWEEN 57 AND 60 THEN 8
    END,
    batch_year = CASE
        WHEN student_id BETWEEN 1 AND 16 THEN 2026
        WHEN student_id BETWEEN 17 AND 32 THEN 2025
        WHEN student_id BETWEEN 33 AND 48 THEN 2024
        WHEN student_id BETWEEN 49 AND 60 THEN 2023
    END,
    admission_date = CASE
        WHEN student_id BETWEEN 1 AND 8 THEN '2026-08-10'
        WHEN student_id BETWEEN 9 AND 16 THEN '2026-02-09'
        WHEN student_id BETWEEN 17 AND 24 THEN '2025-08-11'
        WHEN student_id BETWEEN 25 AND 32 THEN '2025-02-13'
        WHEN student_id BETWEEN 33 AND 40 THEN '2024-08-13'
        WHEN student_id BETWEEN 41 AND 48 THEN '2024-02-13'
        WHEN student_id BETWEEN 49 AND 56 THEN '2023-08-13'
        WHEN student_id BETWEEN 57 AND 60 THEN '2023-02-16'
    END,
    expected_graduation = CASE
        WHEN student_id BETWEEN 1 AND 16 THEN '2030-06-30'
        WHEN student_id BETWEEN 17 AND 24 THEN '2029-06-30'
        WHEN student_id BETWEEN 25 AND 32 THEN '2029-02-28'
        WHEN student_id BETWEEN 33 AND 40 THEN '2028-06-30'
        WHEN student_id BETWEEN 41 AND 48 THEN '2028-02-28'
        WHEN student_id BETWEEN 49 AND 56 THEN '2027-06-30'
        WHEN student_id BETWEEN 57 AND 60 THEN '2027-02-28'
    END,
    credits_completed = COALESCE((
        SELECT SUM(cr.credit_hours)
        FROM Course_Results cr
        WHERE cr.student_id = Students.student_id
          AND UPPER(COALESCE(cr.letter_grade, '')) <> 'F'
    ), 0),
    updated_at = CURRENT_TIMESTAMP
WHERE student_id BETWEEN 1 AND 60;

-- Rebuild the cached CGPA strictly from retained, finalized results.
UPDATE Student_CGPA
SET total_completed_credit_hours = COALESCE((
        SELECT SUM(cr.credit_hours)
        FROM Course_Results cr
        WHERE cr.student_id = Student_CGPA.student_id
          AND UPPER(COALESCE(cr.letter_grade, '')) <> 'F'
    ), 0),
    total_grade_points = COALESCE((
        SELECT ROUND(SUM(cr.quality_points), 2)
        FROM Course_Results cr
        WHERE cr.student_id = Student_CGPA.student_id
    ), 0),
    overall_cgpa = COALESCE((
        SELECT ROUND(
            SUM(cr.quality_points) / NULLIF(SUM(CASE WHEN UPPER(COALESCE(cr.letter_grade, '')) <> 'F' THEN cr.credit_hours ELSE 0 END), 0),
            2
        )
        FROM Course_Results cr
        WHERE cr.student_id = Student_CGPA.student_id
    ), 0),
    total_passed_courses = COALESCE((
        SELECT COUNT(*)
        FROM Course_Results cr
        WHERE cr.student_id = Student_CGPA.student_id
          AND UPPER(COALESCE(cr.letter_grade, '')) <> 'F'
    ), 0),
    total_failed_courses = COALESCE((
        SELECT COUNT(*)
        FROM Course_Results cr
        WHERE cr.student_id = Student_CGPA.student_id
          AND UPPER(COALESCE(cr.letter_grade, '')) = 'F'
    ), 0),
    academic_status = 'Good Standing',
    graduation_eligible = FALSE,
    honors_status = CASE WHEN EXISTS (
        SELECT 1 FROM Course_Results cr WHERE cr.student_id = Student_CGPA.student_id
    ) THEN honors_status ELSE 'None' END,
    last_calculated = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE student_id BETWEEN 1 AND 60;
