"""Creates the Azure AI Search index and provides upload/retrieve functions."""
from __future__ import annotations

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from src.core.azure_clients import get_search_client, get_search_index_client
from src.core.config import get_config
from src.rag.chunker import Chunk
from src.rag.embedder import embed_text, embed_texts

EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small


def build_index_schema() -> SearchIndex:
    cfg = get_config()["azure_ai_search"]
    index_name = cfg["index_name"]
    vector_field_name = cfg["vector_field"]

    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="default-profile", algorithm_configuration_name="hnsw-config")],
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
    )

    fields = [
        SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="article_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(
            name="tags",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
        ),
        SearchableField(name="section_heading", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name=vector_field_name,
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="default-profile",
        ),
    ]

    return SearchIndex(name=index_name, fields=fields, vector_search=vector_search)


def create_or_update_index() -> None:
    index_client = get_search_index_client()
    index = build_index_schema()
    index_client.create_or_update_index(index)
    print(f"Index '{index.name}' created/updated.")


def upload_chunks(chunks: list[Chunk], batch_size: int = 16) -> None:
    """Embed and upload chunks to Azure AI Search in batches."""
    cfg = get_config()["azure_ai_search"]
    vector_field_name = cfg["vector_field"]
    search_client = get_search_client()

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = embed_texts([c.text for c in batch])
        documents = [
            {
                "chunk_id": c.chunk_id,
                "article_id": c.article_id,
                "title": c.title,
                "category": c.category,
                "tags": c.tags,
                "section_heading": c.section_heading,
                "content": c.text,
                vector_field_name: vectors[j],
            }
            for j, c in enumerate(batch)
        ]
        search_client.upload_documents(documents=documents)
        print(f"Uploaded chunks {i}–{i + len(batch) - 1}")


def retrieve(query: str, category: str | None = None, top_k: int | None = None) -> list[dict]:
    """Hybrid (vector + keyword) search over the knowledge base with an
    optional category filter, e.g. restrict Tax Education agent retrieval to
    category='tax_advantaged_accounts'.

    Returns a list of dicts with content + source metadata for citation.
    """
    cfg = get_config()["azure_ai_search"]
    vector_field_name = cfg["vector_field"]
    k = top_k or cfg["top_k"]
    search_client = get_search_client()

    query_vector = embed_text(query)
    vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=k, fields=vector_field_name)

    filter_expr = f"category eq '{category}'" if category else None

    results = search_client.search(
        search_text=query,  # keyword half of the hybrid search
        vector_queries=[vector_query],
        filter=filter_expr,
        select=["chunk_id", "article_id", "title", "category", "section_heading", "content"],
        top=k,
    )

    return [
        {
            "chunk_id": r["chunk_id"],
            "article_id": r["article_id"],
            "title": r["title"],
            "category": r["category"],
            "section_heading": r["section_heading"],
            "content": r["content"],
        }
        for r in results
    ]
