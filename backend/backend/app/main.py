from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.student import router as student_router
from app.api.teacher import router as teacher_router
from app.api.admin import router as admin_router
from app.api.exam import router as exam_router
from app.api.exam_assistant import router as exam_assistant_router
from app.api.library import router as library_router
from app.services.library_catalog import ensure_library_schema
from app.services.exam_migration import ensure_online_assessment_schema
from app.services.gradebook_migration import ensure_gradebook_schema
from app.core.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Timetable migrations and data repairs are explicit maintenance operations.
    # Startup must never publish or rewrite an administrator's timetable.
    ensure_online_assessment_schema()
    ensure_library_schema()
    ensure_gradebook_schema()
    yield


# ==========================================================
# APPLICATION
# ==========================================================

app = FastAPI(
    title="Zero-Trust Autonomous Campus Ecosystem Using Multi-Agent AI",
    description="University ERP and AI Agentic System",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)


# ==========================================================
# CORS CONFIGURATION
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=(
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
        if settings.APP_ENV != "production"
        else None
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Library-Download-Count"],
)


# ==========================================================
# ROUTERS & STATIC MOUNTS
# ==========================================================

uploads_dir = settings.UPLOAD_DIR
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.include_router(auth_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(admin_router)
app.include_router(exam_router)
app.include_router(exam_assistant_router)
app.include_router(library_router)

# ==========================================================
# ROOT ENDPOINT
# ==========================================================

@app.get("/")
def root():
    return {
        "message": "Zero-Trust Autonomous Campus Ecosystem API is running",
        "status": "online"
    }


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
