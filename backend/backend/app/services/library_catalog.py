"""Shared catalog, safe file storage, and attributable library activity."""
from pathlib import Path
import re
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, BASE_DIR

BOOKS_DIR = settings.LIBRARY_BOOKS_DIR

def ensure_library_schema():
    migration = BASE_DIR / 'database/migrations/v14_library_activity.sql'
    with engine.begin() as conn:
        conn.connection.executescript(migration.read_text(encoding='utf-8'))
    from app.core.database import SessionLocal
    with SessionLocal() as db:
        sync_books(db)

def sync_books(db):
    """Import existing PDFs once by relative path; never rewrite catalog metadata."""
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    known = set(db.execute(text('SELECT digital_copy_path FROM Library')).scalars())
    for path in sorted(BOOKS_DIR.glob('*.pdf')):
        if path.is_symlink() or path.name in known:
            continue
        db.execute(text('''INSERT INTO Library(title,author,category,digital_copy_path)
            VALUES (:title,'Unknown','General',:path)'''),
            {'title': path.stem.replace('_', ' '), 'path': path.name})
    db.commit()

def book_file(book):
    value = book.get('digital_copy_path') or ''
    path = (BOOKS_DIR / value).resolve()
    if not value or path.parent != BOOKS_DIR.resolve() or not path.is_file() or path.suffix.lower() != '.pdf':
        return None
    return path

def catalog(db, query=''):
    rows = [dict(r) for r in db.execute(text('''SELECT b.book_id, b.isbn, b.title, b.author, b.publisher, b.publication_year,
        b.edition, b.category, b.language, b.description, b.keywords, b.shelf_location, b.total_copies,
        b.available_copies, b.status, b.digital_copy_path, b.created_at,
        COALESCE(COUNT(CASE WHEN a.action='download' THEN 1 END), 0) AS download_count
        FROM Library b
        LEFT JOIN Library_Activity a ON a.book_id = b.book_id
        GROUP BY b.book_id
        ORDER BY b.book_id DESC''')).mappings()]
    terms = set(re.findall(r'[\w+#]+', query.lower())) - {'a','an','the','what','is','are','for','of','to','in','me','about','book','books','please','recommend','articles','related'}
    result = []
    for row in rows:
        if not book_file(row):
            continue
        haystack = ' '.join(str(row.get(k) or '') for k in ('title','author','category','description','keywords')).lower()
        score = sum(term in haystack for term in terms)
        if terms and not score:
            continue
        row.pop('digital_copy_path')
        row['score'] = score
        result.append(row)
    return sorted(result, key=lambda r: -r['score'])

def download_summary(db):
    """Return student-facing, database-backed catalog download metrics."""
    rows = catalog(db)
    return {
        'books': len(rows),
        'downloads': sum(int(book.get('download_count') or 0) for book in rows),
        'categories': len({(book.get('category') or 'General').strip().lower() for book in rows}),
        'top_books': sorted(rows, key=lambda book: (-int(book.get('download_count') or 0), book['title']))[:3],
    }

def record(db, user, action, book_id=None, query=None):
    department = db.execute(text('SELECT department_id FROM Students WHERE user_id=:id'), {'id': user.user_id}).scalar()
    db.execute(text('''INSERT INTO Library_Activity(user_id,department_id,book_id,action,query)
        VALUES (:user,:department,:book,:action,:query)'''),
        dict(user=user.user_id, department=department, book=book_id, action=action, query=query))

def record_search(db, user, query, books, action='search'):
    record(db, user, action, query=query)
    for book in books[:20]:
        record(db, user, 'search_match', book['book_id'], query)
    db.commit()
