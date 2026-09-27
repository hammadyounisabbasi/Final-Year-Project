"""Apply the additive v21 timetable migration to the configured development DB."""
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/backend"))

from app.core.database import DATABASE_PATH
from app.services.timetable_migration import ensure_data_driven_timetable_schema, schema_status


if DATABASE_PATH.resolve() != (ROOT / "database/university.db").resolve():
    raise SystemExit(f"Refusing unexpected database path: {DATABASE_PATH}")

ensure_data_driven_timetable_schema()
print(f"Applied v21 to {DATABASE_PATH}: {schema_status()}")
