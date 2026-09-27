-- Safe additive migration: result publication is controlled per academic term.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Academic_Terms (
    term_id INTEGER PRIMARY KEY AUTOINCREMENT,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Upcoming'
        CHECK(status IN ('Upcoming', 'Active', 'Completed')),
    completed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(academic_year, semester)
);

CREATE INDEX IF NOT EXISTS idx_academic_terms_status ON Academic_Terms(status);

-- Backfill historical terms conservatively: the latest semester in each
-- academic year is active; older semesters are historical completed terms.
-- Registrar staff can correct a status through the admin API before publication.
INSERT OR IGNORE INTO Academic_Terms (academic_year, semester, status)
SELECT academic_year,
       semester,
       CASE WHEN semester < MAX(semester) OVER (PARTITION BY academic_year)
            THEN 'Completed' ELSE 'Active' END
FROM Enrollments;
