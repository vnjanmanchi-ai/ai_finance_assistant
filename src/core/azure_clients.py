"""Factory functions for Azure OpenAI and Azure AI Search clients.

Uses API-key auth for local dev (via .env). In the Azure Container Apps
deployment (Phase 10), swap these for azure.identity.DefaultAzureCredential /
ManagedIdentityCredential so no keys are stored anywhere.
"""
from __future__ import annotations

from functools import lru_cache

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import AzureOpenAI

from src.core.config import get_config, get_env


@lru_cache(maxsize=1)
def get_openai_client() -> AzureOpenAI:
    cfg = get_config()["azure_openai"]
    return AzureOpenAI(
        azure_endpoint=get_env(cfg["endpoint_env"]),
        api_key=get_env(cfg["api_key_env"]),
        api_version=cfg["api_version"],
    )


@lru_cache(maxsize=1)
def get_search_index_client() -> SearchIndexClient:
    cfg = get_config()["azure_ai_search"]
    return SearchIndexClient(
        endpoint=get_env(cfg["endpoint_env"]),
        credential=AzureKeyCredential(get_env(cfg["api_key_env"])),
    )


@lru_cache(maxsize=1)
def get_search_client() -> SearchClient:
    cfg = get_config()["azure_ai_search"]
    return SearchClient(
        endpoint=get_env(cfg["endpoint_env"]),
        index_name=cfg["index_name"],
        credential=AzureKeyCredential(get_env(cfg["api_key_env"])),
    )


def chat_deployment_name(which: str = "chat_fast") -> str:
    """which: 'chat_fast' (gpt-4o-mini) or 'chat_reasoning' (gpt-4o)."""
    return get_config()["azure_openai"]["deployments"][which]


def embedding_deployment_name() -> str:
    return get_config()["azure_openai"]["deployments"]["embedding"]
