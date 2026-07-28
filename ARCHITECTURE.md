# System Architecture

## Project
**Autonomous Campus Operating System (ACOS)**

**Version:** 1.0

**Document Type:** System Architecture

---

# 1. Introduction

The Autonomous Campus Operating System (ACOS) is a research-based intelligent campus management platform that integrates Agentic Artificial Intelligence, Multi-Agent Systems, Retrieval-Augmented Generation (RAG), and Zero-Trust Security principles.

Unlike traditional Campus Management Systems (CMS), ACOS is designed to monitor, verify, analyze, and automate campus operations through specialized AI agents coordinated by LangGraph.

This document describes the overall system architecture, software components, communication flow, and technology integration.

---

# 2. Architecture Goals

The architecture is designed to achieve the following objectives:

- Modular and scalable system design
- Secure communication using Zero-Trust principles
- Intelligent decision-making through AI agents
- Separation of frontend, backend, AI, and database layers
- Easy integration of future AI agents and services
- Support for local Large Language Models using Ollama

---

# 3. High-Level Architecture

```
                              Users
                                │
                                ▼
                   Frontend (HTML/CSS/JavaScript)
                                │
                                ▼
                     FastAPI REST API Gateway
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
 Authentication          LangGraph Engine          System Services
 Authorization          (Agent Orchestrator)      Logging & Monitoring
                                │
                                ▼
                ┌──────────────────────────────────┐
                │      AI Agent Layer              │
                ├──────────────────────────────────┤
                │ Academic Advisor Agent           │
                │ Sessional Marks Agent            │
                │ Exam Monitoring Agent            │
                │ Result Verification Agent        │
                │ Admission Agent                  │
                │ Financial Verification Agent     │
                │ Library Agent                    │
                │ Research Agent                   │
                │ Hostel Agent                     │
                │ Security Agent                   │
                │ IT Helpdesk Agent                │
                │ Administration Agent             │
                └──────────────────────────────────┘
                                │
                ┌───────────────┼────────────────┐
                ▼               ▼                ▼
          SQLite Database   FAISS Vector DB   Ollama LLM
```

---

# 4. System Layers

The ACOS architecture is organized into five logical layers.

---

## Layer 1 – Presentation Layer

### Technology

- HTML5
- CSS3
- JavaScript

### Responsibilities

- User authentication
- Dashboard interface
- Student portal
- Administrative portal
- AI agent monitoring
- Reports and analytics
- User interaction

---

## Layer 2 – API Gateway Layer

### Technology

- FastAPI

### Responsibilities

- REST API endpoints
- Authentication
- Authorization
- Request validation
- Rate limiting
- Logging
- Error handling
- Communication with AI agents

---

## Layer 3 – AI Agent Layer

### Technology

- LangGraph

### Responsibilities

- Coordinate AI agents
- Execute workflows
- Pass messages between agents
- Trigger automated actions
- Process user requests
- Manage decision-making

---

## Layer 4 – Data Layer

### Technologies

- SQLite
- FAISS

### SQLite Stores

- Students
- Courses
- Faculty
- Grades
- Fee records
- Admissions
- Documents
- Audit logs
- Security events

### FAISS Stores

- Research paper embeddings
- Library embeddings
- University policies
- Student handbook
- Academic regulations

---

## Layer 5 – AI Model Layer

### Technology

- Ollama

### Responsibilities

- Natural language understanding
- Report generation
- Question answering
- AI recommendations
- Summarization
- Retrieval-Augmented Generation (RAG)

---

# 5. AI Agent Architecture

The system consists of thirteen specialized AI agents.

| Agent | Responsibility |
|--------|----------------|
| Sessional Marks Agent | Verify sessional marks before storage |
| Exam Monitoring Agent | Detect cheating and monitor online exams |
| Result Verification Agent | Verify result integrity and prevent tampering |
| Academic Advisor Agent | Analyze academic performance |
| Admission Agent | Process admission applications |
| Financial Verification Agent | Verify fee payments and reconciliation |
| Research Agent | Manage research documents and ORIC records |
| Library Agent | Intelligent library search |
| Hostel & Transport Agent | Manage accommodation and transport |
| Security Agent | Monitor security threats |
| IT Helpdesk Agent | Handle technical support requests |
| Administration Agent | Manage HR and administrative workflows |
| Student Portal Agent | Assist students with academic services |

Each agent performs a specialized task while collaborating through LangGraph workflows.

---

# 6. Agent Communication Flow

```
User Request

      │

      ▼

FastAPI API

      │

      ▼

LangGraph Controller

      │

      ▼

Required AI Agent

      │

      ▼

Database / FAISS / Ollama

      │

      ▼

Response Generated

      │

      ▼

Frontend Dashboard
```

---

# 7. Data Flow

```
User

↓

Frontend

↓

FastAPI

↓

Authentication

↓

LangGraph

↓

Selected AI Agent

↓

SQLite / FAISS / Ollama

↓

Processed Result

↓

API Response

↓

Frontend Dashboard
```

---

# 8. Security Architecture

The project follows a Zero-Trust security model.

### Security Principles

- Verify every request
- Role-Based Access Control (RBAC)
- Secure authentication
- Audit logging
- Data integrity verification
- Cryptographic hash validation
- Secure API communication

---

# 9. Database Architecture

The relational database stores structured information.

Main entities include:

- Users
- Students
- Faculty
- Courses
- Enrollments
- Grades
- Fee Records
- Documents
- Admissions
- Research Papers
- Audit Logs
- Security Events

The database is normalized to reduce redundancy and maintain data integrity.

---

# 10. Vector Database Architecture

FAISS provides semantic search capabilities.

Stored embeddings include:

- Research papers
- Library books
- Academic policies
- Student regulations
- Official notices

Workflow:

```
Document

↓

Text Extraction

↓

Embedding Model

↓

Vector Generation

↓

FAISS Index

↓

Semantic Search
```

---

# 11. Technology Integration

| Component | Technology |
|-----------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI |
| AI Workflow | LangGraph |
| LLM | Ollama |
| Database | SQLite |
| Vector Database | FAISS |
| Computer Vision | OpenCV |
| PDF Processing | PyPDF2 |

---

# 12. Project Directory Overview

```
frontend/
backend/
ai/
database/
docs/
scripts/
tests/
```

Each directory is responsible for a specific layer of the system to ensure modularity and maintainability.

---

# 13. Scalability

The architecture supports future enhancements, including:

- PostgreSQL or MySQL integration
- Cloud deployment
- Additional AI agents
- Mobile applications
- Real-time notifications
- Multi-campus support
- Advanced analytics

---

# 14. Design Principles

The architecture follows these software engineering principles:

- Separation of Concerns
- Modularity
- Scalability
- Maintainability
- Security by Design
- Reusability
- Loose Coupling
- High Cohesion

---

# 15. Conclusion

The Autonomous Campus Operating System is designed as a modular, intelligent, and secure platform that combines modern web technologies with Agentic AI and Zero-Trust Architecture. By separating the application into presentation, API, AI, data, and model layers, the system remains scalable, maintainable, and ready for future enhancements. The architecture establishes a solid foundation for implementing autonomous campus services while supporting ongoing research in intelligent educational systems.
