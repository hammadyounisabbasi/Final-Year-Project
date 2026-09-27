-- ===========================================================
-- TABLE: Security_Events
-- PURPOSE:
-- Stores login attempts, suspicious activities,
-- device tracking and Zero-Trust security events.
-- ===========================================================
DROP TABLE IF EXISTS Security_Events;
CREATE TABLE Security_Events (
    security_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_role TEXT NOT NULL
        CHECK(user_role IN
        ('Student',
         'Teacher',
         'Admin')),
    event_type TEXT NOT NULL
        CHECK(event_type IN
        ('Login',
         'Logout',
         'Password Change',
         'Failed Login',
         'Permission Denied',
         'Suspicious Activity',
         'File Access',
         'Data Modification',
         'Exam Access',
         'AI Alert')),
    ip_address TEXT,
    device_name TEXT,
    operating_system TEXT,
    browser TEXT,
    location TEXT,
    login_status TEXT
        CHECK(login_status IN
        ('Success',
         'Failed',
         'Blocked')),
    risk_score REAL DEFAULT 0,
    ai_detected BOOLEAN DEFAULT FALSE,
    ai_reason TEXT,
    session_token TEXT,
    event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    FOREIGN KEY(user_id)
        REFERENCES Users(user_id)
);
-- ===========================================================
-- TABLE: Active_Sessions
-- PURPOSE:
-- Stores active login sessions.
-- ===========================================================
DROP TABLE IF EXISTS Active_Sessions;
CREATE TABLE Active_Sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    device_name TEXT,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_time DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY(user_id)
        REFERENCES Users(user_id)
);
-- ===========================================================
-- TABLE: Threat_Logs
-- PURPOSE:
-- Stores AI detected cyber security threats.
-- ===========================================================
DROP TABLE IF EXISTS Threat_Logs;
CREATE TABLE Threat_Logs (
    threat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_event_id INTEGER,
    threat_level TEXT
        CHECK(threat_level IN
        ('Low',
         'Medium',
         'High',
         'Critical')),
    threat_type TEXT,
    description TEXT,
    action_taken TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(security_event_id)
        REFERENCES Security_Events(security_event_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_security_user
ON Security_Events(user_id);
CREATE INDEX idx_security_event
ON Security_Events(event_type);
CREATE INDEX idx_security_time
ON Security_Events(event_time);
CREATE INDEX idx_security_risk
ON Security_Events(risk_score);
CREATE INDEX idx_session_user
ON Active_Sessions(user_id);
CREATE INDEX idx_session_token
ON Active_Sessions(session_token);
CREATE INDEX idx_threat_level
ON Threat_Logs(threat_level);
CREATE INDEX idx_threat_status
ON Threat_Logs(resolved);
