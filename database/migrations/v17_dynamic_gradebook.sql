CREATE TABLE IF NOT EXISTS Gradebook_Settings (
    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES Courses(course_id),
    teacher_id INTEGER NOT NULL REFERENCES Teachers(teacher_id),
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    total_marks REAL NOT NULL DEFAULT 100 CHECK(total_marks = 100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, academic_year, semester)
);

CREATE TABLE IF NOT EXISTS Gradebook_Components (
    component_id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_id INTEGER NOT NULL REFERENCES Gradebook_Settings(setting_id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK(category IN ('Sessional', 'Midterm', 'Final')),
    name TEXT NOT NULL,
    item_count INTEGER NOT NULL CHECK(item_count > 0),
    total_marks REAL NOT NULL CHECK(total_marks > 0),
    item_total_marks REAL NOT NULL CHECK(item_total_marks > 0),
    aggregation TEXT NOT NULL DEFAULT 'average' CHECK(aggregation = 'average'),
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_gradebook_setting_term ON Gradebook_Settings(course_id, academic_year, semester);
CREATE INDEX IF NOT EXISTS idx_gradebook_component_setting ON Gradebook_Components(setting_id);

-- The original result table encoded the historical 25/25/50 policy in checks.
-- Rebuild it once so configured category totals can be stored without changing
-- the existing result data.
PRAGMA foreign_keys=OFF;
ALTER TABLE Course_Results RENAME TO Course_Results_legacy_dynamic_gradebook;
CREATE TABLE Course_Results AS SELECT * FROM Course_Results_legacy_dynamic_gradebook WHERE 0;
DROP TABLE Course_Results;
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
    sessional_marks REAL DEFAULT 0,
    midterm_marks REAL DEFAULT 0,
    final_marks REAL DEFAULT 0,
    total_marks REAL DEFAULT 0,
    percentage REAL DEFAULT 0,
    letter_grade TEXT,
    grade_points REAL,
    result_status TEXT DEFAULT 'Pass' CHECK(result_status IN ('Pass','Fail','Incomplete')),
    verified BOOLEAN DEFAULT FALSE,
    published BOOLEAN DEFAULT FALSE,
    locked BOOLEAN DEFAULT FALSE,
    verification_hash TEXT,
    remarks TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(enrollment_id) REFERENCES Enrollments(enrollment_id),
    FOREIGN KEY(student_id) REFERENCES Students(student_id),
    FOREIGN KEY(course_id) REFERENCES Courses(course_id),
    FOREIGN KEY(teacher_id) REFERENCES Teachers(teacher_id)
);
INSERT INTO Course_Results SELECT * FROM Course_Results_legacy_dynamic_gradebook;
DROP TABLE Course_Results_legacy_dynamic_gradebook;
CREATE INDEX IF NOT EXISTS idx_result_student ON Course_Results(student_id);
CREATE INDEX IF NOT EXISTS idx_result_course ON Course_Results(course_id);
CREATE INDEX IF NOT EXISTS idx_result_semester ON Course_Results(semester);
CREATE INDEX IF NOT EXISTS idx_result_grade ON Course_Results(letter_grade);
CREATE INDEX IF NOT EXISTS idx_result_verified ON Course_Results(verified);
CREATE INDEX IF NOT EXISTS idx_result_published ON Course_Results(published);
PRAGMA foreign_keys=ON;