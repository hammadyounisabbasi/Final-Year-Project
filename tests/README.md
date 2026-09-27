# ACOS Test Suite & Quality Assurance

Install `requirements-dev.txt` from the repository root before running tests. API and browser suites can mutate test data; point `DATABASE_URL` at a disposable SQLite database rather than a production file.

> **Automated Test Suites, API Functional Tests & Multi-Agent AI Verification**

---

## 🧪 Overview

The **Autonomous Campus Operating System (ACOS)** incorporates a multi-tiered test suite to guarantee high reliability, data integrity, Zero-Trust access isolation, and deterministic AI grounding.

---

## 📂 Test Suite Structure

```
tests/
├── README.md                          # Testing documentation (this file)
│
├── api/                               # API Endpoint Functional Tests
│   ├── test_student_results.py        # Student results, GPA/CGPA calculations & chart data
│   ├── test_multi_semester_results.py # Multi-semester progress & cumulative credit audit
│   ├── test_multiple_students.py      # Multi-student authentication & profile isolation
│   ├── test_student_courses.py        # Course enrollment & credit hours verification
│   ├── test_student_profile.py        # Student profile metadata & department mapping
│   └── test_danish_malik_results.py   # Cohort transcript & grading accuracy verification
│
├── integration/                       # End-to-end multi-service integration tests
└── unit/                              # Isolated unit tests for utility functions & models
```

### Dedicated AI Agent Verification Suites (located in `backend/backend/`):
- [`test_agent_suite.py`](../backend/backend/test_agent_suite.py): Comprehensive verification suite testing dynamic greetings, multi-turn chat, context grounding, and multi-provider failover for Teacher and Student AI agents.
- [`test_teacher_ai.py`](../backend/backend/test_teacher_ai.py): Focused test harness for Faculty AI Assistant workflows.

---

## 🚀 Running the Tests

### 1. Run API Tests with `pytest`
Make sure your virtual environment is active and dependencies are installed:
```bash
# Run all API tests with verbose output
pytest tests/api/ -v

# Run a specific test module
pytest tests/api/test_student_results.py -v
pytest tests/api/test_multiple_students.py -v
```

### 2. Run API Tests Directly with Python
You can also execute individual test files directly:
```bash
python tests/api/test_student_results.py
python tests/api/test_multi_semester_results.py
python tests/api/test_multiple_students.py
```

### 3. Run AI Agent Verification Suites
Ensure the FastAPI backend is running on `http://127.0.0.1:8000`:
```bash
# In a separate terminal with backend active:
cd backend/backend
python test_agent_suite.py
python test_teacher_ai.py
```

---

## 📋 Key Test Scenarios Covered

| Test File | Verification Scope | Expected Outcome |
|---|---|---|
| `test_student_results.py` | Semester GPA, Cumulative CGPA, total grade points, course breakdown, Chart.js payload | Verified calculated CGPA, accurate letter grades, and correct credit summation. |
| `test_multiple_students.py` | Role-Based Access Control and data isolation between multiple student accounts | Each student only receives their own data; zero cross-account leakage. |
| `test_student_courses.py` | Enrolled course lists, department relationships, course codes | Valid course arrays and assigned teachers matching database records. |
| `test_agent_suite.py` | AI Provider fallback (Groq → Gemini → HF → Ollama → DB), dynamic greeting, context grounding | Grounded, accurate responses using live database context without hallucination. |

---

## 🔐 Test Accounts & Credentials

Default seed credentials for testing:
- **Default Password**: `UOH@2025`
- **Sample Students**: `hamza.ali24`, `ahmed.raza24`, `usman.khan24`, `bilal.raja24`, `zain.abidin24`
- **Sample Faculty**: `ahmad.malik@uoh.edu.pk`, `usman.ali@uoh.edu.pk`, `sara.khan@uoh.edu.pk`
- **Sample Admin**: `admin`
