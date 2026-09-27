-- ===========================================================
-- TABLE: Users
-- PURPOSE:
-- Authentication & Authorization
-- Used by Student, Teacher and Admin Login
-- ===========================================================
DROP TABLE IF EXISTS Users;
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
        CHECK(role IN ('student','teacher','admin')),
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK(is_active IN (0,1)),
    is_verified INTEGER NOT NULL DEFAULT 0
        CHECK(is_verified IN (0,1)),
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    last_login DATETIME,
    password_changed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_users_username
ON Users(username);
CREATE INDEX idx_users_email
ON Users(email);
CREATE INDEX idx_users_role
ON Users(role);
CREATE INDEX idx_users_active
ON Users(is_active);