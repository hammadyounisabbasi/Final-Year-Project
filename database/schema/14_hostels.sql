-- ===========================================================
-- TABLE: Hostels
-- PURPOSE:
-- Stores hostel information, room allocation,
-- occupancy and student accommodation records.
-- ===========================================================
DROP TABLE IF EXISTS Hostels;
CREATE TABLE Hostels (
    hostel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostel_name TEXT NOT NULL,
    hostel_type TEXT
        CHECK(hostel_type IN
        ('Boys',
         'Girls',
         'Faculty',
         'Guest')),
    block_name TEXT,
    room_number TEXT NOT NULL,
    room_type TEXT
        CHECK(room_type IN
        ('Single',
         'Double',
         'Triple',
         'Dormitory')),
    floor_number INTEGER,
    capacity INTEGER NOT NULL,
    occupied_seats INTEGER DEFAULT 0,
    room_status TEXT DEFAULT 'Available'
        CHECK(room_status IN
        ('Available',
         'Full',
         'Maintenance',
         'Reserved')),
    monthly_fee REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ===========================================================
-- TABLE: Hostel_Allocations
-- PURPOSE:
-- Stores student room allocations.
-- ===========================================================
DROP TABLE IF EXISTS Hostel_Allocations;
CREATE TABLE Hostel_Allocations (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    hostel_id INTEGER NOT NULL,
    seat_number TEXT,
    allocation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expected_checkout DATE,
    actual_checkout DATE,
    allocation_status TEXT DEFAULT 'Active'
        CHECK(allocation_status IN
        ('Active',
         'Completed',
         'Cancelled')),
    remarks TEXT,
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),
    FOREIGN KEY(hostel_id)
        REFERENCES Hostels(hostel_id),
    UNIQUE(student_id)
);
-- ===========================================================
-- TABLE: Hostel_Complaints
-- PURPOSE:
-- Stores hostel maintenance and complaint records.
-- ===========================================================
DROP TABLE IF EXISTS Hostel_Complaints;
CREATE TABLE Hostel_Complaints (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    hostel_id INTEGER NOT NULL,
    complaint_type TEXT,
    description TEXT NOT NULL,
    complaint_status TEXT DEFAULT 'Pending'
        CHECK(complaint_status IN
        ('Pending',
         'In Progress',
         'Resolved',
         'Rejected')),
    reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),
    FOREIGN KEY(hostel_id)
        REFERENCES Hostels(hostel_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_hostel_status
ON Hostels(room_status);
CREATE INDEX idx_hostel_student
ON Hostel_Allocations(student_id);
CREATE INDEX idx_hostel_room
ON Hostel_Allocations(hostel_id);
CREATE INDEX idx_hostel_complaint_student
ON Hostel_Complaints(student_id);
CREATE INDEX idx_hostel_complaint_status
ON Hostel_Complaints(complaint_status);
