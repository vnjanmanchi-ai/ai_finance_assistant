# 02 — Chunking

## The one-sentence version

Chunking is splitting a long document into smaller pieces before embedding them, because embedding an entire article as one vector loses too much detail to be useful for search.

## Why we can't just embed whole articles

Imagine embedding this entire question: "what is diversification, what is risk tolerance, and how does compound interest work" all as one giant vector representing one 2,000-word article. If a user asks specifically about risk tolerance, that one giant vector is an *average* of everything in the article — stocks, risk, compound interest all blended together — so it won't match the user's specific question very precisely. Smaller, focused chunks let each one represent *one specific idea*, which matches specific questions much better.

## Why we also can't chunk too small

If you chunk down to individual sentences, you lose context. "It compounds monthly" means nothing on its own without the sentence before it explaining what "it" is. There's a balance: chunks need to be small enough to be topically focused, but large enough to be self-contained and make sense in isolation.

## Two competing chunking strategies (and which we picked)

- **Fixed-size chunking**: split every N tokens (say, every 500 tokens), regardless of where sentences or ideas end. Simple, works on any text, but can cut a sentence — or an idea — in half.
- **Structure-aware chunking**: split at natural boundaries the document already has (paragraphs, headers, sections). More setup work, but each chunk is a complete, coherent idea.

**We use structure-aware chunking.** Since every article in `knowledge_base/` is deliberately written with clear `## Section Header` boundaries, we split on those headers rather than counting tokens. This means a chunk like "How stocks create value for an investor" is always a complete, self-contained explanation — never half a thought.

## Where this lives in our code

`src/rag/chunker.py`, function `chunk_article()`:

1. Reads one markdown file
2. Splits the YAML front-matter (title, category, tags) from the body text
3. Splits the body on `## ` headers using a regex
4. Each resulting section becomes one `Chunk` object, carrying both the text *and* metadata (which article it came from, its category, its section heading)
5. Very short leftover pieces (like the one-line disclaimer footer) get merged into the previous chunk instead of becoming a near-empty, useless chunk on their own

## Why we kept metadata attached to every chunk

Look at the `Chunk` dataclass — it's not just text, it also carries `article_id`, `category`, and `section_heading`. This matters later: when the Tax Education agent searches, we don't want it accidentally retrieving a chunk about ETFs. Attaching `category` to every chunk at chunking time is what lets `search_index.py` filter searches to `category = 'tax_advantaged_accounts'` later. Chunking isn't just "cutting up text" — it's also the step where we decide what metadata will be usable for filtering during retrieval.

## Try it yourself

```bash
python -m src.rag.chunker
```
This runs the chunker standalone (no Azure needed) and prints how many chunks came from the 10 articles, so you can see the actual boundaries it chose.
