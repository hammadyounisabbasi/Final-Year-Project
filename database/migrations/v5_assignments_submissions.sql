-- Safe additive migration for teacher-owned assignments and student submissions.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    assignment_type TEXT NOT NULL DEFAULT 'Assignment'
        CHECK(assignment_type IN ('Assignment', 'Quiz', 'Project', 'Lab', 'Presentation')),
    total_marks REAL NOT NULL CHECK(total_marks > 0),
    semester INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    release_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME NOT NULL,
    allow_late_submission BOOLEAN NOT NULL DEFAULT FALSE,
    late_penalty_percentage REAL NOT NULL DEFAULT 0,
    attachment_path TEXT,
    status TEXT NOT NULL DEFAULT 'Published'
        CHECK(status IN ('Draft', 'Published', 'Closed', 'Archived')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES Courses(course_id),
    FOREIGN KEY(teacher_id) REFERENCES Teachers(teacher_id)
);

CREATE TABLE IF NOT EXISTS Submissions (
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    submission_title TEXT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    file_hash TEXT,
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_late BOOLEAN NOT NULL DEFAULT FALSE,
    submission_attempt INTEGER NOT NULL DEFAULT 1,
    plagiarism_score REAL,
    ai_score REAL,
    ai_feedback TEXT,
    teacher_marks REAL,
    teacher_feedback TEXT,
    submission_status TEXT NOT NULL DEFAULT 'Submitted'
        CHECK(submission_status IN ('Draft', 'Submitted', 'Under Review', 'Reviewed', 'Returned', 'Accepted', 'Rejected')),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    graded BOOLEAN NOT NULL DEFAULT FALSE,
    graded_at DATETIME,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assignment_id) REFERENCES Assignments(assignment_id),
    FOREIGN KEY(student_id) REFERENCES Students(student_id),
    UNIQUE(assignment_id, student_id, submission_attempt)
);

CREATE INDEX IF NOT EXISTS idx_assignment_course ON Assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_assignment_teacher ON Assignments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_assignment_due_date ON Assignments(due_date);
CREATE INDEX IF NOT EXISTS idx_assignment_status ON Assignments(status);
CREATE INDEX IF NOT EXISTS idx_submission_assignment ON Submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_submission_student ON Submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_submission_status ON Submissions(submission_status);
