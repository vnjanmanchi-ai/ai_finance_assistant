"""Chunker tests — no Azure credentials required, safe to run in CI."""
from pathlib import Path

from src.rag.chunker import chunk_all_articles, chunk_article

KB_DIR = Path(__file__).resolve().parents[1] / "knowledge_base"


def test_all_articles_produce_chunks():
    chunks = chunk_all_articles(KB_DIR)
    assert len(chunks) > 0
    # 10 articles, each with multiple sections, should produce well over 10 chunks
    assert len(chunks) >= 20


def test_chunk_has_required_metadata():
    chunks = chunk_all_articles(KB_DIR)
    for c in chunks:
        assert c.article_id.startswith("kb-")
        assert c.category
        assert c.text.strip()


def test_single_article_chunking():
    path = KB_DIR / "01_what_is_a_stock.md"
    chunks = chunk_article(path)
    assert all(c.article_id == "kb-001" for c in chunks)
    assert any("dividend" in c.text.lower() for c in chunks)
