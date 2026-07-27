"""Base class every one of the 6 agents inherits from.

Wires in: LLM call w/ retry, optional RAG retrieval, and the Phase 3.5
governance/security layer (disclaimers, audit logging, prompt-injection
delimiting) — so every subclass gets these for free instead of
each agent re-implementing them.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.azure_clients import chat_deployment_name, get_openai_client
from src.core.config import agent_config
from src.core.governance import append_disclaimer, format_citations, log_audit_event
from src.core.security import SYSTEM_GUARDRAIL_PREAMBLE, check_content_safety, wrap_retrieved_context
from src.rag.search_index import retrieve


class BaseAgent(ABC):
    name: str = "base_agent"  # override in subclasses, must match config.yaml agents.<name>

    def __init__(self) -> None:
        self.cfg = agent_config(self.name)
        self.model_deployment = chat_deployment_name(self.cfg["model"])
        self.kb_categories = self.cfg.get("kb_categories", [])

    @abstractmethod
    def system_prompt(self) -> str:
        """Each agent defines its own role/scope/constraints."""
        raise NotImplementedError

    def retrieve_context(self, query: str) -> list[dict]:
        """Pull relevant KB chunks, filtered to this agent's allowed categories.
        Agents with no kb_categories (e.g. Market Analysis) skip RAG entirely.
        """
        if not self.kb_categories:
            return []
        results: list[dict] = []
        for category in self.kb_categories:
            results.extend(retrieve(query, category=category, top_k=2))
        return results[:4]  # cap total context chunks

    @retry(wait=wait_exponential(min=1, max=15), stop=stop_after_attempt(3))
    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=self.model_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    def run(self, user_query: str, session_id: str | None = None) -> dict:
        """Standard entry point for every agent. Returns a dict with the
        response text, sources used, and session id — ready to slot into
        LangGraph state or a FastAPI response.
        """
        session_id = session_id or str(uuid.uuid4())

        is_safe, reason = check_content_safety(user_query)
        if not is_safe:
            return {
                "agent": self.name,
                "response": "I can't help with that request.",
                "sources": [],
                "session_id": session_id,
                "blocked_reason": reason,
            }

        sources = self.retrieve_context(user_query)
        context_block = wrap_retrieved_context(sources) if sources else ""

        full_system_prompt = self.system_prompt()
        if context_block:
            full_system_prompt = (
                f"{full_system_prompt}\n\n{SYSTEM_GUARDRAIL_PREAMBLE}\n\n"
                f"Reference material for this query:\n{context_block}"
            )

        raw_response = self._call_llm(full_system_prompt, user_query)
        final_response = append_disclaimer(self.name, raw_response)
        if sources:
            final_response = f"{final_response}\n\n{format_citations(sources)}"

        log_audit_event(
            agent_name=self.name,
            session_id=session_id,
            user_query=user_query,
            response_text=final_response,
            sources=sources,
            model_used=self.model_deployment,
        )

        return {
            "agent": self.name,
            "response": final_response,
            "sources": sources,
            "session_id": session_id,
        }
