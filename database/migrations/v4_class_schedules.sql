-- Safe additive migration: teacher-owned class timetable entries.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Class_Schedules (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    section TEXT NOT NULL,
    day_of_week TEXT NOT NULL
        CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    room_location TEXT NOT NULL,
    class_type TEXT NOT NULL DEFAULT 'Lecture'
        CHECK(class_type IN ('Lecture', 'Lab', 'Tutorial', 'Seminar')),
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK(status IN ('Active', 'Cancelled', 'Completed')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES Courses(course_id),
    FOREIGN KEY(teacher_id) REFERENCES Teachers(teacher_id),
    UNIQUE(course_id, academic_year, semester, section, day_of_week, start_time)
);

CREATE INDEX IF NOT EXISTS idx_class_schedule_teacher
    ON Class_Schedules(teacher_id);
CREATE INDEX IF NOT EXISTS idx_class_schedule_course
    ON Class_Schedules(course_id);
CREATE INDEX IF NOT EXISTS idx_class_schedule_period
    ON Class_Schedules(academic_year, semester, section);
