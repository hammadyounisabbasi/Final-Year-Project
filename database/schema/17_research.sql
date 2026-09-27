-- ===========================================================
-- TABLE: Research
-- PURPOSE:
-- Stores faculty and student research projects,
-- publications, AI embeddings and semantic search metadata.
-- ===========================================================
DROP TABLE IF EXISTS Research;
CREATE TABLE Research (
    research_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    keywords TEXT,
    department_id INTEGER,
    supervisor_id INTEGER,
    author_type TEXT
        CHECK(author_type IN
        ('Student',
         'Teacher',
         'Research Group')),
    author_id INTEGER NOT NULL,
    publication_type TEXT
        CHECK(publication_type IN
        ('Journal',
         'Conference',
         'Thesis',
         'Book',
         'Patent',
         'Technical Report')),
    publication_status TEXT DEFAULT 'Draft'
        CHECK(publication_status IN
        ('Draft',
         'Submitted',
         'Accepted',
         'Published',
         'Rejected')),
    publication_date DATE,
    doi TEXT,
    journal_name TEXT,
    citation_count INTEGER DEFAULT 0,
    document_path TEXT,
    embedding_vector TEXT,
    ai_summary TEXT,
    semantic_tags TEXT,
    visibility TEXT DEFAULT 'Private'
        CHECK(visibility IN
        ('Private',
         'University',
         'Public')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(department_id)
        REFERENCES Departments(department_id),
    FOREIGN KEY(supervisor_id)
        REFERENCES Teachers(teacher_id)
);
-- ===========================================================
-- TABLE: Research_Funding
-- PURPOSE:
-- Stores grants and funding opportunities.
-- ===========================================================
DROP TABLE IF EXISTS Research_Funding;
CREATE TABLE Research_Funding (
    funding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_id INTEGER NOT NULL,
    funding_agency TEXT NOT NULL,
    grant_title TEXT,
    amount REAL,
    currency TEXT DEFAULT 'PKR',
    application_date DATE,
    approval_date DATE,
    funding_status TEXT DEFAULT 'Pending'
        CHECK(funding_status IN
        ('Pending',
         'Approved',
         'Rejected',
         'Completed')),
    remarks TEXT,
    FOREIGN KEY(research_id)
        REFERENCES Research(research_id)
);
-- ===========================================================
-- INDEXES
-- ===========================================================
CREATE INDEX idx_research_title
ON Research(title);
CREATE INDEX idx_research_author
ON Research(author_id);
CREATE INDEX idx_research_department
ON Research(department_id);
CREATE INDEX idx_research_status
ON Research(publication_status);
CREATE INDEX idx_research_visibility
ON Research(visibility);
CREATE INDEX idx_research_funding
ON Research_Funding(research_id);