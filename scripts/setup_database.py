"""Build a fresh SQLite database from the versioned SQL sources."""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_DIR = PROJECT_ROOT / "database"


def _ordered_sql(directory: Path, prefix: str | None = None) -> list[Path]:
    files = [path for path in directory.glob("*.sql") if path.stat().st_size]
    if prefix:
        files = [path for path in files if path.name != prefix]

    def key(path: Path) -> tuple[int, str]:
        match = re.match(r"(?:v)?(\d+)", path.stem, re.IGNORECASE)
        return (int(match.group(1)) if match else 10_000, path.name.casefold())

    return sorted(files, key=key)


def _run_sql(connection: sqlite3.Connection, path: Path) -> None:
    try:
        connection.executescript(path.read_text(encoding="utf-8-sig"))
    except sqlite3.Error as error:
        raise RuntimeError(f"Failed while applying {path.relative_to(PROJECT_ROOT)}: {error}") from error


def build_database(target: Path, include_seed: bool, force: bool) -> None:
    target = target.resolve()
    if target.exists() and not force:
        raise FileExistsError(f"{target} already exists; pass --force to replace it")
    target.parent.mkdir(parents=True, exist_ok=True)

    handle, temporary_name = tempfile.mkstemp(prefix=f".{target.stem}-", suffix=".db", dir=target.parent)
    os.close(handle)
    temporary = Path(temporary_name)

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(temporary)
        connection.execute("PRAGMA foreign_keys = ON")

        for sql_file in _ordered_sql(DATABASE_DIR / "schema", "00_create_database.sql"):
            _run_sql(connection, sql_file)

        if include_seed:
            for sql_file in _ordered_sql(DATABASE_DIR / "seed"):
                _run_sql(connection, sql_file)

        for sql_file in _ordered_sql(DATABASE_DIR / "migrations"):
            _run_sql(connection, sql_file)

        trigger_file = DATABASE_DIR / "triggers" / "22_triggers.sql"
        if trigger_file.exists() and trigger_file.stat().st_size:
            _run_sql(connection, trigger_file)

        for sql_file in _ordered_sql(DATABASE_DIR / "views"):
            _run_sql(connection, sql_file)

        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key validation failed with {len(violations)} violation(s)")
        connection.close()
        connection = None
        os.replace(temporary, target)
    except Exception:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)
        raise

    print(f"Created {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=DATABASE_DIR / "university.db",
        help="Output SQLite file (default: database/university.db)",
    )
    parser.add_argument("--without-seed", action="store_true", help="Create schema without demo data")
    parser.add_argument("--force", action="store_true", help="Replace an existing database after a successful build")
    args = parser.parse_args()
    build_database(args.database, include_seed=not args.without_seed, force=args.force)


if __name__ == "__main__":
    main()
