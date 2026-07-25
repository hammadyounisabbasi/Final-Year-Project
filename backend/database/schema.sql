-- Core Academic Tables
CREATE TABLE Students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(100),
    semester INTEGER,
    cgpa DECIMAL(3,2),
    status VARCHAR(20) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    credits INTEGER NOT NULL,
    instructor_id INTEGER,
    semester INTEGER
);

CREATE TABLE Enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER NOT NULL,

    course_id INTEGER NOT NULL,

    semester INTEGER,

    enrollment_date DATE DEFAULT CURRENT_DATE,

    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),

    FOREIGN KEY(course_id)
        REFERENCES Courses(course_id)
);

CREATE TABLE Grades (

    grade_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER NOT NULL,

    course_id INTEGER NOT NULL,

    component VARCHAR(50) NOT NULL,

    marks DECIMAL(5,2),

    date_recorded DATE,

    verification_hash VARCHAR(255),

    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),

    FOREIGN KEY(course_id)
        REFERENCES Courses(course_id)
);

-- Design Administrative Tables
CREATE TABLE Users (

    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,

    role VARCHAR(50) NOT NULL,

    department VARCHAR(100) NOT NULL,

    permissions TEXT NOT NULL

);

CREATE TABLE Audit_Log (

    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,

    action VARCHAR(255) NOT NULL,

    actor VARCHAR(100) NOT NULL,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    affected_rows INTEGER,

    change_hash VARCHAR(255)

);

CREATE TABLE Fee_Records (

    fee_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER NOT NULL,

    amount DECIMAL(10,2) NOT NULL,

    status VARCHAR(20) NOT NULL,

    transaction_id VARCHAR(100) UNIQUE,

    reconciled BOOLEAN DEFAULT FALSE,

    FOREIGN KEY(student_id)
        REFERENCES Students(student_id)

);

-- Design Document Management Tables
CREATE TABLE Documents ( --doc uploaded by the students

    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER NOT NULL,

    type VARCHAR(50) NOT NULL,

    file_path VARCHAR(255) NOT NULL,

    verified_hash VARCHAR(255) NOT NULL,

    FOREIGN KEY(student_id)
        REFERENCES Students(student_id)

);

CREATE TABLE Admission_Applications ( -- Applications submitted by applicant during admission

    application_id INTEGER PRIMARY KEY AUTOINCREMENT,

    applicant_id INTEGER NOT NULL,

    documents TEXT NOT NULL,

    status VARCHAR(20) NOT NULL,

    decision VARCHAR(100)

);

CREATE TABLE Research_Papers ( --store research papers submitted by the faculty

    paper_id INTEGER PRIMARY KEY AUTOINCREMENT,

    professor_id INTEGER NOT NULL,

    title VARCHAR(255) NOT NULL,

    abstract TEXT NOT NULL,

    submission_date DATE NOT NULL

);