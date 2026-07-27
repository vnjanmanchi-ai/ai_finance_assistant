"""Finance Q&A Agent — general financial education, grounded in the RAG
knowledge base. This is the reference implementation the other 5 agents
(Portfolio, Market, Goal Planning, News, Tax Education) should follow.
"""
from __future__ import annotations

from src.agents.base_agent import BaseAgent


class FinanceQAAgent(BaseAgent):
    name = "finance_qa"

    def system_prompt(self) -> str:
        return (
            "You are a financial education assistant for a retail banking app. "
            "Answer general questions about investing concepts (stocks, bonds, "
            "ETFs, diversification, compound interest, tax-advantaged accounts) "
            "clearly and accurately, grounded in the reference material provided. "
            "You provide education, never personalized investment or tax advice — "
            "never tell the user what they specifically should buy, sell, or do "
            "with their money. If a question asks for personalized advice, explain "
            "the relevant general concept and note that a licensed advisor can "
            "help apply it to their situation. Keep answers concise and in plain "
            "language."
        )


if __name__ == "__main__":
    # Manual smoke test — requires .env configured and the index already
    # populated via `python -m src.rag.ingest`.
    agent = FinanceQAAgent()
    result = agent.run("What's the difference between a stock and a bond?")
    print(result["response"])
