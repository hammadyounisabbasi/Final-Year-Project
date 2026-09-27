-- =====================================================
-- TABLE: Grades
-- Description:
-- Stores every assessment record of a student.
--
-- University of Haripur Assessment Structure:
-- Sessional (25 Marks)
--   - Quiz
--   - Assignment
--   - Lab
--   - Viva
--   - Presentation
--
-- Midterm (25 Marks)
--
-- Final (50 Marks)
--
-- Used By:
-- - Teacher Dashboard
-- - Student Dashboard
-- - Academic Advisor Agent
-- - Blind Paper Auditor Agent
-- - Clerk Watchdog Agent
-- - GPA / CGPA Calculation
-- =====================================================
DROP TABLE IF EXISTS Grades;
CREATE TABLE Grades (
    grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    assessment_type TEXT NOT NULL
    CHECK(
        assessment_type IN
        (
            'Quiz',
            'Assignment',
            'Lab',
            'Viva',
            'Presentation',
            'Midterm',
            'Final'
        )
    ),
    title TEXT,
    obtained_marks REAL NOT NULL,
    total_marks REAL NOT NULL,
    percentage REAL,
    letter_grade TEXT,
    grade_points REAL,
    remarks TEXT,
    graded_by INTEGER,
    graded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE,
    verification_hash TEXT,
    published BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(enrollment_id)
        REFERENCES Enrollments(enrollment_id)
        ON DELETE CASCADE,
    FOREIGN KEY(graded_by)
        REFERENCES Teachers(teacher_id)
        ON DELETE SET NULL
);
-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX idx_grade_enrollment
ON Grades(enrollment_id);
CREATE INDEX idx_grade_teacher
ON Grades(graded_by);
CREATE INDEX idx_grade_type
ON Grades(assessment_type);
CREATE INDEX idx_grade_semester
ON Grades(semester);
CREATE INDEX idx_grade_verified
ON Grades(verified);
CREATE INDEX idx_grade_published
ON Grades(published);