-- ===========================================================
-- TABLE: Semester_GPA
-- PURPOSE:
-- Stores GPA of each semester for every student.
--
-- Used By:
-- - Student Dashboard
-- - Transcript
-- - Academic Advisor Agent
-- - Scholarship Agent
-- - Graduation Eligibility Agent
-- ===========================================================
DROP TABLE IF EXISTS Semester_GPA;
CREATE TABLE Semester_GPA (
    semester_gpa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    total_credit_hours INTEGER NOT NULL,
    earned_credit_hours INTEGER NOT NULL,
    total_grade_points REAL NOT NULL,
    semester_gpa REAL NOT NULL,
    academic_status TEXT DEFAULT 'Good Standing'
        CHECK(
            academic_status IN
            (
                'Good Standing',
                'Warning',
                'Probation',
                'Dismissed'
            )
        ),
    remarks TEXT,
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),
    UNIQUE(student_id, semester, academic_year)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_semester_gpa_student
ON Semester_GPA(student_id);
CREATE INDEX idx_semester_gpa_semester
ON Semester_GPA(semester);
CREATE INDEX idx_semester_gpa_year
ON Semester_GPA(academic_year);
CREATE INDEX idx_semester_gpa_status
ON Semester_GPA(academic_status);