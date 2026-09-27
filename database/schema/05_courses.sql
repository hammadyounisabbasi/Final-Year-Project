-- ===========================================================
-- TABLE: Courses
-- PURPOSE:
-- Stores all academic courses offered by the university.
-- ===========================================================
DROP TABLE IF EXISTS Courses;
CREATE TABLE Courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    course_code TEXT NOT NULL UNIQUE,
    course_title TEXT NOT NULL,
    course_description TEXT,
    credit_hours INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    course_type TEXT DEFAULT 'Core'
        CHECK(course_type IN ('Core','Elective','Lab')),
    teacher_id INTEGER,
    status TEXT DEFAULT 'Active'
        CHECK(status IN ('Active','Inactive')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(department_id)
        REFERENCES Departments(department_id),
    FOREIGN KEY(teacher_id)
        REFERENCES Teachers(teacher_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_course_code
ON Courses(course_code);
CREATE INDEX idx_course_department
ON Courses(department_id);
CREATE INDEX idx_course_teacher
ON Courses(teacher_id);
CREATE INDEX idx_course_semester
ON Courses(semester);
CREATE INDEX idx_course_status
ON Courses(status);