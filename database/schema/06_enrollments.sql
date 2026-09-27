-- ===========================================================
-- TABLE: Enrollments
-- PURPOSE:
-- Maps students to courses for each semester.
-- ===========================================================
DROP TABLE IF EXISTS Enrollments;
CREATE TABLE Enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    section TEXT,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    enrollment_status TEXT DEFAULT 'Enrolled'
        CHECK(enrollment_status IN
        ('Enrolled','Dropped','Completed','Withdrawn')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),
    FOREIGN KEY(course_id)
        REFERENCES Courses(course_id),
    UNIQUE(student_id, course_id, academic_year)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_enrollment_student
ON Enrollments(student_id);
CREATE INDEX idx_enrollment_course
ON Enrollments(course_id);
CREATE INDEX idx_enrollment_semester
ON Enrollments(semester);
CREATE INDEX idx_enrollment_year
ON Enrollments(academic_year);
CREATE INDEX idx_enrollment_status
ON Enrollments(enrollment_status);