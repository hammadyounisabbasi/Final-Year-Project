"""Persistent, read-only RAG knowledge for the student Fee AI Assistant.

The public web content is collected by the explicit maintenance script in
``scripts/build_fee_knowledge.py``.  Runtime requests only load the persisted
store; they never scrape the university website.
"""
from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.services.timetable_knowledge import LocalHashEmbedding


PROJECT_ROOT = Path(__file__).resolve().parents[4]
STORE_PATH = PROJECT_ROOT / "backend" / "backend" / "vectorstore" / "fee_knowledge" / "fee_knowledge.json"


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
        sum(value * value for value in right)
    )
    return sum(a * b for a, b in zip(left, right)) / denominator if denominator else 0.0


@lru_cache(maxsize=1)
def load_fee_store() -> dict:
    if not STORE_PATH.exists():
        return {"embedding_model": "local-hash-v1", "documents": []}
    with STORE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class FeeKnowledgeRetriever(BaseRetriever):
    """LangChain retriever backed by the checked-in, one-time vector store."""

    top_k: int = 4
    minimum_score: float = 0.04

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        store = load_fee_store()
        query_vector = LocalHashEmbedding().embed(query)
        lowered_query = query.casefold()
        query_terms = {
            token for token in re.findall(r"[a-z0-9]+", lowered_query)
            if len(token) >= 4 and token not in {"what", "which", "from", "about", "tell", "fees"}
        }
        intent_hints = (
            (("contact", "phone", "email", "department", "office", "help desk"), ("contact", "support")),
            (("pending", "unpaid", "failed", "wrong", "incorrect", "challan", "payment issue"), ("pending", "payment")),
            (("overdue", "late", "fine", "penalty"), ("dues", "charges")),
            (("scholarship", "waiver", "concession"), ("scholarship", "financial assistance")),
            (("improvement", "improve", "repeat", "retake", "deficiency", "bridging"), ("improvement", "repeat")),
            (("transport", "bus", "route", "stop"), ("transport",)),
            (("hostel", "mess", "provost"), ("hostel",)),
            (("rechecking", "recheck", "re-totaling", "retotaling", "make-up", "makeup", "attendance"), ("examination", "attendance")),
            (("migration", "credit transfer", "freeze", "freezing", "suspension", "department change", "course exemption"), ("migration", "academic charges", "graduate improvement")),
            (("other fee", "other charges", "miscellaneous fee", "miscellaneous charges"), ("other official", "miscellaneous")),
            (("deadline", "last date", "submission window"), ("deadline", "schedule")),
            (("fee structure", "program fee", "tuition"), ("fee schedule", "program")),
        )
        ranked: list[tuple[float, dict]] = []
        for record in store.get("documents", []):
            score = _cosine(query_vector, record.get("embedding", []))
            title = record.get("metadata", {}).get("title", "").casefold()
            searchable_text = f"{title} {record.get('text', '')}".casefold()
            score += 0.06 * sum(term in searchable_text for term in query_terms)
            for intent_query_terms, title_terms in intent_hints:
                if any(term in lowered_query for term in intent_query_terms) and any(term in title for term in title_terms):
                    score += 0.35
            if score >= self.minimum_score:
                ranked.append((score, record))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            Document(
                page_content=record["text"],
                metadata={**record.get("metadata", {}), "score": round(score, 4)},
            )
            for score, record in ranked[: self.top_k]
        ]


fee_knowledge_retriever = FeeKnowledgeRetriever()


def retrieve_fee_knowledge(query: str) -> list[Document]:
    """Invoke the LangChain retriever for a natural-language fee question."""
    return fee_knowledge_retriever.invoke(query)
