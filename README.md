# 💰 AI Finance Assistant — Multi-Agent RAG System for Financial Education

A production-grade multi-agent AI financial education assistant for a retail banking app, built with **Retrieval-Augmented Generation (RAG)**, **LangGraph**, **Azure OpenAI (gpt-5-mini)**, **Azure AI Search**, **FastAPI**, and **React**. Six specialized agents — three of them RAG-grounded — handle general education, portfolio analysis, live market data, savings projections, news, and tax education, backed by a curated knowledge base with an empirically-calibrated groundedness gate that detects and declines out-of-scope questions rather than answering from the model's own unverified training knowledge. Built with strict "education, not advice" guardrails, PII redaction, and checkpointed, resumable orchestration.

---

## Key Features

- **Retrieval-Augmented Generation (RAG)** — three agents grounded in a curated 10-article knowledge base via Azure AI Search vector retrieval, with source citations on every grounded answer
- **Empirically-calibrated groundedness gate** — discovered a real false-citation bug in production use, root-caused it to Azure AI Search's hybrid RRF fusion score being unusable as a relevance signal, switched to vector-only cosine similarity, and calibrated a real threshold from actual good/bad query data
- Multi-agent orchestration using LangGraph, with single- and multi-agent (parallel fan-out) routing
- Live market data (yfinance primary, Alpha Vantage fallback) with in-memory TTL caching
- Deterministic financial math (portfolio allocation, diversification scoring, compound-interest projections) — the LLM explains numbers, never invents them
- Checkpointed conversation state with genuine resume-on-failure (not just restart)
- Governance built into every agent call: disclaimer injection, audit logging, PII redaction
- Prompt-injection resistant RAG context, verified via live adversarial testing
- FastAPI backend + React frontend, ready for Azure Container Apps deployment

---

## Overview

User queries are classified by an LLM router into one or more of six specialist agents, which run in parallel where needed and converge into a single synthesized response. Every response is grounded either in a curated knowledge base (RAG), live market data, or deterministic calculations — never in the model's own unverified training knowledge, which is explicitly detected and declined.

```
User (React UI)
      ↓
   FastAPI (/chat)
      ↓
   router_node          ← LLM intent classification, returns 1+ agent names
      ↓
 ┌────┴─────┬─────────┬────────┬────────┬────────┐
 finance_qa portfolio market  goal    news     tax
             _analysis _analysis planning synth  education
 └────┬─────┴─────────┴────────┴────────┴────────┘
      ↓
  synthesis_node       ← combine, 1 disclaimer, deduped citations
      ↓
 Response → React UI
```

---

## RAG Pipeline

Three of the six agents (Finance Q&A, Tax Education, and optionally Portfolio Analysis/Goal Planning) are grounded via Retrieval-Augmented Generation, not the model's own training knowledge:

```
knowledge_base/*.md  (10 curated articles, YAML front-matter: id, title, category, tags)
        ↓  chunker.py    — header-based chunking (splits on ## sections)
        ↓  embedder.py   — Azure OpenAI text-embedding-3-small, batched
        ↓  search_index.py — Azure AI Search, vector-only index
        ↓
   retrieve(query, category)  — filtered to the calling agent's allowed categories
        ↓
   relevance gate (score ≥ 0.58, empirically calibrated)
        ↓
   ┌─── PASS ───────────────┐        ┌─── FAIL ───────────────────┐
   │ context injected,      │        │ explicitly told to decline, │
   │ citations attached     │        │ NOT answer from training    │
   └─────────────────────────┘        │ knowledge                   │
                                       └──────────────────────────────┘
```

**Why this matters, and how it was verified:** a live test asking an out-of-scope question ("What is India's GDP growth rate?") initially produced a fluent, confident answer from the model's own training data — with citations falsely attached to unrelated knowledge-base articles. Root-caused to Azure AI Search's hybrid search using Reciprocal Rank Fusion, which scores by rank position, not semantic distance, and is therefore unusable as a cross-query relevance signal. Fixed by switching to vector-only cosine similarity and empirically calibrating a threshold (`0.58`) from real good-query vs. bad-query score distributions — then verified in both directions before considering it resolved. Full write-up in `docs/` and the project's test log.

---

## Architecture

<img width="823" height="791" alt="image" src="https://github.com/user-attachments/assets/29c6af94-59f4-43a0-b6d8-a35236241b2c" />


### Groundedness gate

Retrieval uses **vector-only** search (not hybrid), specifically because Azure AI Search's hybrid Reciprocal Rank Fusion score was found — via live testing — to be unusable as an absolute relevance signal (rank-based, not distance-based). Cosine similarity scores below an empirically-calibrated threshold (`0.58`, derived from real good/bad query comparisons) cause the agent to explicitly decline rather than answer from the model's own training knowledge.

### Governance, built into `BaseAgent`

Every agent call passes through:
1. Content-safety check (Azure platform-level jailbreak/content filtering + a `check_content_safety` extension point)
2. RAG retrieval, filtered to the agent's allowed knowledge-base categories and relevance threshold
3. LLM call via Azure OpenAI's **Responses API** (`client.responses.create`) — required for `gpt-5-mini`, which is not exposed on the classic Chat Completions surface
4. Disclaimer injection (config-driven, per agent)
5. **PII redaction before audit logging** — regex-based, catching SSNs and account-number-shaped sequences at the actual point of persistence, not the display layer
6. Structured audit log write

### Checkpointing

Each conversation gets a `thread_id`; LangGraph's checkpointer persists state after every node. On a transient failure, `retry_query(thread_id)` resumes from the last checkpoint rather than restarting the whole analysis — verified via a live test that deliberately forced a mid-graph failure.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 (backend), JavaScript/JSX (frontend) |
| Agent Framework | LangGraph |
| LLM | Azure OpenAI — gpt-5-mini (Responses API), text-embedding-3-small |
| Vector Store | Azure AI Search (vector-only retrieval) |
| Backend Framework | FastAPI + Pydantic |
| Frontend Framework | React 18 (Vite) |
| Live Market Data | yfinance (primary), Alpha Vantage (fallback) |
| Config | PyYAML + python-dotenv |
| Testing | pytest + standalone diagnostic scripts |
| Deployment (target) | Docker, Azure Container Apps, Azure Static Web Apps, Azure Key Vault |

---

## Project Structure

```
ai_finance_assistant/
├── Dockerfile
├── .dockerignore
├── config.yaml                       # deployment names, kb_categories, governance rules
├── requirements.txt
├── .env.example
├── README.md
│
├── src/
│   ├── main.py                       # FastAPI entry point
│   │
│   ├── core/
│   │   ├── config.py                 # loads config.yaml + .env, cached
│   │   ├── azure_clients.py          # AzureOpenAI (embeddings) + plain OpenAI (v1/Responses)
│   │   ├── governance.py             # disclaimers, audit logging, citation formatting
│   │   └── security.py               # prompt-injection guard, PII redaction
│   │
│   ├── rag/
│   │   ├── chunker.py                # header-based (## sections) chunking
│   │   ├── embedder.py                # text-embedding-3-small, batched, retried
│   │   ├── search_index.py           # index schema + vector-only retrieve()
│   │   └── ingest.py                 # one-shot: chunk → embed → upload
│   │
│   ├── agents/
│   │   ├── base_agent.py             # shared LLM call, RAG, governance, security
│   │   ├── finance_qa_agent.py       # pure RAG
│   │   ├── tax_education_agent.py    # pure RAG
│   │   ├── portfolio_analysis_agent.py  # compute-then-explain
│   │   ├── goal_planning_agent.py    # compute-then-explain
│   │   ├── market_analysis_agent.py  # live API, no RAG
│   │   └── news_synthesizer_agent.py # live API, no RAG
│   │
│   └── workflow/
│       ├── state.py                  # AgentState + merge_agent_outputs reducer
│       ├── router.py                 # LLM intent classification
│       ├── nodes.py                  # AgentState ↔ agent-interface translation
│       ├── synthesis.py              # multi-agent combination
│       └── graph.py                  # StateGraph assembly + checkpointing
│
├── knowledge_base/                   # 10 curated articles + manifest.json
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── index.css
│       └── components/
│           ├── ChatMessage.jsx
│           ├── ChatInput.jsx
│           ├── PortfolioPanel.jsx
│           └── TickerLookup.jsx
│
├── docs/
│   └── architecture.svg
│
└── tests/
    └── test_chunker.py
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend)
- An Azure subscription with:
  - Azure OpenAI resource, with `gpt-5-mini` and `text-embedding-3-small` deployed
  - Azure AI Search resource (Free tier is sufficient for the current knowledge base size)
- (Optional) A free Alpha Vantage API key, for the market-data fallback path

### 2. Clone and create a virtual environment

```bash
git clone https://github.com/<your-username>/ai_finance_assistant.git
cd ai_finance_assistant

python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env` with your real Azure values:

```
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_CHAT_ENDPOINT=https://<your-resource>.services.ai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
AZURE_SEARCH_API_KEY=<your-key>
ALPHA_VANTAGE_API_KEY=<optional>
```

> **Note:** `gpt-5-mini` requires Azure's newer **v1 Responses API** endpoint (`AZURE_OPENAI_CHAT_ENDPOINT`, ending in `/openai/v1/` — trailing slash required), which is distinct from the classic embeddings endpoint (`AZURE_OPENAI_ENDPOINT`). See `src/core/azure_clients.py` for details.

### 5. Ingest the knowledge base

```bash
python -m src.rag.chunker      # sanity check — no Azure calls
python -m src.rag.ingest       # creates the index, embeds and uploads all articles
```

### 6. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Running the App

Two terminals, running simultaneously:

**Terminal 1 — backend**
```bash
uvicorn src.main:app --reload --port 8000
```

**Terminal 2 — frontend**
```bash
cd frontend
npm run dev
```

Open your browser at:

```
http://localhost:3000
```

Interactive API docs (Swagger UI) are available at:

```
http://localhost:8000/docs
```

---

## How to Use

### Ask a general question

```
What's the difference between a stock and a bond?
```

### Analyze your portfolio

Expand **My holdings** in the UI, add tickers with asset class and value, then ask:

```
How diversified is my portfolio?
```

### Combine portfolio + live market data (multi-agent case)

```
How is my portfolio doing given today's market?
```

### Check a live stock price

Expand **Check a stock price**. US tickers are plain (`AAPL`); NSE-listed Indian stocks need a `.NS` suffix (`HDFCBANK.NS`); BSE-listed need `.BO`.

### Ask about savings goals

```python
from src.agents.goal_planning_agent import GoalPlanningAgent
agent = GoalPlanningAgent()
result = agent.analyze(years=10, monthly_contribution=500, contribution_delta=100,
                        user_query="If I save $500/month for 10 years, how much will I have?")
```

### Out-of-scope questions

Questions outside the knowledge base's scope (macroeconomics, unrelated topics) are explicitly declined rather than answered from the model's general training knowledge:

```
User:      What is India's GDP growth rate?
Assistant: I don't have grounded reference material for current
           macroeconomic figures, so I can't provide India's up-to-date
           GDP growth rate. I won't answer this from general knowledge
           as if it were sourced.
```

---

## Running Tests

```bash
pytest tests/ -v
```

Standalone diagnostic and behavioral test scripts (run individually, require `.env` configured):

```bash
python test_state.py               # multi-agent parallel-write correctness
python test_memory.py              # multi-turn conversation continuity
python test_checkpoint_resume.py   # forced-failure checkpoint resume
python test_prompt_injection.py    # adversarial input resistance
python test_out_of_scope.py        # personalized-advice refusal boundary
python diagnose_relevance_scores.py  # groundedness threshold calibration
```

---

## Key Design Decisions

**Why two different Azure OpenAI clients?** `gpt-5-mini` is only exposed via Azure's newer unified "v1" API surface (`client.responses.create`, plain `OpenAI` client with a manually-set `base_url`) — not the classic Chat Completions API. Embeddings still use the classic `AzureOpenAI` client. Both point at the same underlying resource, just different API surfaces. See `src/core/azure_clients.py`.

**Why vector-only retrieval instead of hybrid?** Hybrid search's fused Reciprocal Rank Fusion score is rank-based, not distance-based — testing showed it could not distinguish a genuinely relevant match from a fabricated one. Vector-only cosine similarity provides a real, comparable relevance signal, at the cost of losing exact-keyword-match strength.

**Why do some agents use `.run()` and others `.analyze()`?** `FinanceQAAgent`/`TaxEducationAgent` fit `BaseAgent`'s simple `run(query, session_id)` shape. `PortfolioAnalysisAgent`/`GoalPlanningAgent` need structured numeric input and perform deterministic math before any LLM call — forcing them into the same interface would have polluted the base class. Each agent's calling convention is absorbed by a thin wrapper in `workflow/nodes.py`.

**Why does `agent_outputs` need a custom reducer?** Multi-agent fan-out (e.g. Portfolio + Market running in parallel) causes concurrent writes to the same state key in the same graph step. LangGraph's default reducer only accepts one write per key per step — `merge_agent_outputs` (in `workflow/state.py`) merges them, the same conceptual role `add_messages` plays for conversation history.

**Why structured input via UI forms, not chat-text parsing?** Reliably extracting a portfolio holding or stock ticker from free-text chat is a real NLP problem on its own. `PortfolioPanel.jsx` and `TickerLookup.jsx` collect this explicitly; agent nodes assume it's pre-populated, with a graceful clarifying-question fallback if it's missing.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | ✅ Yes | Classic endpoint, used for embeddings |
| `AZURE_OPENAI_CHAT_ENDPOINT` | ✅ Yes | v1/Responses API endpoint, used for gpt-5-mini chat calls (trailing slash required) |
| `AZURE_OPENAI_API_KEY` | ✅ Yes | Shared key for both endpoints (same underlying resource) |
| `AZURE_SEARCH_ENDPOINT` | ✅ Yes | Azure AI Search service endpoint |
| `AZURE_SEARCH_API_KEY` | ✅ Yes | Azure AI Search admin key |
| `ALPHA_VANTAGE_API_KEY` | No | Market-data fallback provider; yfinance is primary and needs no key |

---

## Known Limitations

- **Groundedness is query-level, not claim-level.** A query with a thin but genuine partial match can still blend real knowledge-base content with substantial model-generated elaboration under one citation footer. A dedicated groundedness-detection API (e.g. Azure AI Content Safety) would solve this at the claim level.
- **PII redaction is regex-based**, not a full PII detection service — it catches common shapes (SSNs, long account-number-like sequences) but isn't exhaustive.
- **Conversation-history threading** is implemented for `FinanceQAAgent`/`TaxEducationAgent`; the other four agents don't yet receive prior-turn context in their `.analyze()` calls.
- **Real brokerage integration** (e.g. Zerodha Kite Connect) is not implemented — `TickerLookup` provides live market data for any yfinance-supported ticker, but does not read a user's actual brokerage holdings.

---

## Security Notes

- `.env` is gitignored and never committed — see `.gitignore`
- `.env` is explicitly excluded from the Docker build context (`.dockerignore`) — secrets never enter image layers
- All PII is redacted before audit logging, not just before display
- Prompt-injection resistance verified via live adversarial testing (direct override attempts + subtler social-engineering framing)
- Production deployment plan moves secrets to Azure Key Vault with Managed Identity, replacing local `.env`-based API keys

---

## Troubleshooting

**`DeploymentNotFound` when calling gpt-5-mini**
Confirm `AZURE_OPENAI_CHAT_ENDPOINT` ends in `/openai/v1/` **with a trailing slash** — without it, the SDK's URL-joining silently drops the `/v1` path segment.

**`ModuleNotFoundError: No module named 'src'`**
Run all commands from the project root, not from inside `src/` or `tests/`.

**`ModuleNotFoundError: No module named 'azure'` / `'yaml'`**
Your virtual environment isn't activated, or `pip install -r requirements.txt` wasn't run inside it. Confirm `(venv)` appears in your terminal prompt.

**Frontend shows "Can't reach the backend"**
Confirm `uvicorn src.main:app --reload --port 8000` is running in a separate terminal.

**Azure AI Search errors on ingest**
Confirm the Search resource actually exists and its endpoint/key in `.env` match its own **Keys and Endpoint** page — not a different, similarly-named Azure OpenAI resource.

---

## License

MIT
