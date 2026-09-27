"""Build the Fee AI Assistant's reusable vector store from reviewed sources.

Run this only when the curated source snapshot changes. Student chat requests do
not call the network and never run this script.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.timetable_knowledge import LocalHashEmbedding  # noqa: E402


SOURCE_PATH = PROJECT_ROOT / "backend" / "backend" / "vectorstore" / "fee_knowledge" / "sources.json"
STORE_PATH = PROJECT_ROOT / "backend" / "backend" / "vectorstore" / "fee_knowledge" / "fee_knowledge.json"


def build() -> dict:
    with SOURCE_PATH.open("r", encoding="utf-8") as handle:
        source_data = json.load(handle)
    provider = LocalHashEmbedding()
    documents = []
    for item in source_data["documents"]:
        text = " ".join(str(item["text"]).split())
        documents.append(
            {
                "id": item["id"],
                "text": text,
                "metadata": {
                    "title": item["title"],
                    "source_url": item["source_url"],
                    "retrieved_at": source_data["retrieved_at"],
                    "institution": source_data["institution"],
                    "source_type": "official-university-website",
                },
                "embedding": provider.embed(text),
            }
        )
    store = {
        "format_version": 1,
        "institution": source_data["institution"],
        "embedding_model": provider.name,
        "dimensions": provider.dimensions,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_retrieved_at": source_data["retrieved_at"],
        "documents": documents,
    }
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STORE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return store


if __name__ == "__main__":
    result = build()
    print(f"Wrote {len(result['documents'])} embedded documents to {STORE_PATH}")

