"""Governance and security helpers every agent routes through.

This is intentionally small and composable — Phase 3.5 of the roadmap calls
for these to be inherited automatically by every agent via BaseAgent, not
bolted on per-agent later.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from src.core.config import get_config

DISCLAIMER_TEXT = (
    "This is general financial education, not personalized investment or tax "
    "advice. Please consult a licensed financial advisor for guidance specific "
    "to your situation."
)


def requires_disclaimer(agent_name: str) -> bool:
    cfg = get_config()["governance"]
    return agent_name in cfg.get("disclaimer_required_agents", [])


def append_disclaimer(agent_name: str, response_text: str) -> str:
    if requires_disclaimer(agent_name):
        return f"{response_text}\n\n---\n{DISCLAIMER_TEXT}"
    return response_text


def log_audit_event(
    agent_name: str,
    session_id: str,
    user_query: str,
    response_text: str,
    sources: list[dict] | None = None,
    model_used: str | None = None,
) -> None:
    """Append a structured audit record. In production this should also flow
    to Azure Application Insights, not just a local file."""
    cfg = get_config()["governance"]
    log_path = Path(cfg["audit_log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": time.time(),
        "agent": agent_name,
        "session_id": session_id,
        "query": user_query,
        "response": response_text,
        "sources": sources or [],
        "model_used": model_used,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def format_citations(sources: list[dict]) -> str:
    """Turns retrieved RAG chunks into a short, human-readable citation block."""
    if not sources:
        return ""
    lines = [f"- {s['title']} ({s['section_heading']})" for s in sources]
    return "Sources:\n" + "\n".join(lines)
