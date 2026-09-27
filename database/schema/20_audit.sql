-- ===========================================================
-- TABLE: Audit_Logs
-- PURPOSE:
-- Immutable audit trail for every important action
-- performed inside the University Operating System.
-- ===========================================================
DROP TABLE IF EXISTS Audit_Logs;
CREATE TABLE Audit_Logs (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_role TEXT
        CHECK(user_role IN
        ('Student',
         'Teacher',
         'Admin',
         'AI Agent',
         'System')),
    module_name TEXT NOT NULL,
    action_type TEXT NOT NULL
        CHECK(action_type IN
        ('Create',
         'Read',
         'Update',
         'Delete',
         'Login',
         'Logout',
         'Approve',
         'Reject',
         'Upload',
         'Download',
         'Verify',
         'AI Decision')),
    table_name TEXT,
    record_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    action_status TEXT DEFAULT 'Success'
        CHECK(action_status IN
        ('Success',
         'Failed',
         'Blocked')),
    ip_address TEXT,
    device_name TEXT,
    session_token TEXT,
    hash_signature TEXT,
    remarks TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ===========================================================
-- TABLE: Audit_Verification
-- PURPOSE:
-- Stores cryptographic verification records
-- for Zero-Trust architecture.
-- ===========================================================
DROP TABLE IF EXISTS Audit_Verification;
CREATE TABLE Audit_Verification (
    verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id INTEGER NOT NULL,
    verification_hash TEXT NOT NULL,
    verification_status TEXT DEFAULT 'Verified'
        CHECK(verification_status IN
        ('Verified',
         'Tampered',
         'Pending')),
    verified_by TEXT DEFAULT 'AI',
    verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(audit_id)
        REFERENCES Audit_Logs(audit_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_audit_user
ON Audit_Logs(user_id);
CREATE INDEX idx_audit_module
ON Audit_Logs(module_name);
CREATE INDEX idx_audit_action
ON Audit_Logs(action_type);
CREATE INDEX idx_audit_table
ON Audit_Logs(table_name);
CREATE INDEX idx_audit_date
ON Audit_Logs(created_at);
CREATE INDEX idx_audit_status
ON Audit_Logs(action_status);
CREATE INDEX idx_verification_status
ON Audit_Verification(verification_status);