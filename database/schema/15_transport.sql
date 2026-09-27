-- ===========================================================
-- TABLE: Transport
-- PURPOSE:
-- Stores university buses, routes, drivers,
-- and student transport allocations.
-- ===========================================================
DROP TABLE IF EXISTS Transport;
CREATE TABLE Transport (
    transport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_number TEXT UNIQUE NOT NULL,
    vehicle_type TEXT
        CHECK(vehicle_type IN
        ('Bus',
         'Van',
         'Coaster',
         'Car')),
    driver_name TEXT NOT NULL,
    driver_phone TEXT,
    route_name TEXT NOT NULL,
    start_location TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_time TIME,
    arrival_time TIME,
    total_seats INTEGER NOT NULL,
    available_seats INTEGER NOT NULL,
    vehicle_status TEXT DEFAULT 'Active'
        CHECK(vehicle_status IN
        ('Active',
         'Maintenance',
         'Out of Service')),
    gps_enabled BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ===========================================================
-- TABLE: Transport_Allocations
-- PURPOSE:
-- Stores student transport registrations.
-- ===========================================================
DROP TABLE IF EXISTS Transport_Allocations;
CREATE TABLE Transport_Allocations (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    transport_id INTEGER NOT NULL,
    pickup_point TEXT,
    drop_point TEXT,
    allocation_status TEXT DEFAULT 'Active'
        CHECK(allocation_status IN
        ('Active',
         'Cancelled',
         'Completed')),
    allocation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),
    FOREIGN KEY(transport_id)
        REFERENCES Transport(transport_id),
    UNIQUE(student_id)
);
-- ===========================================================
-- TABLE: Transport_Trips
-- PURPOSE:
-- Stores daily transport trip logs.
-- ===========================================================
DROP TABLE IF EXISTS Transport_Trips;
CREATE TABLE Transport_Trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transport_id INTEGER NOT NULL,
    trip_date DATE NOT NULL,
    departure_actual DATETIME,
    arrival_actual DATETIME,
    trip_status TEXT DEFAULT 'Scheduled'
        CHECK(trip_status IN
        ('Scheduled',
         'Running',
         'Completed',
         'Cancelled')),
    remarks TEXT,
    FOREIGN KEY(transport_id)
        REFERENCES Transport(transport_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_transport_route
ON Transport(route_name);
CREATE INDEX idx_transport_status
ON Transport(vehicle_status);
CREATE INDEX idx_transport_student
ON Transport_Allocations(student_id);
CREATE INDEX idx_transport_vehicle
ON Transport_Allocations(transport_id);
CREATE INDEX idx_transport_trip
ON Transport_Trips(trip_date);
CREATE INDEX idx_transport_trip_status
ON Transport_Trips(trip_status);