-- Data-driven timetable foundation. This migration is additive: the legacy
-- Class_Schedules and Student_Timetable tables remain operational until the
-- replacement passes its end-to-end publication test.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL UNIQUE,
    room_name TEXT,
    room_type TEXT NOT NULL DEFAULT 'Classroom'
        CHECK(room_type IN ('Classroom','Computer Lab','Laboratory','Seminar Room')),
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Timetable_Configurations (
    configuration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    working_days TEXT NOT NULL DEFAULT 'Monday,Tuesday,Wednesday,Thursday,Friday',
    day_start_time TEXT NOT NULL DEFAULT '08:30',
    day_end_time TEXT NOT NULL DEFAULT '15:30',
    slot_minutes INTEGER NOT NULL DEFAULT 60 CHECK(slot_minutes > 0),
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bootstrap the room catalogue from locations already used by the legacy
-- timetable. Capacity is the largest linked cohort observed in that room, not
-- an invented building capacity; administrators can correct/enrich it later.
INSERT OR IGNORE INTO Rooms (room_code,room_name,room_type,capacity,status)
SELECT
    trim(cs.room_location),
    trim(cs.room_location),
    CASE WHEN lower(cs.room_location) LIKE '%lab%' OR MAX(CASE WHEN cs.class_type='Lab' THEN 1 ELSE 0 END)=1
         THEN 'Laboratory' ELSE 'Classroom' END,
    MAX(1,COALESCE(COUNT(DISTINCT st.student_id),1)),
    'Active'
FROM Class_Schedules cs
LEFT JOIN Student_Timetable st ON st.schedule_id=cs.schedule_id
WHERE trim(COALESCE(cs.room_location,''))<>''
GROUP BY lower(trim(cs.room_location));

CREATE TABLE IF NOT EXISTS Teacher_Availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL REFERENCES Teachers(teacher_id) ON DELETE CASCADE,
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1 CHECK(is_available IN (0,1)),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_teacher_availability_window UNIQUE(teacher_id,day_of_week,start_time,end_time),
    CONSTRAINT check_teacher_availability_time_order CHECK(start_time < end_time)
);

CREATE TABLE IF NOT EXISTS Room_Availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES Rooms(room_id) ON DELETE CASCADE,
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1 CHECK(is_available IN (0,1)),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_room_availability_window UNIQUE(room_id,day_of_week,start_time,end_time),
    CONSTRAINT check_room_availability_time_order CHECK(start_time < end_time)
);

CREATE TABLE IF NOT EXISTS Timetables (
    timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL REFERENCES Departments(department_id),
    term_id INTEGER NOT NULL REFERENCES Academic_Terms(term_id),
    configuration_id INTEGER NOT NULL REFERENCES Timetable_Configurations(configuration_id),
    semester INTEGER NOT NULL CHECK(semester > 0),
    section TEXT NOT NULL DEFAULT 'A',
    status TEXT NOT NULL DEFAULT 'Draft' CHECK(status IN ('Draft','Approved','Published','Archived')),
    created_by INTEGER NOT NULL REFERENCES Users(user_id),
    approved_by INTEGER REFERENCES Users(user_id),
    approved_at DATETIME,
    published_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_timetable_scope UNIQUE(department_id,term_id,semester,section)
);

CREATE TABLE IF NOT EXISTS Timetable_Courses (
    timetable_course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timetable_id INTEGER NOT NULL REFERENCES Timetables(timetable_id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES Courses(course_id),
    teacher_id INTEGER NOT NULL REFERENCES Teachers(teacher_id),
    weekly_sessions INTEGER NOT NULL CHECK(weekly_sessions > 0),
    session_duration_minutes INTEGER NOT NULL DEFAULT 60 CHECK(session_duration_minutes > 0),
    class_type TEXT NOT NULL DEFAULT 'Lecture' CHECK(class_type IN ('Lecture','Lab','Tutorial','Seminar')),
    required_room_type TEXT NOT NULL DEFAULT 'Classroom',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_timetable_course UNIQUE(timetable_id,course_id)
);

CREATE TABLE IF NOT EXISTS Timetable_Sessions (
    timetable_session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timetable_course_id INTEGER NOT NULL REFERENCES Timetable_Courses(timetable_course_id) ON DELETE CASCADE,
    room_id INTEGER NOT NULL REFERENCES Rooms(room_id),
    day_of_week TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    legacy_schedule_id INTEGER REFERENCES Class_Schedules(schedule_id),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_timetable_course_session_slot UNIQUE(timetable_course_id,day_of_week,start_time),
    CONSTRAINT check_timetable_session_time_order CHECK(start_time < end_time)
);

CREATE TABLE IF NOT EXISTS Timetable_Course_Rooms (
    timetable_course_id INTEGER NOT NULL REFERENCES Timetable_Courses(timetable_course_id) ON DELETE CASCADE,
    room_id INTEGER NOT NULL REFERENCES Rooms(room_id),
    PRIMARY KEY(timetable_course_id,room_id)
);

CREATE INDEX IF NOT EXISTS idx_timetable_scope ON Timetables(department_id,term_id,semester,section,status);
CREATE INDEX IF NOT EXISTS idx_timetable_session_room ON Timetable_Sessions(room_id,day_of_week,start_time,end_time);
CREATE INDEX IF NOT EXISTS idx_teacher_availability ON Teacher_Availability(teacher_id,day_of_week,start_time,end_time);

INSERT OR IGNORE INTO Timetable_Configurations
    (name,working_days,day_start_time,day_end_time,slot_minutes,status)
VALUES
    ('University Default','Monday,Tuesday,Wednesday,Thursday,Friday','08:30','15:30',60,'Active');
