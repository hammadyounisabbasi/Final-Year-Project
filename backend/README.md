# ACOS Backend Architecture & API Engine

> Deployment note: install the canonical dependencies from the repository-root `requirements.txt`. Production settings and persistent-storage requirements are documented in [`../DEPLOYMENT.md`](../DEPLOYMENT.md).

> **High-Performance FastAPI Backend with Zero-Trust Security, Dynamic Context-Grounded AI, and Relational SQLite Engine**

---

## 📌 Overview

The **Autonomous Campus Operating System (ACOS)** backend is the central computational and orchestration engine of the platform. Built on **FastAPI (Python 3.12+)** and **SQLAlchemy 2.0**, it provides high-throughput, asynchronous RESTful APIs, strict Role-Based Access Control (RBAC), and a dynamic Multi-Provider AI Subsystem that guarantees zero hallucination through deterministic database grounding.

---

## 🏛️ Directory Structure

```
backend/
└── backend/
    ├── app/
    │   ├── api/                   # REST API Routers & Endpoint Controllers
    │   │   ├── auth.py            # Authentication & JWT token issuing
    │   │   ├── student.py         # Student Portal APIs (results, attendance, AI, etc.)
    │   │   ├── teacher.py         # Teacher Portal APIs (gradebook, roster, AI, etc.)
    │   │   ├── admin.py           # Admin Governance & AI Watchdog endpoints
    │   │   └── exam.py            # Online examination & proctoring APIs
    │   │
    │   ├── core/                  # Core Configuration & Security Framework
    │   │   ├── config.py          # Environment settings, secrets, and provider keys
    │   │   ├── database.py        # SQLAlchemy engine, session maker, DB dependency
    │   │   ├── security.py        # Bcrypt password hashing & verification
    │   │   └── auth.py            # JWT token creation, decoding & RBAC dependencies
    │   │
    │   ├── models/                # SQLAlchemy Relational ORM Models (20 Models)
    │   │   ├── user.py            # Base authentication user entity
    │   │   ├── student.py         # Student profile & academic metadata
    │   │   ├── teacher.py         # Faculty member profile & department link
    │   │   ├── admin.py           # University administrator entity
    │   │   ├── department.py      # Academic departments & faculties
    │   │   ├── course.py          # Course catalog, credit hours & syllabus
    │   │   ├── enrollment.py      # Student-Course registration mapping
    │   │   ├── attendance.py      # Lecture-by-lecture attendance records
    │   │   ├── grade.py           # Assessment & exam grades
    │   │   ├── assignment.py      # Course assignments & deadlines
    │   │   ├── submission.py      # Student assignment submissions & feedback
    │   │   ├── class_schedule.py  # Weekly timetable schedule & room allocations
    │   │   ├── student_timetable.py # Normalized student timetable mapping
    │   │   ├── academic_term.py   # Semesters, terms & academic years
    │   │   ├── course_result.py   # Final course grades, marks & GPA points
    │   │   ├── semester_gpa.py    # Semester-wise GPA calculations
    │   │   ├── student_cgpa.py    # Cumulative CGPA & credit progression
    │   │   ├── exam.py            # Online assessments, questions & options
    │   │   └── role.py            # User roles & permissions
    │   │
    │   ├── schemas/               # Pydantic Schemas for Request/Response Validation
    │   │   ├── auth.py            # Login requests & token payloads
    │   │   ├── student.py         # Student request & response models
    │   │   ├── teacher.py         # Teacher request & gradebook models
    │   │   ├── admin.py           # Administrative management schemas
    │   │   ├── exam.py            # Online assessment schemas
    │   │   └── ai_assistant.py    # AI chat payloads & provider responses
    │   │
    │   ├── services/              # Business Logic & AI Orchestration Services
    │   │   ├── ai_providers.py    # Multi-Provider AI Fallback Engine (Groq/Gemini/HF/Ollama/DB)
    │   │   ├── student_ai_assistant.py # Student AI Advisor service
    │   │   ├── student_ai_context.py   # Student live database context extractor
    │   │   ├── teacher_ai_assistant.py # Teacher AI Assistant service
    │   │   ├── teacher_ai_context.py   # Teacher live database context extractor
    │   │   ├── academic_results.py     # GPA/CGPA computation & analytics
    │   │   ├── timetable_creator.py    # Automated timetable generator
    │   │   ├── timetable_normalizer.py # Schedule normalization & slotting
    │   │   ├── weekly_session_expander.py # Attendance session expander
    │   │   ├── auth_service.py         # User credential verification
    │   │   ├── exam_migration.py       # Automated online exam tables migration
    │   │   ├── student_timetable_migration.py # Timetable schema migration
    │   │   └── timetable_coverage_migration.py # Schedule integrity migration
    │   │
    │   └── main.py                # FastAPI Application entry point & lifespan hooks
    │
    ├── test_agent_suite.py        # Comprehensive AI Agent verification suite
    ├── test_teacher_ai.py         # Dedicated Teacher AI verification script
    ├── requirements.txt           # Python dependency requirements
    ├── .env.example               # Environment variables template
    └── uploads/                   # Stored files & assignment attachments
```

---

## 🔌 API Router Modules

### 1. Authentication Router (`app/api/auth.py`)
- `POST /auth/login`: Unified login endpoint for Students, Teachers, and Admins. Validates credentials, issues signed JWT tokens, and returns user identity metadata.

### 2. Student Router (`app/api/student.py`)
- `GET /student/profile`: Returns student profile, degree program, and department info.
- `GET /student/courses`: Lists currently registered courses and instructors.
- `GET /student/timetable`: Returns weekly class schedule with room numbers and timings.
- `GET /student/attendance`: Returns attendance statistics, percentages, and warning flags.
- `GET /student/assignments`: Fetches active assignments and submission status.
- `POST /student/assignments/{id}/submit`: Handles student assignment file/text submission.
- `GET /student/results`: Delivers semester-wise GPA progression, total CGPA, and Chart.js payload.
- `GET /student/fees`: Displays fee challans, paid vouchers, and pending dues.
- `GET /student/library`: Queries library book issues and due return dates.
- `GET /student/notices`: Returns university notices and campus circulars.
- `GET /student/ai/greeting`: Delivers a personalized, context-grounded greeting.
- `POST /student/ai/chat`: Interactive multi-turn chat with the AI Academic Advisor.
- `GET /student/ai/providers`: Returns active AI inference provider health and availability.

### 3. Teacher Router (`app/api/teacher.py`)
- `GET /teacher/profile`: Faculty member profile details.
- `GET /teacher/courses`: Assigned teaching courses and section breakdown.
- `GET /teacher/courses/{id}/students`: Enrolled student roster per course.
- `GET /teacher/schedule`: Faculty weekly lecture schedule.
- `POST /teacher/attendance`: Submits and updates student attendance records.
- `GET /teacher/assignments`: Manages course assignments and student submissions.
- `POST /teacher/assignments`: Creates a new assignment with max marks and deadline.
- `POST /teacher/assignments/grade`: Submits grades and feedback for student submissions.
- `GET /teacher/gradebook/{course_id}`: Retrieves complete class gradebook (sessional, midterm, final).
- `POST /teacher/gradebook/save`: Batch saves student grade marks.
- `GET /teacher/ai/greeting`: Delivers dynamic faculty briefing greeting.
- `POST /teacher/ai/chat`: Interactive chat with the Teacher AI Assistant.
- `GET /teacher/ai/providers`: Checks active AI provider statuses.

### 4. Admin Router (`app/api/admin.py`)
- `GET /admin/dashboard/stats`: High-level campus metrics (students, faculty, active agents).
- `GET /admin/students`: Student admission directory & status management.
- `GET /admin/faculty`: Faculty directory & department assignments.
- `GET /admin/audit-logs`: Zero-Trust immutable audit logs of sensitive system operations.
- `GET /admin/watchdogs/status`: Real-time health status of campus AI watchdog agents.

### 5. Examination Router (`app/api/exam.py`)
- `GET /exam/list`: List scheduled exams and online assessments.
- `POST /exam/create`: Create online quiz/assessment with time limits and questions.
- `POST /exam/submit`: Student assessment submission with automated grading.

---

## 🤖 Multi-Provider AI Architecture

The backend includes an intelligent fallback mechanism (`app/services/ai_providers.py`):

```
                      User Chat Request
                              │
                              ▼
                 Authenticated Session (JWT)
                              │
                              ▼
               Live Database Context Extraction
       (student_ai_context.py / teacher_ai_context.py)
                              │
                              ▼
             ┌─────────────────────────────────┐
             │       AIProviderManager         │
             └────────────────┬────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
  1. Groq Cloud        2. Google Gemini     3. Hugging Face
  (Llama 3.3 70B)      (Gemini 2.0 Flash)   (Llama 3.1 8B)
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │ (If cloud providers fail / rate limit)
                              ▼
                       4. Local Ollama
                    (qwen2.5 / llama3.2)
                              │
                              │ (If offline / unconfigured)
                              ▼
               5. Direct Database Rule-Based
                     Fallback Generator
```

### Deterministic Context Grounding
Before prompting any LLM, the backend queries the database for:
- Student: Current CGPA, semester GPAs, course attendance %, fee dues, assignment deadlines, today's schedule.
- Teacher: Courses taught, student counts, low-attendance alerts, today's classes, pending submissions to grade.

This grounds the LLM strictly within verified database records, preventing hallucinations.

---

## 🚀 Running the Backend Server

### 1. Setup Virtual Environment & Install Dependencies
```bash
# From repository root
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate    # Linux/macOS

python -m pip install -r requirements.txt
```

### 2. Configure `.env`
Copy the repository-root `.env.example` to `.env` and fill in your keys. Keep `CORS_ORIGINS` explicit in production:
```env
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Provider Keys
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...
HUGGINGFACE_API_KEY=hf_...
OLLAMA_BASE_URL=http://127.0.0.1:11434
CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

### 3. Launch Uvicorn Server
```bash
uvicorn app.main:app --app-dir backend/backend --reload --host 127.0.0.1 --port 8000
```

- **Swagger UI Interactive Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/health`

---

## 🧪 Testing Backend & AI Services

```bash
# Run AI Agent Verification Suite
python test_agent_suite.py

# Run Dedicated Teacher AI Test
python test_teacher_ai.py
```
