from pathlib import Path
from sqlalchemy import text
from app.core.database import engine


def ensure_online_assessment_schema() -> None:
    """Apply the narrowly scoped, idempotent online-assessment migration."""
    migration = Path(__file__).resolve().parents[4] / "database" / "migrations" / "v13_online_assessments.sql"
    with engine.begin() as connection:
        raw = connection.connection
        raw.executescript(migration.read_text(encoding="utf-8"))
