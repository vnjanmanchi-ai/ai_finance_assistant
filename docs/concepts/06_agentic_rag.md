# 06 — Agentic RAG

## The one-sentence version

"Agentic RAG" means RAG isn't just a single Q&A lookup — it's wrapped inside agents that can reason, decide which knowledge/tools to use, and hand off to each other, orchestrated by a graph (LangGraph) instead of one straight-line script.

## Plain RAG vs. agentic RAG — what actually changes

**Plain RAG** (what `04_rag_pipeline.md` describes) is a single, fixed sequence: question → retrieve → generate → answer. It's the same steps every time, for every kind of question.

**Agentic RAG** adds a decision layer on top: given a question, *which* specialized process should handle it, does it need RAG at all, does it need live data instead (or in addition), and does it need more than one specialist to answer fully? Our 6 agents plus a router is exactly this layer.

## Why one Q&A agent isn't enough for this project

Consider these three questions:
- *"What's an ETF?"* → pure knowledge lookup, RAG is exactly right (Finance Q&A agent)
- *"What's Apple's stock price right now?"* → RAG is useless here — no knowledge base article has today's price. This needs a live API call instead (Market Analysis agent)
- *"How's my portfolio's diversification, given today's market?"* → needs *both* the user's holdings data *and* live market context — a single agent covering everything would need every possible tool and every possible knowledge category all the time, which gets bloated and harder to keep accurate

Agentic RAG's job is routing each question to the right specialist (or combination of specialists) instead of forcing one processes to do everything.

## What LangGraph actually adds

LangGraph represents the whole conversation as a **graph**: nodes are processing steps (a router, an agent), edges are "what happens next," and a shared **state** object flows through every node, accumulating information as it goes (see `src/workflow/state.py`'s `AgentState`).

```
        ┌──────────┐
        │  Router  │   "does this need Q&A, Portfolio, Market, or several?"
        └────┬─────┘
             │
    ┌────────┼─────────┬─────────────┐
    ▼        ▼          ▼             ▼
 Finance   Portfolio  Market       Goal Planning
   QA      Analysis   Analysis      (etc.)
    │        │          │             │
    └────────┴─────┬────┴─────────────┘
                    ▼
          Synthesize final response
```

This is more flexible than a fixed if/else chain in plain Python because:
- **Conditional routing** — the router can send a question to 1 agent or to 3, based on what's actually being asked
- **Shared memory** — `AgentState` carries the conversation and a user's portfolio data across turns, so the Portfolio agent doesn't need the user to re-paste their holdings every message
- **Composability** — adding a 7th agent later means adding one more possible route, not rewriting a long chain of if-statements

## Where "agentic" and "RAG" meet in our code, concretely

Every individual agent (`base_agent.py`, `finance_qa_agent.py`) is still doing plain RAG internally — retrieve, wrap, generate, as described in `04_rag_pipeline.md`. What makes the *system* agentic is the layer we haven't built yet (Phase 5): the router node that decides *which* agent(s) to call for a given message, and the graph structure that lets their outputs combine into one final response.

## What's built vs. what's next

- **Built**: `AgentState` schema (the shared data structure the graph will pass around), and one fully working agent (`FinanceQAAgent`) that does the RAG half correctly
- **Next (Phase 4)**: the other 5 agents, each following the same `BaseAgent` pattern
- **After that (Phase 5)**: the actual LangGraph `StateGraph` — the router node, the conditional edges connecting router → agents → synthesis, wired together for the first time

## The mental model to keep

RAG answers "how does one agent find and use the right knowledge." Agentic RAG answers "how does the system decide which agent(s) should even be involved, and how do their answers come together." Our project needs both — and right now we have the first fully working for one agent, with the second (the router/graph) still ahead of us.
