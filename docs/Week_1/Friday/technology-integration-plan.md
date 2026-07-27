# Technology Integration Plan

## Project
**Autonomous Campus Operating System (ACOS)**

**Week:** 1 - Friday  
**Version:** 1.0

---

# 1. Introduction

The Autonomous Campus Operating System (ACOS) is built using multiple technologies that work together to provide a secure, intelligent, and autonomous campus management system.

Each technology has a specific responsibility. Together, they support AI agents, database operations, document processing, semantic search, and user interaction.

---

# 2. Technology Stack

| Technology | Purpose |
|------------|---------|
| Frontend | Frontend User Interface |
| FastAPI | Backend API Framework |
| LangGraph | Multi-Agent Orchestration |
| Ollama | Local Large Language Model |
| SQLite | Relational Database |
| FAISS | Vector Database |
| OpenCV | Image Processing |
| PyPDF2 | PDF Text Extraction |
| SQLAlchemy | Database ORM |
| Python | Backend Programming Language |

---

# 3. Technology Integration

## 3.1 Frontend → FastAPI

Frontend is responsible for displaying the user interface.

When a user performs an action, such as logging in, submitting a form, or asking an AI question, Frontend sends an HTTP request to the FastAPI backend.

### Workflow

```
User

↓

Frontend Frontend

↓

HTTP Request

↓

FastAPI
```

---

## 3.2 FastAPI → SQLite

FastAPI manages all communication with the relational database.

It performs:

- Insert records
- Update records
- Delete records
- Retrieve records

### Workflow

```
FastAPI

↓

SQLAlchemy

↓

SQLite Database
```

---

## 3.3 FastAPI → LangGraph

When a request requires AI reasoning instead of simple database operations, FastAPI sends the request to LangGraph.

LangGraph determines which AI agent should handle the request.

Example:

Student asks:

> "Why is my fee still unpaid?"

LangGraph selects the **Finance Verification Agent**.

### Workflow

```
FastAPI

↓

LangGraph

↓

Selected AI Agent
```

---

## 3.4 LangGraph → Ollama

LangGraph communicates with the local Large Language Model through Ollama.

The selected AI agent sends a prompt to Ollama.

Ollama generates the response and returns it to LangGraph.

### Workflow

```
LangGraph

↓

Ollama

↓

Llama Model

↓

AI Response
```

---

## 3.5 Document Processing using PyPDF2

Whenever a PDF document is uploaded, PyPDF2 extracts the text.

Examples:

- Admission Forms
- Result Sheets
- Research Papers
- Official Notices

### Workflow

```
Upload PDF

↓

PyPDF2

↓

Extract Text

↓

Store in Database
```

---

## 3.6 Image Processing using OpenCV

OpenCV processes uploaded images.

Examples:

- Student ID verification
- Face detection
- Exam monitoring
- Image preprocessing

### Workflow

```
Upload Image

↓

OpenCV

↓

Image Analysis

↓

AI Agent
```

---

## 3.7 FAISS Vector Database

FAISS stores vector embeddings instead of structured records.

Whenever a document is uploaded:

1. Text is extracted.
2. The text is converted into embeddings.
3. Embeddings are stored in FAISS.
4. During a search, FAISS returns the most relevant documents.

### Workflow

```
Upload Document

↓

Extract Text

↓

Generate Embeddings

↓

Store in FAISS

↓

Similarity Search
```

---

# 4. Complete Technology Integration Diagram

```
                               USER
                                 │
                                 ▼
                        Frontend Frontend
                                 │
                       HTTP Request/Response
                                 │
                                 ▼
                          FastAPI Backend
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
  SQLite Database          LangGraph Engine         File Upload
        │                        │                        │
        │               ┌────────┼────────┐               │
        │               │        │        │               │
        ▼               ▼        ▼        ▼               ▼
 Student Data       AI Agents  Ollama   FAISS         OpenCV
        │               │        │        │               │
        │               │        │        │               │
        │               ▼        ▼        ▼               ▼
        │          AI Reasoning  LLM   Vector Search  Image Analysis
        │                        │        │
        └────────────────────────┼────────┘
                                 │
                                 ▼
                         Final AI Response
                                 │
                                 ▼
                        Frontend Frontend
```

---

# 5. Complete Request Flow

The following steps describe how the complete system works.

### Step 1

The user submits a request through the Frontend frontend.

↓

### Step 2

Frontend sends the request to FastAPI.

↓

### Step 3

FastAPI determines the request type.

- Database request
- AI request
- File upload

↓

### Step 4

If it is a database request, FastAPI communicates with SQLite.

↓

### Step 5

If AI reasoning is required, FastAPI forwards the request to LangGraph.

↓

### Step 6

LangGraph selects the appropriate AI agent.

↓

### Step 7

The AI agent interacts with:

- Ollama (LLM)
- FAISS (knowledge retrieval)
- SQLite (structured data)
- OpenCV (image analysis)
- PyPDF2 (document extraction)

↓

### Step 8

The AI agent generates the final response.

↓

### Step 9

FastAPI returns the response to Frontend.

↓

### Step 10

The user receives the final result.

---

# 6. Benefits of This Architecture

- Modular architecture
- Scalable design
- Local AI using Ollama
- Fast API communication
- Secure database operations
- Semantic search using FAISS
- Intelligent multi-agent orchestration
- Easy future expansion

---

# 7. Conclusion

The Autonomous Campus Operating System integrates Frontend, FastAPI, LangGraph, Ollama, SQLite, FAISS, OpenCV, and PyPDF2 into a unified architecture. FastAPI acts as the central communication layer, LangGraph coordinates AI agents, SQLite manages structured data, FAISS enables semantic retrieval, OpenCV processes images, and PyPDF2 extracts text from documents. This integration provides a scalable foundation for building an intelligent, secure, and autonomous campus management system.