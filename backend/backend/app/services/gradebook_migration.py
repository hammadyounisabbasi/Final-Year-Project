from pathlib import Path

from app.core.database import engine


def ensure_gradebook_schema() -> None:
    migration = Path(__file__).resolve().parents[4] / "database" / "migrations" / "v17_dynamic_gradebook.sql"
    with engine.begin() as connection:
        connection.connection.executescript(migration.read_text(encoding="utf-8"))