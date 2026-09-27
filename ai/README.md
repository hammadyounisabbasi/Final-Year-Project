# ACOS AI Subsystem & Multi-Agent Architecture

> **Intelligent, Zero-Trust Context-Grounded Multi-Agent AI System for Academic & Campus Operations**

---

## 📖 Overview

The **Autonomous Campus Operating System (ACOS)** AI subsystem is engineered to provide secure, autonomous, and context-aware intelligence across all campus domains. Unlike standard generative chatbots that may produce hallucinations or leak cross-tenant information, the ACOS AI subsystem operates under **Zero-Trust Principles** and **Session-Isolated Context Grounding**:

1. **Zero-Trust Data Isolation**: Every AI request is strictly bound to the authenticated user's session token and database scope (RBAC). A student can only access their own attendance, fees, and marks; a teacher can only query courses and students they teach.
2. **Context-Grounded Inference**: Before calling any Large Language Model (LLM), the system deterministically queries the SQLite database to build an accurate, real-time snapshot of user context (attendance %, GPA/CGPA, class schedules, dues, pending assignments).
3. **Multi-Provider Failover Architecture**: Automatic cascading fallback across multiple cloud and on-premise AI inference providers to ensure 100% uptime and resilience.

---

## ⚡ Multi-Provider AI Architecture

The system features an autonomous `AIProviderManager` (`backend/backend/app/services/ai_providers.py`) that dynamically manages inference providers in priority sequence:

```
                  User Chat / Query Request
                             │
                             ▼
               Session & RBAC Verification (JWT)
                             │
                             ▼
         Deterministic DB Context Grounding Engine
      (student_ai_context.py / teacher_ai_context.py)
                             │
                             ▼
               ┌───────────────────────────┐
               │    AI Provider Manager    │
               └─────────────┬─────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
     1. Groq Cloud    2. Google Gemini  3. Hugging Face
     (Llama 3.3 70B)  (Gemini 2.0 Flash) (Llama 3.1 8B)
            │                │                │
            └────────────────┼────────────────┘
                             │ (If cloud providers offline / rate-limited)
                             ▼
                      4. Local Ollama
                   (qwen2.5 / llama3.2)
                             │
                             │ (If offline / unconfigured)
                             ▼
              5. Direct Database Rule-Based
                     Fallback Generator
```

### Supported AI Providers

| Provider | Priority | Default Model | Configuration Variables | Characteristics |
|---|---|---|---|---|
| **Groq** | 1 | `llama-3.3-70b-versatile` | `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL` | High-speed, ultra-low latency cloud inference |
| **Google Gemini** | 2 | `gemini-2.0-flash` | `GEMINI_API_KEY`, `GEMINI_MODEL` | Multi-turn reasoning and rich instruction following |
| **Hugging Face** | 3 | `meta-llama/Llama-3.1-8B-Instruct` | `HUGGINGFACE_API_KEY`, `HUGGINGFACE_MODEL` | Open-source foundation models via router / inference API |
| **Ollama** | 4 | `qwen2.5:1.5b` / `llama3.2` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | 100% local, on-premise, offline-capable inference |
| **Direct DB Fallback**| 5 | N/A (Rule Engine) | Automatic | Deterministic template generation from live SQL context |

---

## 🧠 Implemented AI Agents & Modules

### 1. Student Academic Advisor Agent
- **Service Files**: `backend/backend/app/services/student_ai_assistant.py`, `student_ai_context.py`
- **Endpoints**: `POST /student/ai/chat`, `GET /student/ai/greeting`, `GET /student/ai/providers`
- **Capabilities**:
  - Summarizes current CGPA, completed credits, and semester-wise GPA progression.
  - Monitors course attendance and issues warning alerts for subjects below 75%.
  - Details unpaid fee balances, due dates, and challan numbers.
  - Lists upcoming class sessions, timetable room numbers, and instructor details.
  - Highlights pending assignments and imminent submission deadlines.

### 2. Teacher Academic Assistant Agent
- **Service Files**: `backend/backend/app/services/teacher_ai_assistant.py`, `teacher_ai_context.py`
- **Endpoints**: `POST /teacher/ai/chat`, `GET /teacher/ai/greeting`, `GET /teacher/ai/providers`
- **Capabilities**:
  - Delivers dynamic, contextual greetings tailored to the teacher's profile and schedule.
  - Summarizes courses taught, section breakdown, and total registered student counts.
  - Identifies at-risk students with low attendance or poor academic scores.
  - Outlines the instructor's daily teaching timetable and upcoming lecture venues.
  - Tracks assignment submission progress and ungraded student submissions.

### 3. Administrative Watchdogs & Specialized Agents
- **Academic Integrity Watchdog**: Identifies abnormal grade distributions, retroactive grade changes, and unauthorized transcript modifications.
- **Clerk Watchdog**: Monitors administrative data alterations, timestamps, and clerk permission boundaries.
- **Exam Proctoring & Monitoring Agent**: Audits online assessment events and flags anomalous session activities.
- **Finance & Audit Agent**: Cross-verifies fee challan records against bank transaction logs.
- **Hostel, Transport, Library, Security & HR Agents**: Dedicated agent interfaces for campus utility oversight.

---

## 📁 AI Subsystem Directory Structure

```
ai/
├── README.md              # AI subsystem documentation (this file)
├── agents/                # Agent definitions, tools, and execution strategies
├── embeddings/            # Vector embeddings and tokenizer utilities
├── models/                # Local model configurations and metadata
├── prompts/               # System prompts, role personas, and formatting instructions
├── rag/                   # Retrieval-Augmented Generation indexing and query pipelines
├── vector_db/             # Vector database storage and index persistence (FAISS)
└── workflows/             # Multi-agent coordination graphs and orchestration flows
```

*Note: Core production AI runtime services are integrated within `backend/backend/app/services/` for unified, high-performance execution with the FastAPI application.*

---

## ⚙️ Configuration & Environment Setup

Set your AI provider keys in `.env` (located in `backend/backend/.env` or project root):

```env
# 1. Groq (Recommended for fast cloud testing)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# 2. Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# 3. Hugging Face
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct

# 4. Local Ollama (Offline Privacy-First)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

---

## 🧪 Testing the AI Agents

Automated test scripts verify multi-provider routing, dynamic greetings, context grounding, and isolation:

```bash
# Navigate to backend directory
cd backend/backend

# Run complete Agent Verification Suite (Student & Teacher Agents)
python test_agent_suite.py

# Run dedicated Teacher AI test
python test_teacher_ai.py
```
