# AI Finance Assistant — Phase 1 & 2 scaffold

Multi-agent financial education chatbot. See `AI_Finance_Assistant_Build_Roadmap.md` (separate doc) for the full phase-by-phase plan.

## New here? Start with the concepts docs

If the RAG flow feels unclear, read `docs/concepts/` in order (00 → 06) before diving into code — each doc explains one concept plainly and points to the exact file that implements it. `00_overview.md` specifically untangles the two flows that usually cause confusion: "build time" (chunk → embed → index, runs once) vs. "query time" (retrieve → generate, runs every message).

## What's implemented so far

- **Phase 1 (foundations)**: `config.yaml` driven configuration, Azure OpenAI + Azure AI Search client factories (`src/core/azure_clients.py`), the LangGraph `AgentState` schema (`src/workflow/state.py`), and a `BaseAgent` class that every agent inherits from.
- **Phase 2 (RAG)**: 10 knowledge base articles (`knowledge_base/`), a section-aware chunker, an Azure OpenAI embedder, an Azure AI Search index schema + upload/retrieve client, and a one-shot ingestion script.
- **Phase 3.5 (governance & security)**: built directly into `BaseAgent` — every agent call gets disclaimer injection, audit logging, and prompt-injection-resistant context wrapping for free. See `src/core/governance.py` and `src/core/security.py`.
- **First concrete agent**: `src/agents/finance_qa_agent.py` — the reference implementation the other 5 agents should follow.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in .env with your Azure OpenAI + Azure AI Search endpoint/key values
```

You'll need, at minimum:
- An Azure OpenAI resource with `gpt-4o-mini`, `gpt-4o`, and `text-embedding-3-small` deployed
- An Azure AI Search resource (Free tier is enough for these 10 articles)

## Ingest the knowledge base into Azure AI Search

```bash
python -m src.rag.ingest
```

This creates the search index (if it doesn't exist) and uploads all chunked, embedded articles.

## Run tests

```bash
pytest tests/ -v --cov=src
```

`tests/test_chunker.py` runs with no Azure credentials required — it only tests the local chunking logic. Later phases will add tests that mock the Azure OpenAI/Search calls for the agents and orchestration.

## Try the first agent (requires .env configured + knowledge base ingested)

```bash
python -m src.agents.finance_qa_agent
```

## Project structure

```
src/
├── core/         # config loading, Azure client factories, governance, security
├── rag/          # chunking, embedding, Azure AI Search index + retrieval
├── agents/       # BaseAgent + one file per agent
└── workflow/     # LangGraph state schema (orchestration comes in Phase 5)
knowledge_base/   # 10 curated articles + manifest.json
tests/            # pytest suite
```

## Next steps (Phase 3 continued → Phase 4)

Build out the remaining 5 agents (`portfolio_analysis_agent.py`, `market_analysis_agent.py`, `goal_planning_agent.py`, `news_synthesizer_agent.py`, `tax_education_agent.py`), each following the `FinanceQAAgent` pattern — inherit `BaseAgent`, set `name`, implement `system_prompt()`.
