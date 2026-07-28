# Setup Guide

## Project
**Autonomous Campus Operating System (ACOS)**

**Version:** 1.0

**Document Type:** Environment Setup & Installation Guide

---

# 1. Introduction

This document explains how to set up the development environment for the Autonomous Campus Operating System (ACOS). It covers the installation of required software, project dependencies, database initialization, AI model setup, and steps to run the application.

The project is designed to use a local development environment based on Python, FastAPI, SQLite, LangGraph, FAISS, and Ollama.

---

# 2. System Requirements

## Hardware Requirements

| Component | Minimum Requirement |
|-----------|---------------------|
| Processor | Intel Core i5 (8th Generation or newer) |
| RAM | 8 GB (16 GB Recommended) |
| Storage | 20 GB Free Space |
| Internet | Required for initial setup |

---

## Operating System

Supported operating systems:

- Windows 10 / 11
- Ubuntu 22.04+
- macOS 13+

---

# 3. Required Software

Install the following software before running the project.

| Software | Purpose |
|----------|---------|
| Git | Version Control |
| Python 3.12+ | Backend Development |
| Visual Studio Code | Code Editor |
| SQLite | Database |
| Ollama | Local LLM Runtime |

---

# 4. Clone the Repository

Clone the project from GitHub.

```bash
git clone https://github.com/your-username/autonomous-campus-operating-system.git

cd autonomous-campus-operating-system
```

Replace the repository URL with your own GitHub repository.

---

# 5. Create Virtual Environment

Windows

```bash
python -m venv .venv
```

Activate

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

# 6. Install Dependencies

Install Python packages.

```bash
pip install -r requirements.txt
```

Verify installation

```bash
pip list
```

---

# 7. Install Ollama

Download and install Ollama from:

https://ollama.com/download

Verify installation.

```bash
ollama --version
```

---

# 8. Download AI Model

Example:

```bash
ollama pull llama3.1:8b
```

Verify available models.

```bash
ollama list
```

---

# 9. Configure Environment Variables

Create a file named:

```
.env
```

Example configuration:

```env
DATABASE_URL=database/campus.db

OLLAMA_MODEL=llama3.1:8b

FAISS_INDEX_PATH=backend/vectorstore/faiss_index

SECRET_KEY=your-secret-key

DEBUG=True
```

Never commit the `.env` file to GitHub.

---

# 10. Database Initialization

SQLite will be used as the relational database.

Create the database.

```bash
python scripts/setup_database.py
```

The script will:

- Create the SQLite database
- Create all tables
- Apply schema
- Prepare the project for development

Database location:

```
database/campus.db
```

---

# 11. FAISS Initialization

Initialize the vector database.

```bash
python scripts/initialize_faiss.py
```

This process will:

- Create the FAISS index
- Prepare vector storage
- Initialize semantic search

Output directory:

```
backend/vectorstore/faiss_index/
```

---

# 12. Download Embeddings

If required, download the embedding model.

Example:

```python
sentence-transformers/all-MiniLM-L6-v2
```

This model converts documents into embeddings for semantic search.

---

# 13. Run FastAPI

Start the backend server.

```bash
uvicorn backend.app.main:app --reload
```

Default URL

```
http://127.0.0.1:8000
```

API documentation

```
http://127.0.0.1:8000/docs
```

Interactive ReDoc

```
http://127.0.0.1:8000/redoc
```

---

# 14. Run Frontend

Open:

```
frontend/index.html
```

or run a local web server.

Example:

```bash
python -m http.server
```

---

# 15. Verify Installation

The setup is successful if:

- Python is installed
- Git is installed
- Ollama is running
- SQLite database is created
- FAISS index is initialized
- FastAPI starts successfully
- API documentation is accessible
- Frontend loads correctly

---

# 16. Project Structure

```
frontend/

backend/

ai/

database/

scripts/

tests/

docs/
```

---

# 17. Troubleshooting

## Python Not Found

Verify installation.

```bash
python --version
```

---

## Virtual Environment Not Activated

Windows

```bash
.venv\Scripts\activate
```

---

## Ollama Not Running

Start Ollama.

```bash
ollama serve
```

---

## Missing Python Packages

Install dependencies again.

```bash
pip install -r requirements.txt
```

---

## Database Missing

Run:

```bash
python scripts/setup_database.py
```

---

## FAISS Index Missing

Run:

```bash
python scripts/initialize_faiss.py
```

---

# 18. Development Workflow

```
Clone Repository

↓

Create Virtual Environment

↓

Install Dependencies

↓

Configure Environment Variables

↓

Install Ollama

↓

Download AI Model

↓

Initialize Database

↓

Initialize FAISS

↓

Run FastAPI

↓

Open Frontend

↓

Start Development
```

---

# 19. Future Setup

Later development phases will include:

- PostgreSQL support
- Docker deployment
- CI/CD pipelines
- Automated database migrations
- Cloud deployment
- Production configuration

---

# 20. Conclusion

This setup guide provides a standardized process for preparing the development environment for the Autonomous Campus Operating System. Following these steps ensures that all developers use a consistent configuration, simplifying collaboration and reducing environment-related issues during development.