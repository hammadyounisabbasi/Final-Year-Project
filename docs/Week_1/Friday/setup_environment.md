# Development Environment Setup Guide

## Project
**Autonomous Campus Operating System (ACOS)**

**Week:** 1 - Friday  
**Version:** 1.0

---

# 1. Purpose

This document explains how to configure the development environment for the Autonomous Campus Operating System (ACOS). It defines the required software, project configuration, environment variables, database initialization, AI model setup, and vector database initialization.

---

# 2. Development Environment

The project will be developed using the following tools.

| Component | Technology |
|-----------|------------|
| Operating System | Windows 11 |
| Programming Language | Python 3.12+ |
| IDE | Visual Studio Code |
| Backend | FastAPI |
| AI Framework | LangGraph |
| Local LLM | Ollama |
| Database | SQLite |
| Vector Database | FAISS |
| Version Control | Git & GitHub |

---

# 3. Project Folder Structure

```
Autonomous-Campus-Operating-System/

│
├── backend/
│   ├── database/
│   │   ├── campus.db
│   │   └── schema.sql
│   │
│   ├── agents/
│   ├── api/
│   ├── vectorstore/
│   ├── uploads/
│   └── main.py
│
├── frontend/
│
├── docs/
│
├── .env
├── requirements.txt
└── README.md
```

---

# 4. Environment Variables (.env)

The project uses a `.env` file to store configuration values.

Example:

```env
# Database
DATABASE_URL=sqlite:///backend/database/campus.db

# Ollama
OLLAMA_MODEL=llama3

# Vector Database
FAISS_INDEX_PATH=backend/vectorstore/faiss_index

# Upload Folder
UPLOAD_PATH=backend/uploads

# Application
APP_ENV=development
DEBUG=True
```

These values can be changed without modifying the application source code.

---

# 5. Ollama Model Setup

The project uses Ollama to run a local Large Language Model.

### Selected Model

```
llama3
```

### Installation Steps

1. Install Ollama.
2. Start the Ollama service.
3. Download the model:

```
ollama pull llama3
```

4. Verify installation:

```
ollama list
```

The downloaded model will be used by LangGraph agents during AI processing.

---

# 6. SQLite Database Initialization

Before running the application, initialize the database.

Database file:

```
backend/database/campus.db
```

Schema file:

```
backend/database/schema.sql
```

Initialization process:

1. Create the SQLite database.
2. Execute `schema.sql`.
3. Verify that all tables are created successfully.

---

# 7. FAISS Index Initialization

The vector database must be initialized before semantic search can be used.

Initialization process:

1. Create the FAISS index folder.
2. Load the embedding model.
3. Generate embeddings for uploaded documents.
4. Store vectors in the FAISS index.
5. Save the index for future searches.

Directory:

```
backend/vectorstore/faiss_index/
```

Files:

```
index.faiss
index.pkl
```

---

# 8. File Upload Configuration

Uploaded files are stored in:

```
backend/uploads/
```

Supported file types include:

- PDF
- PNG
- JPG
- JPEG

These files are processed using:

- PyPDF2 (PDF documents)
- OpenCV (Images)

---

# 9. Development Workflow

The environment setup follows these steps:

```
Install Python

↓

Install Project Dependencies

↓

Configure .env

↓

Initialize SQLite Database

↓

Install Ollama Model

↓

Initialize FAISS Index

↓

Run FastAPI Server

↓

Open React Frontend
```

---

# 10. Configuration Summary

| Component | Status |
|-----------|--------|
| Python | Installed |
| VS Code | Installed |
| SQLite | Configured |
| FastAPI | Ready |
| LangGraph | Ready |
| Ollama | Ready |
| FAISS | Ready |
| Git | Ready |

---

# 11. Conclusion

The development environment provides a consistent configuration for all project components. Using environment variables, local AI models, SQLite, and FAISS ensures that the Autonomous Campus Operating System can be developed, tested, and maintained efficiently. This setup also simplifies future deployment by separating configuration from application code.