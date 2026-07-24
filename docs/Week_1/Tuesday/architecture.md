# System Architecture

## Introduction

The Autonomous Campus Operating System (ACOS) follows a layered architecture to provide scalability, modularity, security, and maintainability. The system integrates a web-based frontend, an API Gateway, a LangGraph-based multi-agent orchestration layer, and a centralized data layer. This architecture enables autonomous decision-making while maintaining Zero-Trust security principles.

---

# High-Level Architecture

Presentation Layer
        │
        ▼
API Gateway (FastAPI)
        │
        ▼
LangGraph Supervisor Agent
        │
        ▼
13 Specialized AI Agents
        │
        ▼
Shared Security Layer
        │
        ▼
Data Layer

---

## Layer 1 – Presentation Layer

The presentation layer provides interfaces for different stakeholders.

Components:

- Student Portal
- Teacher Portal
- Parent Portal
- Clerk Portal
- Administration Portal
- AI Chat Assistant
- Mobile Interface

Responsibilities:

- User interaction
- Display information
- Submit requests
- Receive responses

---

## Layer 2 – API Gateway

The API Gateway serves as the single entry point.

Responsibilities:

- Authentication
- Authorization
- Request Validation
- Request Routing
- Rate Limiting
- Logging
- Error Handling

Technology:

FastAPI

---

## Layer 3 – Multi-Agent Layer

The LangGraph Supervisor Agent coordinates all specialized agents.

Agents:

1. Sessional Accountability Agent
2. Exam Evaluation Agent
3. Clerk Watchdog Agent
4. Online Examination Integrity Agent
5. Academic & Student Portal Agent
6. Admissions & Query Handling Agent
7. Financial & Fee Verification Agent
8. ORIC & Research Management Agent
9. Library & Knowledge Management Agent
10. Hostel & Transport Management Agent
11. Campus Security & Asset Tracking Agent
12. IT Helpdesk Maintenance Agent
13. Core Administration & HR Agent

---

## Shared Security Layer

All agents operate under Zero-Trust Architecture.

Security mechanisms include:

- Authentication
- Authorization
- Cryptographic Verification
- Integrity Checking
- Immutable Audit Logging

---

## Data Layer

The data layer stores structured and unstructured information.

Components:

- SQLite Database
- FAISS Vector Store
- Document Repository
- Audit Logs
- Knowledge Base

---

## Conclusion

This layered architecture separates responsibilities between user interfaces, request processing, AI agent orchestration, security, and data storage. Such separation improves scalability, maintainability, and supports future expansion of ACOS.