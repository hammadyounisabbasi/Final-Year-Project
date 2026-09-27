-- ===========================================================
-- TABLE: Teachers
-- PURPOSE:
-- Stores faculty information.
-- Linked with Users and Departments.
-- ===========================================================
DROP TABLE IF EXISTS Teachers;
CREATE TABLE Teachers (
    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    department_id INTEGER NOT NULL,
    employee_id TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT
        CHECK(gender IN ('Male','Female','Other')),
    date_of_birth DATE,
    phone TEXT,
    office_email TEXT NOT NULL UNIQUE,
    designation TEXT NOT NULL,
    qualification TEXT,
    specialization TEXT,
    joining_date DATE,
    office_room TEXT,
    profile_photo TEXT,
    employment_type TEXT DEFAULT 'Permanent'
        CHECK(employment_type IN ('Permanent','Contract','Visiting')),
    status TEXT DEFAULT 'Active'
        CHECK(status IN ('Active','On Leave','Retired','Resigned')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES Users(user_id),
    FOREIGN KEY (department_id)
        REFERENCES Departments(department_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_teacher_employee
ON Teachers(employee_id);
CREATE INDEX idx_teacher_department
ON Teachers(department_id);
CREATE INDEX idx_teacher_email
ON Teachers(office_email);
CREATE INDEX idx_teacher_status
ON Teachers(status);