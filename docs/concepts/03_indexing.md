# 03 — Indexing

## The one-sentence version

Indexing is storing every chunk (its text, its metadata, and its embedding vector) somewhere that can be searched quickly, at scale — that "somewhere" is a vector database, and ours is Azure AI Search.

## Why you can't just keep vectors in a Python list

Technically, you could store all 62 chunk vectors in a Python list and, at query time, manually compute the distance from the question's vector to all 62 stored vectors, then sort and pick the closest ones. For 62 chunks, that would even work fine. It falls apart at scale — thousands or millions of chunks — because comparing one query against every single stored vector, one at a time, gets slow fast. A vector database's whole job is doing that comparison efficiently using specialized indexing algorithms, so search stays fast even as your knowledge base grows far beyond 10 articles.

## What actually gets stored per chunk

Looking at our index schema in `search_index.py`, each chunk becomes one "document" in the index with these fields:

| Field | What it is | Why it's there |
|---|---|---|
| `chunk_id` | Unique ID like `kb-001-02` | The primary key — every document needs one |
| `article_id`, `title`, `category`, `tags`, `section_heading` | Metadata carried over from chunking | Lets us filter (e.g. `category eq 'tax_advantaged_accounts'`) and show citations |
| `content` | The actual chunk text | This is what gets shown to the LLM and cited to the user — the vector alone is meaningless to a human |
| `content_vector` | The 1536-number embedding | This is what the *search* actually compares against |

## "Hybrid search" — why we search two ways at once

Our `retrieve()` function does both a **vector search** (find chunks with similar meaning, even different wording) and a **keyword search** (find chunks containing the user's literal words) in the same call, then Azure AI Search blends the results. This matters because vector search alone can occasionally miss an exact term match (like a specific fund name or acronym) that a simple keyword search would catch instantly. Hybrid search gets the best of both — meaning-based matching *and* exact-term matching — rather than picking one at the cost of the other.

## Why we filter by category instead of searching everything

Every agent has a `kb_categories` list in `config.yaml`. When the Tax Education agent calls `retrieve()`, it passes `category="tax_advantaged_accounts"`, so Azure AI Search only searches within that subset instead of the whole knowledge base. Two reasons this matters:
1. **Relevance** — prevents an ETF question's chunk from sneaking into a tax-education answer just because it was vaguely similar.
2. **Governance** — it's a control, not just a nicety: it enforces that each agent stays within its intended domain, which ties into the "task adherence" security control from Phase 3.5.

## Where this lives in our code

`src/rag/search_index.py`:
- `build_index_schema()` — defines the fields/types above (this is a one-time schema definition, like a table schema in a regular database)
- `create_or_update_index()` — actually creates the index in your Azure AI Search resource
- `upload_chunks()` — embeds and uploads chunks in batches (called once per knowledge base update, via `ingest.py`)
- `retrieve()` — the query-time search function every agent calls through `base_agent.py`

## The analogy that usually clicks

If you've used a regular (non-vector) database before: `chunk_id` is like a primary key, `category`/`tags` are like normal filterable columns, and `content_vector` is like a special column type that supports "find rows similar to this one" instead of "find rows exactly equal to this value." Everything else about it — creating a schema, uploading rows, querying with filters — works the same way you'd expect from any database.
