-- ===========================================================
-- TABLE: Documents
-- PURPOSE:
-- Stores all uploaded documents for students,
-- teachers and university operations.
-- Supports AI verification and Zero-Trust architecture.
-- ===========================================================
DROP TABLE IF EXISTS Documents;
CREATE TABLE Documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_type TEXT NOT NULL
        CHECK(owner_type IN
        ('Student',
         'Teacher',
         'Admin',
         'Department')),
    owner_id INTEGER NOT NULL,
    document_type TEXT NOT NULL
        CHECK(document_type IN
        ('CNIC',
         'Transcript',
         'Degree',
         'Certificate',
         'Assignment',
         'Fee Challan',
         'Admission Form',
         'Medical Certificate',
         'Research Paper',
         'Other')),
    file_name TEXT NOT NULL,
    original_file_name TEXT,
    file_path TEXT NOT NULL,
    file_extension TEXT,
    file_size INTEGER,
    mime_type TEXT,
    file_hash TEXT NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER,
    verification_status TEXT DEFAULT 'Pending'
        CHECK(verification_status IN
        ('Pending',
         'Verified',
         'Rejected')),
    verified_by INTEGER,
    verified_at DATETIME,
    ai_verified BOOLEAN DEFAULT FALSE,
    ai_confidence REAL,
    remarks TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(uploaded_by)
        REFERENCES Users(user_id),
    FOREIGN KEY(verified_by)
        REFERENCES Users(user_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_document_owner
ON Documents(owner_id);
CREATE INDEX idx_document_type
ON Documents(document_type);
CREATE INDEX idx_document_status
ON Documents(verification_status);
CREATE INDEX idx_document_hash
ON Documents(file_hash);
CREATE INDEX idx_document_uploaded
ON Documents(upload_date);
CREATE INDEX idx_document_active
ON Documents(is_active);