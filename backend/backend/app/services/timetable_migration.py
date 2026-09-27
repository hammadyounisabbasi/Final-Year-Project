"""Explicit, idempotent installer for the data-driven timetable schema."""
from pathlib import Path

from app.core.database import engine


MIGRATION = Path(__file__).resolve().parents[4] / "database" / "migrations" / "v21_data_driven_timetables.sql"


def ensure_data_driven_timetable_schema():
    sql = MIGRATION.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.connection.executescript(sql)


def schema_status():
    expected = {"Rooms", "Room_Availability", "Timetable_Configurations", "Teacher_Availability", "Timetables", "Timetable_Courses", "Timetable_Course_Rooms", "Timetable_Sessions"}
    with engine.connect() as connection:
        tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
        legacy = {
            "Class_Schedules": connection.exec_driver_sql("SELECT COUNT(*) FROM Class_Schedules").scalar_one(),
            "Student_Timetable": connection.exec_driver_sql("SELECT COUNT(*) FROM Student_Timetable").scalar_one(),
        }
    return {"applied": expected <= tables, "missing": sorted(expected - tables), "legacy_counts": legacy}


if __name__ == "__main__":
    ensure_data_driven_timetable_schema()
    print(f"Applied {MIGRATION.name}: {schema_status()}")
