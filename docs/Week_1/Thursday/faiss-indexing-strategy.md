# FAISS Indexing Strategy
## Autonomous Campus Operating System (ACOS)

**Version:** 1.0  
**Phase:** Week 1 – Thursday  
**Module:** Vector Database Design  

---

# 1. Introduction

The Autonomous Campus Operating System (ACOS) uses Retrieval-Augmented Generation (RAG) to provide intelligent responses from university knowledge sources. Since Large Language Models (LLMs) do not retain organization-specific knowledge, the system employs a vector database using Facebook AI Similarity Search (FAISS) to retrieve relevant information efficiently.

FAISS enables semantic search by storing vector embeddings of documents instead of relying on traditional keyword-based searching.

---

# 2. Purpose of FAISS

FAISS is used to:

- Store vector embeddings of university documents.
- Perform fast similarity searches.
- Retrieve relevant information for AI agents.
- Support Retrieval-Augmented Generation (RAG).
- Improve the accuracy of AI-generated responses.

---

# 3. Difference Between SQLite and FAISS

| SQLite | FAISS |
|---------|--------|
| Stores structured data | Stores vector embeddings |
| Uses SQL queries | Uses similarity search |
| Best for transactional data | Best for semantic search |
| Stores metadata | Stores numerical vectors |
| Supports CRUD operations | Supports nearest-neighbor search |

SQLite and FAISS work together within the system. SQLite stores structured information and metadata, while FAISS stores vector representations of textual content for efficient semantic retrieval.

---

# 4. Embedding Model

The system will use the following embedding model:

**Model Name**

```
sentence-transformers/all-MiniLM-L6-v2
```

### Why this model?

- Lightweight
- Fast inference
- High-quality sentence embeddings
- Produces 384-dimensional vectors
- Compatible with FAISS
- Open-source

---

# 5. Data Flow

The document indexing workflow is illustrated below.

```
University Document
        │
        ▼
 Text Extraction
        │
        ▼
 Text Chunking
        │
        ▼
 Embedding Generation
        │
        ▼
 384-Dimensional Vector
        │
        ▼
    FAISS Index
        │
        ▼
  Similarity Search
        │
        ▼
 Retrieved Context
        │
        ▼
 Large Language Model
```

---

# 6. Document Indexing Process

When a new document is uploaded, the system follows these steps:

1. Receive the uploaded document.
2. Extract the textual content.
3. Divide the content into smaller chunks.
4. Generate embeddings for each chunk.
5. Store document metadata in SQLite.
6. Store vector embeddings in the FAISS index.
7. Save the updated FAISS index.

---

# 7. Query Processing Workflow

When a user asks a question, the system performs the following operations:

1. Receive the user's query.
2. Convert the query into an embedding.
3. Search the FAISS index.
4. Retrieve the Top-K most similar document chunks.
5. Send the retrieved context to the LangGraph agent.
6. Generate a final response using the LLM.

Workflow:

```
User Question
      │
      ▼
Generate Query Embedding
      │
      ▼
Search FAISS Index
      │
      ▼
Retrieve Top-K Chunks
      │
      ▼
Send Context to LLM
      │
      ▼
AI Response
```

---

# 8. Index Update Strategy

The FAISS index must remain synchronized with the SQLite database.

## New Document

```
Upload Document
        │
        ▼
Save Metadata in SQLite
        │
        ▼
Generate Embeddings
        │
        ▼
Add Vectors to FAISS
        │
        ▼
Save Updated Index
```

## Updated Document

```
Update Document
        │
        ▼
Regenerate Embeddings
        │
        ▼
Update FAISS Index
        │
        ▼
Save Index
```

## Deleted Document

```
Delete Metadata
        │
        ▼
Remove Vector
        │
        ▼
Rebuild or Update Index
```

---

# 9. Storage Structure

The project stores relational data and vector data separately.

```
backend/
│
├── database/
│   ├── campus.db
│   └── schema.sql
│
├── vectorstore/
│   ├── faiss_index/
│   │   ├── index.faiss
│   │   └── index.pkl
│   │
│   ├── embeddings.py
│   ├── indexing.py
│   └── search.py
```

---

# 10. Technologies

| Component | Technology |
|-----------|------------|
| Relational Database | SQLite |
| Vector Database | FAISS |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Backend Framework | FastAPI |
| AI Orchestration | LangGraph |
| ORM | SQLAlchemy |
| Programming Language | Python |

---

# 11. Benefits of FAISS

The use of FAISS provides several advantages:

- High-speed semantic search.
- Efficient handling of large document collections.
- Low memory usage.
- Scalable retrieval architecture.
- Improved response relevance.
- Seamless integration with Retrieval-Augmented Generation (RAG).

---

# 12. Future Enhancements

Future improvements to the vector database include:

- Hybrid search (Keyword + Semantic Search).
- Incremental index updates.
- Metadata filtering.
- Multi-vector retrieval.
- GPU-accelerated FAISS indexing.
- Integration with external vector databases if required.

---

# 13. Conclusion

The FAISS indexing strategy provides the semantic retrieval layer for the Autonomous Campus Operating System. SQLite stores structured data and document metadata, while FAISS stores vector embeddings for efficient similarity search. Together, they enable Retrieval-Augmented Generation (RAG), allowing LangGraph agents to retrieve relevant university knowledge before generating responses with the Large Language Model. This architecture is scalable, efficient, and aligns with the project's Zero-Trust and Agentic AI objectives.