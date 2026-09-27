# Autonomous Campus Operating System (ACOS)

> **A Zero-Trust Autonomous Campus Ecosystem Powered by Multi-Agent AI & Modern Web Architecture**

![Status](https://img.shields.io/badge/Status-Active%20Development%20%26%20Testing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red)
![Database](https://img.shields.io/badge/SQLite-Relational%20%26%20Migrations-003B57)
![AI Providers](https://img.shields.io/badge/AI%20Providers-Groq%20%7C%20Gemini%20%7C%20HF%20%7C%20Ollama-orange)
![Frontend](https://img.shields.io/badge/Frontend-HTML5%20%7C%20CSS3%20%7C%20Vanilla%20JS-yellow)

---

## 📌 Project Overview

The **Autonomous Campus Operating System (ACOS)** is an enterprise-grade university management and AI orchestration platform. Developed as a research-driven Final Year Project (FYP) at the **Department of Computer Science, University of Haripur**, ACOS transcends conventional Campus Management Systems (CMS) by unifying **Role-Based Access Control (RBAC)**, **Zero-Trust Security Principles**, and **Context-Grounded Multi-Agent AI Assistants**.

ACOS provides three fully functional web portals for **Students**, **Faculty Members (Teachers)**, and **University Administrators**, backed by a high-performance **FastAPI** backend and an intelligent **Multi-Provider AI Fallback Engine** that eliminates hallucinations through deterministic, session-isolated database context grounding.

---

## 📚 Documentation Quick Links

To explore specific modules in detail, refer to the dedicated documentation files:

- 🖥️ **[Frontend Documentation](frontend/README.md)** — UI portals, JavaScript controllers, HTML templates, Chart.js integrations.
- ⚙️ **[Backend Architecture Guide](backend/README.md)** — FastAPI routers, SQLAlchemy models, Pydantic schemas, and services.
- 🗄️ **[Database & Schema Reference](database/README.md)** — 25 SQL schemas, 18 executable migrations, views, triggers, and seed data.
- 🤖 **[AI Subsystem & Multi-Agent Guide](ai/README.md)** — Multi-provider failover, context grounding, prompt engineering.
- 🛠️ **[Maintenance Scripts Guide](scripts/README.md)** — Database provisioning, FAISS indexing, model downloaders.
- 🧪 **[Testing & QA Guide](tests/README.md)** — API functional pytest suites and AI agent verification harnesses.
- 📐 **[System Architecture](ARCHITECTURE.md)** — High-level system architecture and data flows.
- 🔌 **[REST API Design Specification](API_DESIGN.md)** — Detailed REST endpoint specifications.
- 🚀 **[System Setup Guide](SETUP.md)** — Step-by-step installation instructions.
- **[Deployment Guide](DEPLOYMENT.md)** — GitHub release checklist, persistent backend hosting, and Vercel frontend deployment.

---

## 🏛️ System Architecture

```
                                Users (Student / Teacher / Admin)
                                                │
                                                ▼
                             Frontend Web Portals (HTML5 / CSS3 / ES6 JS)
                                                │
                                                ▼
                                    FastAPI REST API Gateway
                                                │
                   ┌────────────────────────────┼────────────────────────────┐
                   │                            │                            │
                   ▼                            ▼                            ▼
            Authentication & RBAC         Business Logic          Live Database Context
             (JWT + Password Hashing)    (Services & Routers)      (Grounding Engine)
                                                │                            │
                                                ▼                            ▼
                                      ┌─────────────────────────────────────────┐
                                      │        AI Provider Fallback Manager     │
                                      └────────────────────┬────────────────────┘
                                                           │
                      ┌───────────────────┬────────────────┼───────────────────┐
                      │                   │                │                   │
                      ▼                   ▼                ▼                   ▼
               1. Groq Cloud       2. Google Gemini  3. Hugging Face     4. Local Ollama
               (Llama 3.3 70B)     (Gemini 2.0)      (Llama 3.1 8B)      (qwen2.5/llama3.2)
                      │                   │                │                   │
                      └───────────────────┴────────────────┼───────────────────┘
                                                           │ (If offline)
                                                           ▼
                                            5. Direct DB Rule Generator
                                                           │
                                                           ▼
                                            SQLite Relational Database
                                              (25 Tables & Migrations)
```

---

## 🏛️ Key Implemented Modules & Portals

### 1. 🎓 Student Portal (`frontend/Student_dashboard/*`)
- **Interactive Dashboard**: Real-time CGPA, completed credits, enrolled courses, upcoming classes, attendance metrics, and fee notices.
- **Academic Results & CGPA Analytics**: Semester-wise GPA progression, course grade points, percentage breakdowns, visual performance charts (Chart.js), and academic standing classification.
- **Attendance Tracking**: Course-wise attendance percentages, present/absent summaries, and eligibility warning flags (<75%).
- **Timetable & Schedule**: Dynamic weekly schedules with normalized time-slots, rooms, and instructor details.
- **Assignment Hub & Submissions**: Active assignments, due dates, submission portal, teacher feedback, and grading status.
- **Online Examination & Assessments**: Real-time online assessment portal with session control and proctoring hooks.
- **Financial & Fee Management**: Semester challan breakdowns, payment verification, transaction IDs, and outstanding dues tracking.
- **Digital Library & Notices**: Catalog search, book issue records, due dates, and campus circulars.
- **AI Academic Advisor**: Grounded conversational AI assistant for academic advice, timetable queries, attendance alerts, and fee status.

### 2. 👨‍🏫 Teacher Portal (`frontend/Teacher_dashboard/*`)
- **Teacher Dashboard**: Real-time summaries of assigned courses, total enrolled students, pending assignments to grade, and daily class schedules.
- **Course & Student Management**: Detailed rosters of enrolled students per section and course.
- **Class Schedule & Timetables**: Dynamic weekly teaching schedule with real-time room allocations and period timings.
- **Attendance Management System**: Session-wise student attendance marking (Present/Absent/Late/Excused) with auto-calculation of attendance rates.
- **Assignment Creator & Submissions Review**: Create assignments, set deadlines and maximum marks, inspect student submissions, and submit grades with teacher feedback.
- **Comprehensive Gradebook**: Sessional, midterm, final, and total mark entry with automatic grade calculation.
- **Assessments & Quizzes**: Creation and management of online assessments.
- **Teacher AI Academic Assistant**: Grounded AI assistant offering rapid queries on course enrollment, low-attendance warnings, student performance summaries, and teaching agendas.

### 3. 🛡️ Admin & AI Agentic Command Center (`frontend/Admin_dashboard/*`)
- **Institutional Governance**: Department management, faculty assignments, student admissions, course catalog configuration, and academic term scheduling.
- **Zero-Trust User Management**: Role management, secure credential provisioning, and activation states.
- **Audit & Security Logs**: Comprehensive, immutable audit logging tracking critical operations (logins, record edits, grade changes, permissions).
- **AI Watchdogs & Autonomous Monitoring**:
  - *Academic Integrity Watchdog*: Analyzes grade distributions, anomalies, and unauthorized grade alterations.
  - *Clerk Watchdog*: Audits administrative workflows, document processing, and data modification timestamps.
  - *Exam Monitoring Agent*: Real-time oversight of online and on-campus examination integrity.
  - *Financial Verification Agent*: Reconciles fee records, payment receipts, and balance discrepancies.
  - *Hostel, Transport, Library, Security & HR Agents*: Specialized agent dashboards for campus resource management.

### 4. 🤖 Multi-Provider AI Subsystem
- **Multi-Provider Fallback Architecture**:
  1. **Groq API** (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) — Ultra-low latency cloud inference.
  2. **Google Gemini API** (`gemini-2.0-flash`, `gemini-1.5-flash`) — Advanced reasoning and multi-turn context.
  3. **Hugging Face Inference API** (`meta-llama/Llama-3.1-8B-Instruct`) — Open-weights cloud provider.
  4. **Local Ollama** (`qwen2.5`, `llama3.2`, etc.) — Offline, privacy-first local inference.
  5. **Deterministic DB Rule-Based Fallback** — Guaranteed response delivery even when offline or during API rate limits.
- **Zero-Trust Context Grounding**: The system extracts real-time, authenticated database context per user session before prompting LLMs, preventing hallucinations.

---

## 💻 Technology Stack

| Layer | Technologies & Tools |
|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+), [Uvicorn](https://www.uvicorn.org/) |
| **Database & ORM** | [SQLite](https://www.sqlite.org/), [SQLAlchemy 2.0](https://www.sqlalchemy.org/), 15 SQL Migrations |
| **Authentication & Security** | Zero-Trust JWT (`python-jose[cryptography]`), Passlib / Bcrypt password hashing, RBAC Middleware |
| **AI & LLM Orchestration** | Multi-Provider Engine (Groq, Google Gemini, Hugging Face, Local Ollama), Dynamic Context Grounders |
| **Frontend UI/UX** | Responsive HTML5, CSS3 Glassmorphism, Vanilla JavaScript (ES6+), Chart.js |
| **Testing & Quality Assurance** | [pytest](https://pytest.org/), Automated API & Multi-Agent Verification Suites |

---

## 📂 Repository File & Directory Map

```
autonomous-campus-operating-system/
│
├── backend/                           # Backend Application Root
│   ├── README.md                      # Detailed backend guide & router catalog
│   └── backend/
│       ├── app/
│       │   ├── api/                   # REST API Routers (auth, student, teacher, admin, exam)
│       │   ├── core/                  # Security, JWT, DB engine, Application config
│       │   ├── models/                # 20 SQLAlchemy ORM models (Users, Students, Courses, etc.)
│       │   ├── schemas/               # Pydantic request/response validation schemas
│       │   ├── services/              # Business logic, AI context injectors, AI providers, migrations
│       │   └── main.py                # FastAPI Application entry point & startup hooks
│       ├── test_agent_suite.py        # Teacher & Student AI Agent verification test suite
│       └── test_teacher_ai.py         # Dedicated Teacher AI verification suite
│
├── frontend/                          # Multi-Portal Web Frontend
│   ├── README.md                      # Frontend architecture & page catalog
│   ├── landing_page/                  # University public landing page (index.html, style.css, app.js)
│   ├── login_page/                    # Role-specific login screens (student, teacher, admin)
│   ├── welcome/                       # Role-based onboarding & home gateways
│   ├── Student_dashboard/             # Student portal (Results, Attendance, Timetable, AI, Fees, etc.)
│   ├── Teacher_dashboard/             # Teacher portal (Dashboard, Gradebook, Schedule, Attendance, AI)
│   ├── Admin_dashboard/               # Admin command center & AI agent watchdog interfaces
│   ├── shared/                        # Shared UI components (topbars, token handlers)
│   └── assets/                        # Brand logos, icons, and background media
│
├── database/                          # Relational SQLite Database & Schemas
│   ├── README.md                      # Database documentation & ER diagrams
│   ├── university.db                  # Active SQLite database instance
│   ├── schema/                        # 25 Modular SQL schema definitions (00 to 24)
│   ├── migrations/                    # Executable schema/data migrations (v4 onward)
│   ├── seed/                          # Comprehensive realistic seed data SQL scripts
│   ├── triggers/                      # Automated GPA & audit SQL triggers
│   ├── views/                         # Pre-calculated analytical SQL views
│   └── backups/                       # Database backup snapshots
│
├── ai/                                # AI Subsystem & Vector Workflows
│   ├── README.md                      # AI subsystem & multi-provider architecture guide
│   ├── agents/                        # AI agent definitions and tool wrappers
│   ├── embeddings/                    # Vector embedding utilities
│   ├── models/                        # Local model configurations & metadata
│   ├── prompts/                       # Grounded system prompts & role templates
│   ├── rag/                           # Retrieval-Augmented Generation query pipelines
│   ├── vector_db/                     # Vector storage & index persistence (FAISS)
│   └── workflows/                     # Multi-agent coordination graphs
│
├── scripts/                           # System Automation & Maintenance Scripts
│   ├── README.md                      # Scripts guide & execution instructions
│   └── setup_database.py              # Atomic SQLite provisioning & optional seeding
│
├── tests/                             # Quality Assurance & Test Suites
│   ├── README.md                      # Test suite documentation & running instructions
│   ├── api/                           # Comprehensive API endpoint tests (pytest)
│   ├── integration/                   # End-to-end integration tests
│   └── unit/                          # Isolated unit tests
│
├── docs/                              # Project documentation, research logs & design assets
├── ARCHITECTURE.md                    # Detailed architectural specification
├── API_DESIGN.md                      # REST API endpoints design specification
├── SETUP.md                           # System installation & setup guide
├── CONTRIBUTING.md                    # Contribution guidelines
├── DEPLOYMENT.md                      # GitHub, backend hosting, and Vercel guide
├── requirements.txt                   # Canonical pinned runtime dependencies
├── requirements-dev.txt               # Test and browser automation dependencies
├── .env.example                       # Safe environment-variable template
├── CODE_OF_CONDUCT.md                 # Code of conduct
├── LICENSE                            # MIT License
└── README.MD                          # Master project documentation (this file)
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.12+**
- **Git**
- *(Optional for offline AI)* **Ollama** installed with models such as `qwen2.5:1.5b` or `llama3.2`.

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/hammadyounisabbasi/autonomous-campus-operating-system.git
cd autonomous-campus-operating-system

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the root `.env.example` to the ignored root `.env` file:
```bash
cp .env.example .env
```
Add your preferred AI API keys:
- `GROQ_API_KEY` (Get from [console.groq.com](https://console.groq.com/))
- `GEMINI_API_KEY` (Get from [Google AI Studio](https://aistudio.google.com/))
- `HUGGINGFACE_API_KEY` (Hugging Face User Access Token)
- `OLLAMA_BASE_URL` (Defaults to `http://127.0.0.1:11434`)

### 4. Initialize the Database
```bash
# From project root:
python scripts/setup_database.py
```

### 5. Run the Backend API
From the repository root:
```bash
uvicorn app.main:app --app-dir backend/backend --reload --host 127.0.0.1 --port 8000
```
- **API Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **ReDoc Interactive Docs**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/health`

### 6. Launch the Frontend
Open `frontend/landing_page/index.html` or `frontend/login_page/student-login.html` directly in your browser, or serve using Python HTTP Server:
```bash
# From repository root:
cd frontend
python -m http.server 3000
```
Visit:
- **Landing Page**: `http://127.0.0.1:3000/landing_page/index.html`
- **Student Login**: `http://127.0.0.1:3000/login_page/student-login.html`
- **Teacher Login**: `http://127.0.0.1:3000/login_page/teacher-login.html`
- **Admin Login**: `http://127.0.0.1:3000/login_page/admin-login.html`

---

## 🔐 Default Test Credentials

All seed accounts are pre-configured with the default password:
- **Default Password**: `UOH@2025`

| Role | Username / Identifier | Portal Link | Sample Access |
|---|---|---|---|
| **Student** | `hamza.ali24`, `ahmed.raza24`, `usman.khan24`, `bilal.raja24`, `zain.abidin24` | `frontend/login_page/student-login.html` | Results, CGPA, Attendance, Assignments, Timetable, AI Advisor |
| **Faculty (Teacher)** | `ahmad.malik@uoh.edu.pk`, `usman.ali@uoh.edu.pk`, `sara.khan@uoh.edu.pk` | `frontend/login_page/teacher-login.html` | Gradebook, Attendance Marking, Assignment Creator, AI Assistant |
| **Administrator** | `admin` | `frontend/login_page/admin-login.html` | Governance, User Management, AI Watchdogs, Audit Logs |

---

## 🧪 Testing & Quality Assurance

Run the automated test suites to verify API integrity and AI grounding:

```bash
# Run API endpoint functional tests (pytest)
python -m pytest tests/api/ -v

# Run AI Agent Multi-Provider Verification Suite
cd backend/backend
python test_agent_suite.py

# Run dedicated Teacher AI Verification Harness
python test_teacher_ai.py
```

---

## 👤 Author & Academic Affiliation

**Hammad Younis Abbasi**<br>
Bachelor of Science in Computer Science (BSCS)<br>
Department of Computer Science, **University of Haripur**<br>
Final Year Research Project

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
