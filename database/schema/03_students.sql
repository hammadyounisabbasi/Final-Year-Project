-- ===========================================================
-- TABLE: Students
-- PURPOSE:
-- Stores complete student profile information.
-- Linked with Users and Departments.
-- ===========================================================
DROP TABLE IF EXISTS Students;
CREATE TABLE Students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    department_id INTEGER NOT NULL,
    roll_number TEXT NOT NULL UNIQUE,
    registration_number TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT
        CHECK(gender IN ('Male','Female','Other')),
    date_of_birth DATE,
    phone TEXT,
    emergency_contact TEXT,
    address TEXT,
    program TEXT NOT NULL,
    semester INTEGER NOT NULL,
    section TEXT,
    batch_year INTEGER,
    admission_date DATE,
    expected_graduation DATE,
    credits_completed INTEGER DEFAULT 0,
    profile_photo TEXT,
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK(status IN ('Active','Graduated','Suspended','Dropped')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id)
        REFERENCES Users(user_id),
    FOREIGN KEY(department_id)
        REFERENCES Departments(department_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_students_roll
ON Students(roll_number);
CREATE INDEX idx_students_registration
ON Students(registration_number);
CREATE INDEX idx_students_department
ON Students(department_id);
CREATE INDEX idx_students_program
ON Students(program);
CREATE INDEX idx_students_semester
ON Students(semester);
CREATE INDEX idx_students_status
ON Students(status);