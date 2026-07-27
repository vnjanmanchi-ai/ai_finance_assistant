"""Shared state schema passed between nodes in the LangGraph StateGraph.

Deciding this contract now (Phase 1) is what lets Phase 5 (orchestration)
wire agents together without reworking each agent's interface later.
"""
from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Conversation history — LangGraph's add_messages reducer appends new
    # messages rather than overwriting, so multi-turn context is preserved.
    messages: Annotated[list, add_messages]

    session_id: str

    # Set by the router node: which agent(s) should handle this turn.
    route: list[str]

    # Optional structured context carried across turns (e.g. a user's
    # previously-entered portfolio holdings, so Portfolio Analysis doesn't
    # need to ask again every message).
    user_profile: dict[str, Any]
    portfolio: dict[str, Any]

    # Populated by whichever agent(s) ran this turn.
    agent_outputs: dict[str, dict]

    # Final synthesized response shown to the user.
    final_response: str
