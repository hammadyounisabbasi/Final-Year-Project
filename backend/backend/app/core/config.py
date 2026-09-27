import os
from pathlib import Path

from dotenv import load_dotenv


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[4]

# Local files provide development defaults. Real environment variables always win.
env_paths = [
    PROJECT_ROOT / ".env",
    CURRENT_FILE.parents[2] / ".env",
    Path.cwd() / ".env",
]
for p in env_paths:
    if p.exists():
        load_dotenv(p, override=False)


def _csv(name: str, default: str = "") -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv(name, default).split(",") if item.strip()]


def _path(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else PROJECT_ROOT / value



class Settings:
    PROJECT_NAME: str = (
        "Zero-Trust Autonomous Campus Ecosystem Using Multi-Agent AI"
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "")

    APP_ENV: str = os.getenv("APP_ENV", "development").strip().lower()

    DEBUG: bool = os.getenv("DEBUG", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///database/university.db",
    )

    CORS_ORIGINS: list[str] = _csv(
        "CORS_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000",
    )

    UPLOAD_DIR: Path = _path("UPLOAD_DIR", "backend/backend/uploads")

    LIBRARY_BOOKS_DIR: Path = _path(
        "LIBRARY_BOOKS_DIR",
        "frontend/Admin_dashboard/Books",
    )


settings = Settings()


# Safety check
if not settings.SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Add SECRET_KEY to the .env file."
    )

if settings.APP_ENV == "production" and (
    len(settings.SECRET_KEY) < 32
    or settings.SECRET_KEY == "replace-with-a-long-random-secret"
):
    raise RuntimeError("Production SECRET_KEY must be a random value of at least 32 characters.")
