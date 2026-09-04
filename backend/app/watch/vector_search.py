"""Vector search wrapper for PakWatch — delegates to shared DB layer.

Handles embedding the query text before delegating to the shared
vector_search_chunks function in the DB layer.
"""

from __future__ import annotations

from typing import Any

from app.db.supabase import vector_search_chunks


def search(
    query: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Embed the query text and run vector search.

    Args:
        query: The raw query text to embed and search for.
        filters: Optional metadata filters (e.g. {"module": "watch"}).
        top_k: Number of results to return.
    """
    from app.ai.embeddings import embed_text

    embedding = embed_text(query)
    if not embedding:
        return []
    return vector_search_chunks(embedding, top_k=top_k, filters=filters)
