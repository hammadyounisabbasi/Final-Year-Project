-- ===========================================================
-- TABLE: Student_CGPA
-- PURPOSE:
-- Stores the overall CGPA of each student.
--
-- Used By:
-- - Student Dashboard
-- - Transcript Generator
-- - Academic Advisor Agent
-- - Scholarship Agent
-- - Graduation Eligibility Agent
-- ===========================================================
DROP TABLE IF EXISTS Student_CGPA;
CREATE TABLE Student_CGPA (
    cgpa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL UNIQUE,
    total_completed_credit_hours INTEGER DEFAULT 0,
    total_grade_points REAL DEFAULT 0,
    overall_cgpa REAL DEFAULT 0,
    total_passed_courses INTEGER DEFAULT 0,
    total_failed_courses INTEGER DEFAULT 0,
    academic_status TEXT DEFAULT 'Good Standing'
        CHECK(
            academic_status IN
            (
                'Good Standing',
                'Warning',
                'Probation',
                'Dismissed',
                'Graduated'
            )
        ),
    graduation_eligible BOOLEAN DEFAULT FALSE,
    honors_status TEXT
        CHECK(
            honors_status IN
            (
                'None',
                'Cum Laude',
                'Magna Cum Laude',
                'Summa Cum Laude'
            )
        ),
    remarks TEXT,
    last_calculated DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id)
        ON DELETE CASCADE
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_cgpa_student
ON Student_CGPA(student_id);
CREATE INDEX idx_cgpa_status
ON Student_CGPA(academic_status);
CREATE INDEX idx_cgpa_graduation
ON Student_CGPA(graduation_eligible);
CREATE INDEX idx_cgpa_value
ON Student_CGPA(overall_cgpa);
