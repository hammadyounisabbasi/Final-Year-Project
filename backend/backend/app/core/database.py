from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

import sqlite3

from app.core.config import PROJECT_ROOT, settings


# ==========================================================
# PROJECT ROOT
# ==========================================================

# database.py location:
# backend/backend/app/core/database.py
#
# Project root:
# Zero-Trust Autonomous Campus Ecosystem Using Multi-Agent AI/
#
# Existing database:
# database/university.db

BASE_DIR = PROJECT_ROOT


def _database_url() -> str:
    configured = settings.DATABASE_URL.strip()
    if configured == "sqlite:///:memory:":
        return configured
    if configured.startswith("sqlite:///"):
        raw_path = configured.removeprefix("sqlite:///")
        path = Path(raw_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.resolve().as_posix()}"
    return configured


DATABASE_URL = _database_url()


# ==========================================================
# DATABASE ENGINE
# ==========================================================

engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite:"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)


# ==========================================================
# ENABLE SQLITE FOREIGN KEYS
# ==========================================================

@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):

    if isinstance(dbapi_connection, sqlite3.Connection):

        cursor = dbapi_connection.cursor()

        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.close()


# ==========================================================
# DATABASE SESSION
# ==========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==========================================================
# BASE MODEL
# ==========================================================

Base = declarative_base()


# ==========================================================
# DATABASE DEPENDENCY
# ==========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
        
