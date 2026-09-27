-- ===========================================================
-- TABLE: Course_Results
-- PURPOSE:
-- Stores final result of ONE student in ONE course.
-- Generated from the teacher's dynamic Grade Book Settings after assessment entry.
--
-- Used By:
-- - Student Dashboard
-- - Teacher Dashboard
-- - Transcript Generator
-- - GPA Calculator
-- - CGPA Calculator
-- - Academic Advisor Agent
-- - Scholarship Agent
-- ===========================================================
DROP TABLE IF EXISTS Course_Results;
CREATE TABLE Course_Results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL UNIQUE,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    teacher_id INTEGER,
    semester INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    credit_hours INTEGER NOT NULL,
    quality_points REAL DEFAULT 0,
    -------------------------------------------------------
    -- Final Marks Breakdown
    -------------------------------------------------------
    sessional_marks REAL DEFAULT 0,
    midterm_marks REAL DEFAULT 0,
    final_marks REAL DEFAULT 0,
    -------------------------------------------------------
    -- Final Result
    -------------------------------------------------------
    total_marks REAL DEFAULT 0,
    percentage REAL DEFAULT 0,
    letter_grade TEXT,
    grade_points REAL,
    result_status TEXT DEFAULT 'Pass'
        CHECK(result_status IN
        ('Pass','Fail','Incomplete')),
    -------------------------------------------------------
    -- Verification
    -------------------------------------------------------
    verified BOOLEAN DEFAULT FALSE,
    published BOOLEAN DEFAULT FALSE,
    locked BOOLEAN DEFAULT FALSE,
    verification_hash TEXT,
    remarks TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -------------------------------------------------------
    -- FOREIGN KEYS
    -------------------------------------------------------
    FOREIGN KEY(enrollment_id)
        REFERENCES Enrollments(enrollment_id),
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),
    FOREIGN KEY(course_id)
        REFERENCES Courses(course_id),
    FOREIGN KEY(teacher_id)
        REFERENCES Teachers(teacher_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_result_student
ON Course_Results(student_id);
CREATE INDEX idx_result_course
ON Course_Results(course_id);
CREATE INDEX idx_result_semester
ON Course_Results(semester);
CREATE INDEX idx_result_grade
ON Course_Results(letter_grade);
CREATE INDEX idx_result_verified
ON Course_Results(verified);
CREATE INDEX idx_result_published
ON Course_Results(published);