-- ===========================================================
-- TABLE: Assignments
-- PURPOSE:
-- Stores assignments created by teachers for specific courses.
-- ===========================================================
DROP TABLE IF EXISTS Assignments;
CREATE TABLE Assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    assignment_type TEXT DEFAULT 'Assignment'
        CHECK(assignment_type IN
        ('Assignment','Quiz','Project','Lab','Presentation')),
    total_marks REAL NOT NULL,
    semester INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    release_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME NOT NULL,
    allow_late_submission BOOLEAN DEFAULT FALSE,
    late_penalty_percentage REAL DEFAULT 0,
    attachment_path TEXT,
    status TEXT DEFAULT 'Published'
        CHECK(status IN
        ('Draft','Published','Closed','Archived')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id)
        REFERENCES Courses(course_id),
    FOREIGN KEY(teacher_id)
        REFERENCES Teachers(teacher_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_assignment_course
ON Assignments(course_id);
CREATE INDEX idx_assignment_teacher
ON Assignments(teacher_id);
CREATE INDEX idx_assignment_due_date
ON Assignments(due_date);
CREATE INDEX idx_assignment_status
ON Assignments(status);
CREATE INDEX idx_assignment_semester
ON Assignments(semester);