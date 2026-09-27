-- ===========================================================
-- FILE: 01_admins.sql
-- PURPOSE: Initial System Administrators
-- PROJECT: University of Haripur ERP (Virtual University)
-- ===========================================================

PRAGMA foreign_keys = ON;

-- ===========================================================
-- DEFAULT LOGIN CREDENTIALS
-- ===========================================================
--
-- VC Admin
-- Email    : vc.admin@uoh.edu.pk
-- Password : UOH@2025
--
-- Dean Admin
-- Email    : dean.admin@uoh.edu.pk
-- Password : UOH@2026
--
-- NOTE:
-- Passwords are stored as bcrypt hashes.
-- Use the plain passwords above for login.
--
-- ===========================================================


INSERT INTO Users
(
    username,
    email,
    password_hash,
    role,
    is_active,
    is_verified,
    created_at
)
VALUES
(
    'vc_admin',
    'vc.admin@uoh.edu.pk',
    'UOH@2025',
    'admin',
    1,
    1,
    CURRENT_TIMESTAMP
),

(
    'dean_admin',
    'dean.admin@uoh.edu.pk',
    'UOH@2026',
    'admin',
    1,
    1,
    CURRENT_TIMESTAMP
);

-- ===========================================================
-- END OF FILE
-- ===========================================================