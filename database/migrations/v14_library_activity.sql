CREATE TABLE IF NOT EXISTS Library_Activity (
 activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES Users(user_id),
 department_id INTEGER REFERENCES Departments(department_id),
 book_id INTEGER REFERENCES Library(book_id),
 action TEXT NOT NULL CHECK(action IN ('search','search_match','view','download','chat')),
 query TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_library_activity_book ON Library_Activity(book_id, action);
CREATE INDEX IF NOT EXISTS idx_library_activity_user ON Library_Activity(user_id, created_at);
