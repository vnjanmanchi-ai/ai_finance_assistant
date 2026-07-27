# 00 — The big picture: how a question becomes an answer

Read this one first. Everything else in this folder zooms into one step of the flow described here.

There are actually **two separate flows** in a RAG system, and mixing them up is the #1 source of confusion. Keep them mentally separate:

## Flow A — "Build time" (runs once, or whenever the knowledge base changes)

This happens *before* any user ever asks a question. It's the process of turning your 10 markdown articles into something searchable.

```
knowledge_base/*.md
      │
      ▼
  CHUNKING          (docs/concepts/02_chunking.md)
  split each article into smaller topic-sized pieces
      │
      ▼
  EMBEDDING         (docs/concepts/01_embeddings.md)
  turn each chunk's text into a list of numbers (a vector)
      │
      ▼
  INDEXING          (docs/concepts/03_indexing.md)
  store chunk text + its vector in Azure AI Search, ready to be searched
```

**Code**: this whole flow is `python -m src.rag.ingest`, which calls `chunker.py` → `embedder.py` → `search_index.py`. You run this once after writing the articles, and again any time you add/edit articles.

## Flow B — "Query time" (runs every single time a user sends a message)

This is what happens live, in the app, when a real user types a question.

```
User asks a question
      │
      ▼
  ROUTER (LangGraph)
  decides which of the 6 agents should handle it
      │
      ▼
  RETRIEVAL          (docs/concepts/04_rag_pipeline.md)
  embed the user's question the same way, search the index built in Flow A,
  pull back the most similar chunks
      │
      ▼
  AGENT + LLM        (docs/concepts/06_agentic_rag.md)
  the agent hands the LLM: the user's question + the retrieved chunks
  the LLM writes an answer grounded in those chunks
      │
      ▼
  GOVERNANCE WRAP
  add disclaimer, add source citations, log the interaction
      │
      ▼
  Response shown to user
```

**Code**: `src/agents/base_agent.py`'s `run()` method is Flow B end to end for one agent. `src/workflow/state.py` is the shared data structure that will let multiple agents participate in one turn once we build the LangGraph router (Phase 5).

## Why this two-flow split matters

The single most common beginner confusion in RAG is expecting the chunking/embedding code to run *during* a conversation. It doesn't. By the time a user asks a question, the knowledge base is already chunked, embedded, and sitting in Azure AI Search — query time only ever does **one new embedding** (of the user's question) and a **search**, never re-processes the whole knowledge base.

## Where evaluation fits

`05_evaluation.md` isn't a step in either flow above — it's a separate process you run *against* Flow B, asking "when I feed it these 15 test questions, does it retrieve the right chunks and give grounded answers?" It's quality control, sitting outside the pipeline itself.

## One more thing worth internalizing early

Every concept from here on out has exactly one job: turn unstructured text into something a similarity search can compare. That's it. Chunking decides *what* text becomes a unit. Embedding decides *how* that unit gets turned into comparable numbers. Indexing decides *where* it's stored so it can be searched fast. If you keep asking "is this step about splitting text, converting text to numbers, or storing/searching those numbers," the whole pipeline stops feeling like magic.
