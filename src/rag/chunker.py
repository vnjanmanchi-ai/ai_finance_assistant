"""Splits knowledge base markdown articles into embeddable chunks.

Each article has YAML front-matter (id, title, category, tags) followed by
markdown body. We split the body on '## ' section headers, since our articles
are deliberately authored with clean section boundaries — this keeps each
chunk topically coherent instead of cutting mid-thought at a fixed token count.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Chunk:
    chunk_id: str
    article_id: str
    title: str
    category: str
    tags: list[str] = field(default_factory=list)
    section_heading: str = ""
    text: str = ""


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def parse_article(path: Path) -> tuple[dict, str]:
    """Returns (front_matter_dict, body_markdown)."""
    raw = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(raw)
    if not match:
        raise ValueError(f"{path.name}: missing YAML front-matter block")
    front_matter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return front_matter, body


def chunk_article(path: Path, min_chunk_chars: int = 200) -> list[Chunk]:
    """Split one article file into a list of Chunk objects."""
    front_matter, body = parse_article(path)
    article_id = front_matter["id"]
    title = front_matter["title"]
    category = front_matter["category"]
    tags = front_matter.get("tags", [])

    # Split on level-2 headers ("## Section name"), keep the intro (before
    # the first header) as its own chunk if it's substantial.
    sections = re.split(r"\n(?=## )", body.strip())

    chunks: list[Chunk] = []
    for i, section in enumerate(sections):
        section = section.strip()
        if len(section) < min_chunk_chars:
            # Too short to stand alone (e.g. the disclaimer footer) — merge
            # into the previous chunk rather than indexing a near-empty vector.
            if chunks:
                chunks[-1].text += "\n\n" + section
            continue

        heading_match = re.match(r"^##\s+(.+)", section)
        heading = heading_match.group(1) if heading_match else title

        chunks.append(
            Chunk(
                chunk_id=f"{article_id}-{i:02d}",
                article_id=article_id,
                title=title,
                category=category,
                tags=tags,
                section_heading=heading,
                text=section,
            )
        )
    return chunks


def chunk_all_articles(knowledge_base_dir: Path) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for md_file in sorted(knowledge_base_dir.glob("*.md")):
        all_chunks.extend(chunk_article(md_file))
    return all_chunks


if __name__ == "__main__":
    kb_dir = Path(__file__).resolve().parents[2] / "knowledge_base"
    chunks = chunk_all_articles(kb_dir)
    print(f"Produced {len(chunks)} chunks from {len(list(kb_dir.glob('*.md')))} articles")
    for c in chunks[:3]:
        print(f"  [{c.chunk_id}] {c.section_heading} ({len(c.text)} chars)")
