"""Rank and combine retrieval results from multiple sources."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Importance weights
_IMPORTANCE_WEIGHT = {"high": 1.0, "medium": 0.7, "low": 0.4}


def rank_results(
    vector_chunks: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
    structured_results: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Combine and rank results from vector search, keyword search, and structured search.

    Returns:
        (ranked_results, context_string)
    """
    seen_ids: set[str] = set()
    ranked: list[dict[str, Any]] = []

    # 1. Add vector search results (already scored by similarity)
    for chunk in vector_chunks:
        doc_id = str(chunk.get("document_id", ""))
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)

        similarity = chunk.get("similarity", 0.0)
        meta = chunk.get("metadata", {}) or {}
        importance = meta.get("importance", "medium")

        score = similarity * _IMPORTANCE_WEIGHT.get(importance, 0.5)
        # Boost by freshness if available
        score *= _freshness_boost(meta)

        ranked.append({
            "type": "vector",
            "score": score,
            "content": chunk.get("content", ""),
            "chunk": chunk,
            "document_id": doc_id,
        })

    # 2. Add keyword search results
    for update in keyword_results:
        update_id = str(update.get("id", ""))
        if update_id in seen_ids:
            continue
        seen_ids.add(update_id)

        importance = update.get("importance", "medium")
        score = 0.5 * _IMPORTANCE_WEIGHT.get(importance, 0.5)
        score *= _freshness_boost_from_update(update)

        ranked.append({
            "type": "update",
            "score": score,
            "content": update.get("summary", "") or update.get("title", ""),
            "update_data": update,
            "update_id": update_id,
        })

    # 3. Add structured search results
    if structured_results:
        for update in structured_results:
            update_id = str(update.get("id", ""))
            if update_id in seen_ids:
                continue
            seen_ids.add(update_id)

            importance = update.get("importance", "medium")
            score = 0.4 * _IMPORTANCE_WEIGHT.get(importance, 0.5)
            score *= _freshness_boost_from_update(update)

            ranked.append({
                "type": "structured",
                "score": score,
                "content": update.get("summary", "") or update.get("title", ""),
                "update_data": update,
                "update_id": update_id,
            })

    # Sort by score descending
    ranked.sort(key=lambda r: r["score"], reverse=True)

    # Build context string
    context = _build_context(ranked)

    return ranked, context


def _build_context(ranked: list[dict[str, Any]]) -> str:
    """Build a context string from ranked results for the LLM."""
    blocks: list[str] = []

    for i, item in enumerate(ranked[:10], 1):  # Top 10
        if item["type"] == "vector":
            chunk = item.get("chunk", {})
            meta = chunk.get("metadata", {}) or {}
            blocks.append(
                f"--- SOURCE {i} [DOCUMENT CHUNK — similarity={item['score']:.3f}] ---\n"
                f"Category: {meta.get('category', 'unknown')}\n"
                f"Province: {meta.get('province', 'unknown')}\n"
                f"Department: {meta.get('department', 'unknown')}\n"
                f"Content:\n{item['content']}"
            )
        elif item["type"] in ("update", "structured"):
            update = item.get("update_data", {})
            source_info = ""
            docs = update.get("documents") or {}
            if docs:
                sources = docs.get("sources") or {}
                if sources:
                    source_info = f"\nOfficial Source: {sources.get('name', 'Unknown')} ({sources.get('url', '')})"

            blocks.append(
                f"--- SOURCE {i} [GOVERNMENT UPDATE — score={item['score']:.3f}] ---\n"
                f"Title: {update.get('title', 'Untitled')}\n"
                f"Category: {update.get('category', 'unknown')}\n"
                f"Organization: {update.get('organization', 'unknown')}\n"
                f"Department: {update.get('department', 'unknown')}\n"
                f"Province: {update.get('province', 'unknown')}\n"
                f"Importance: {update.get('importance', 'unknown')}\n"
                f"Published: {update.get('published_date', 'unknown')}\n"
                f"Last Verified: {update.get('last_verified', 'unknown')}\n"
                f"Summary: {update.get('summary', 'N/A')}\n"
                f"What Changed: {update.get('what_changed', 'N/A')}\n"
                f"Details: {update.get('important_details', [])}"
                f"{source_info}"
            )

    return "\n\n".join(blocks)


def _freshness_boost(meta: dict) -> float:
    """Slight boost for chunks with recent metadata."""
    return 1.0  # Placeholder — chunks don't always have dates


def _freshness_boost_from_update(update: dict) -> float:
    """Boost score based on how recent the update is."""
    pub_date = update.get("published_date")
    if not pub_date:
        return 0.8  # Slight penalty for unknown date

    try:
        if isinstance(pub_date, str):
            pub = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        else:
            return 0.8

        now = datetime.now(timezone.utc)
        days_old = (now - pub).days

        if days_old <= 7:
            return 1.2  # Very fresh — boost
        elif days_old <= 30:
            return 1.0  # Recent — normal
        elif days_old <= 90:
            return 0.8  # Getting older
        else:
            return 0.6  # Old — penalize
    except Exception:
        return 0.8
