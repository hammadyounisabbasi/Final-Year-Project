from pathlib import Path

from sqlalchemy import text

from app.core.database import engine


def ensure_student_timetable_schema() -> None:
    """Apply the timetable migration once; later application starts are read-only."""
    migration = Path(__file__).resolve().parents[4] / "database" / "migrations" / "v14_student_timetable.sql"
    with engine.begin() as connection:
        table_exists = connection.execute(text(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'Student_Timetable'"
        )).scalar()
        if table_exists:
            return
        connection.connection.executescript(migration.read_text(encoding="utf-8"))
