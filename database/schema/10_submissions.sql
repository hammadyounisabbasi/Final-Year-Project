-- ===========================================================
-- TABLE: Submissions
-- PURPOSE:
-- Stores assignment submissions uploaded by students.
-- This table supports AI evaluation, plagiarism detection,
-- teacher review, and grading workflow.
-- ===========================================================
DROP TABLE IF EXISTS Submissions;
CREATE TABLE Submissions (
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    submission_title TEXT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    file_hash TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_late BOOLEAN DEFAULT FALSE,
    submission_attempt INTEGER DEFAULT 1,
    plagiarism_score REAL,
    ai_score REAL,
    ai_feedback TEXT,
    teacher_marks REAL,
    teacher_feedback TEXT,
    submission_status TEXT DEFAULT 'Submitted'
        CHECK(submission_status IN
        ('Draft',
         'Submitted',
         'Under Review',
         'Reviewed',
         'Returned',
         'Accepted',
         'Rejected')),
    verified BOOLEAN DEFAULT FALSE,
    graded BOOLEAN DEFAULT FALSE,
    graded_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assignment_id)
        REFERENCES Assignments(assignment_id),
    FOREIGN KEY (student_id)
        REFERENCES Students(student_id),
    UNIQUE(assignment_id, student_id, submission_attempt)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_submission_assignment
ON Submissions(assignment_id);
CREATE INDEX idx_submission_student
ON Submissions(student_id);
CREATE INDEX idx_submission_status
ON Submissions(submission_status);
CREATE INDEX idx_submission_submitted
ON Submissions(submitted_at);
CREATE INDEX idx_submission_verified
ON Submissions(verified);
CREATE INDEX idx_submission_graded
ON Submissions(graded);