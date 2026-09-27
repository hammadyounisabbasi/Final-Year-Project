-- Current attendance schema. Historical databases are upgraded by v8.
CREATE TABLE Attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    schedule_id INTEGER,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    section TEXT NOT NULL,
    attendance_date DATE NOT NULL,
    session_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late', 'Leave')),
    remarks TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES Students(student_id),
    FOREIGN KEY(course_id) REFERENCES Courses(course_id),
    FOREIGN KEY(teacher_id) REFERENCES Teachers(teacher_id),
    FOREIGN KEY(schedule_id) REFERENCES Class_Schedules(schedule_id),
    UNIQUE(student_id, course_id, academic_year, semester, section, attendance_date, session_key)
);

CREATE INDEX idx_attendance_student ON Attendance(student_id);
CREATE INDEX idx_attendance_teacher ON Attendance(teacher_id);
CREATE INDEX idx_attendance_context ON Attendance(course_id, academic_year, semester, section, attendance_date);
