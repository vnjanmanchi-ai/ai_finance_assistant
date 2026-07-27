"""One-shot script: chunk every article in knowledge_base/, embed, and upload
to Azure AI Search. Run this whenever the knowledge base changes.

Usage:
    python -m src.rag.ingest
"""
from __future__ import annotations

from pathlib import Path

from src.rag.chunker import chunk_all_articles
from src.rag.search_index import create_or_update_index, upload_chunks

KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"


def main() -> None:
    print("Step 1/3 — creating/updating Azure AI Search index schema...")
    create_or_update_index()

    print("Step 2/3 — chunking articles...")
    chunks = chunk_all_articles(KB_DIR)
    print(f"  {len(chunks)} chunks produced from articles in {KB_DIR}")

    print("Step 3/3 — embedding + uploading chunks...")
    upload_chunks(chunks)

    print("Done. Knowledge base is indexed and ready for retrieval.")


if __name__ == "__main__":
    main()
