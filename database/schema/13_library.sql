-- ===========================================================
-- TABLE: Library
-- PURPOSE:
-- Stores library books, digital resources,
-- borrowing history and AI semantic search metadata.
-- ===========================================================
DROP TABLE IF EXISTS Library;
CREATE TABLE Library (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    publisher TEXT,
    publication_year INTEGER,
    edition TEXT,
    category TEXT,
    language TEXT DEFAULT 'English',
    description TEXT,
    keywords TEXT,
    shelf_location TEXT,
    total_copies INTEGER DEFAULT 1,
    available_copies INTEGER DEFAULT 1,
    digital_copy_path TEXT,
    embedding_vector TEXT,
    ai_summary TEXT,
    status TEXT DEFAULT 'Available'
        CHECK(status IN
        ('Available',
         'Issued',
         'Reserved',
         'Lost',
         'Maintenance')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ===========================================================
-- TABLE: Library_Issues
-- PURPOSE:
-- Tracks issued and returned books.
-- ===========================================================
DROP TABLE IF EXISTS Library_Issues;
CREATE TABLE Library_Issues (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    student_id INTEGER,
    teacher_id INTEGER,
    issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME NOT NULL,
    return_date DATETIME,
    fine_amount REAL DEFAULT 0,
    issue_status TEXT DEFAULT 'Issued'
        CHECK(issue_status IN
        ('Issued',
         'Returned',
         'Late',
         'Lost')),
    remarks TEXT,
    FOREIGN KEY(book_id)
        REFERENCES Library(book_id),
    FOREIGN KEY(student_id)
        REFERENCES Students(student_id),
    FOREIGN KEY(teacher_id)
        REFERENCES Teachers(teacher_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_library_title
ON Library(title);
CREATE INDEX idx_library_author
ON Library(author);
CREATE INDEX idx_library_category
ON Library(category);
CREATE INDEX idx_library_status
ON Library(status);
CREATE INDEX idx_library_issue_student
ON Library_Issues(student_id);
CREATE INDEX idx_library_issue_teacher
ON Library_Issues(teacher_id);
CREATE INDEX idx_library_issue_book
ON Library_Issues(book_id);
