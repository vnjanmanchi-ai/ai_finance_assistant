"""Generates embeddings for chunks via Azure OpenAI."""
from __future__ import annotations

from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.azure_clients import embedding_deployment_name, get_openai_client


@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(4))
def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of strings. Retries with backoff on transient errors."""
    client = get_openai_client()
    deployment = embedding_deployment_name()
    response = client.embeddings.create(model=deployment, input=texts)
    # response.data is returned in the same order as the input list
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
