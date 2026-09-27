-- Approved academic-calendar correction for the validated CSE cohort.
-- Preserve the valid 2024 admission cohort and historical enrollments.
-- PAL ends remain unset pending registrar confirmation.
PRAGMA foreign_keys = ON;

ALTER TABLE Academic_Terms ADD COLUMN term_name TEXT;
ALTER TABLE Academic_Terms ADD COLUMN start_date DATE;
ALTER TABLE Academic_Terms ADD COLUMN end_date DATE;

-- Historical terms are final.  Fall 2026 / PAL begins on the confirmed date;
-- all later terms remain upcoming until the registrar activates them.
UPDATE Academic_Terms
SET status = CASE
    WHEN academic_year IN ('2024-2025', '2025-2026') THEN 'Completed'
    ELSE 'Upcoming'
END,
term_name = CASE
    WHEN semester IN (1, 3, 7) THEN 'Fall'
    WHEN semester IN (2, 4, 6, 8) THEN 'Spring'
    WHEN semester = 5 THEN 'PAL'
END,
start_date = CASE
    WHEN academic_year = '2026-2027' AND semester = 5 THEN '2026-09-15'
    ELSE start_date
END,
end_date = CASE
    WHEN academic_year = '2026-2027' AND semester = 5 THEN NULL
    ELSE end_date
END,
completed_at = CASE
    WHEN academic_year IN ('2024-2025', '2025-2026') THEN COALESCE(completed_at, updated_at)
    ELSE NULL
END;

-- Historical student-course registrations are no longer active enrollment.
UPDATE Enrollments
SET enrollment_status = 'Completed'
WHERE academic_year IN ('2024-2025', '2025-2026')
  AND enrollment_status = 'Enrolled';

-- PAL and later terms have not occurred yet, so none of their registrations
-- may claim completion.
UPDATE Enrollments
SET enrollment_status = 'Enrolled'
WHERE academic_year IN ('2026-2027', '2027-2028')
  AND enrollment_status = 'Completed';

-- Results for PAL/future terms are progress only, not published final results.
UPDATE Course_Results
SET published = FALSE,
    verified = FALSE,
    locked = FALSE,
    result_status = 'Incomplete',
    remarks = 'Academic progress only; term not completed.'
WHERE academic_year IN ('2026-2027', '2027-2028');

-- Grade metadata must exactly match the enrollment it belongs to.
UPDATE Grades
SET academic_year = (
        SELECT e.academic_year FROM Enrollments e
        WHERE e.enrollment_id = Grades.enrollment_id
    ),
    semester = (
        SELECT e.semester FROM Enrollments e
        WHERE e.enrollment_id = Grades.enrollment_id
    );
