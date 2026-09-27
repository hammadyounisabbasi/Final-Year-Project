-- ===========================================================
-- TABLE: Fee_Records
-- PURPOSE:
-- Stores student fee information, payment history,
-- scholarships, fines, and payment verification.
-- ===========================================================
DROP TABLE IF EXISTS Fee_Records;
CREATE TABLE Fee_Records (
    fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    total_fee REAL NOT NULL,
    scholarship_amount REAL DEFAULT 0,
    fine_amount REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    payable_amount REAL NOT NULL,
    paid_amount REAL DEFAULT 0,
    remaining_amount REAL NOT NULL,
    payment_status TEXT DEFAULT 'Pending'
        CHECK(payment_status IN
        ('Pending',
         'Partial',
         'Paid',
         'Overdue',
         'Cancelled')),
    payment_method TEXT
        CHECK(payment_method IN
        ('Cash',
         'Bank Transfer',
         'Online',
         'JazzCash',
         'EasyPaisa',
         'Credit Card')),
    transaction_id TEXT UNIQUE,
    payment_date DATETIME,
    due_date DATETIME NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    remarks TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_fee_student
ON Fee_Records(student_id);
CREATE INDEX idx_fee_status
ON Fee_Records(payment_status);
CREATE INDEX idx_fee_transaction
ON Fee_Records(transaction_id);
CREATE INDEX idx_fee_due_date
ON Fee_Records(due_date);
CREATE INDEX idx_fee_verified
ON Fee_Records(verified);