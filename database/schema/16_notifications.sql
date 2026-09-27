-- ===========================================================
-- TABLE: Notifications
-- PURPOSE:
-- Stores all system notifications for students,
-- teachers and administrators.
-- ===========================================================
DROP TABLE IF EXISTS Notifications;
CREATE TABLE Notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_type TEXT NOT NULL
        CHECK(recipient_type IN
        ('Student',
         'Teacher',
         'Admin',
         'Department',
         'System')),
    recipient_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT
        CHECK(notification_type IN
        ('Information',
         'Success',
         'Warning',
         'Error',
         'Reminder',
         'AI Recommendation',
         'Security Alert')),
    priority TEXT DEFAULT 'Normal'
        CHECK(priority IN
        ('Low',
         'Normal',
         'High',
         'Critical')),
    sender TEXT DEFAULT 'System',
    is_read BOOLEAN DEFAULT FALSE,
    action_url TEXT,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_notification_recipient
ON Notifications(recipient_id);
CREATE INDEX idx_notification_type
ON Notifications(notification_type);
CREATE INDEX idx_notification_priority
ON Notifications(priority);
CREATE INDEX idx_notification_read
ON Notifications(is_read);
CREATE INDEX idx_notification_created
ON Notifications(created_at);