-- ===========================================================
-- TABLE: Admins
-- PURPOSE:
-- Stores administrator profile information.
-- Linked with Users.
-- ===========================================================

CREATE TABLE IF NOT EXISTS Admins (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL UNIQUE,

    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,

    designation TEXT,
    phone TEXT,
    office_email TEXT UNIQUE,
    profile_photo TEXT,

    status TEXT NOT NULL DEFAULT 'Active'
        CHECK(status IN ('Active', 'Inactive')),

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
);

-- ===========================================================
-- INDEXES
-- ===========================================================

CREATE INDEX IF NOT EXISTS idx_admin_user
ON Admins(user_id);

CREATE INDEX IF NOT EXISTS idx_admin_email
ON Admins(office_email);

CREATE INDEX IF NOT EXISTS idx_admin_status
ON Admins(status);