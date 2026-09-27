from pathlib import Path

from app.core.database import engine


def ensure_timetable_coverage() -> None:
    """Backfill missing term schedules from approved course-teacher templates."""
    migration = Path(__file__).resolve().parents[4] / "database" / "migrations" / "v15_timetable_coverage.sql"
    with engine.begin() as connection:
        connection.connection.executescript(migration.read_text(encoding="utf-8"))
