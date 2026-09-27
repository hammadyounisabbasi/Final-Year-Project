-- ===========================================================
-- TABLE: Departments
-- PURPOSE:
-- Stores all university departments.
-- Referenced by Students, Teachers, Courses and other modules.
-- ===========================================================
DROP TABLE IF EXISTS Departments;
CREATE TABLE Departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_code TEXT NOT NULL UNIQUE,
    department_name TEXT NOT NULL UNIQUE,
    department_short_name TEXT,
    office_location TEXT,
    office_phone TEXT,
    office_email TEXT UNIQUE,
    hod_user_id INTEGER,
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK(status IN ('Active','Inactive')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hod_user_id)
        REFERENCES Users(user_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_department_code
ON Departments(department_code);
CREATE INDEX idx_department_name
ON Departments(department_name);
CREATE INDEX idx_department_status
ON Departments(status);