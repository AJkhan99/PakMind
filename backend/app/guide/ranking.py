"""Result ranking — merges vector, keyword, and structured search results."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from dateutil import parser as dateparser

logger = logging.getLogger(__name__)


def rank_results(
    vector_chunks: list[dict[str, Any]],
    keyword_services: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    """Merge and rank results from different retrieval sources.

    Returns:
        - A list of context blocks (strings) ordered by relevance.
        - A combined context string for the LLM.
    """
    scored: list[dict[str, Any]] = []

    # Score vector chunks
    for chunk in vector_chunks:
        score = chunk.get("similarity", 0.0)
        # Boost by metadata trust signals
        meta = chunk.get("metadata") or {}
        if meta.get("module") == "guide":
            score *= 1.1  # small boost for guide-module content

        scored.append({
            "type": "chunk",
            "score": score,
            "content": chunk.get("content", ""),
            "document_id": chunk.get("document_id"),
            "metadata": meta,
        })

    # Score keyword-matched services
    for svc in keyword_services:
        score = 0.6  # base score for exact keyword match
        # Boost by trust_level of linked source (nested via documents → sources)
        doc = svc.get("documents") or {}
        source = doc.get("sources") or {}
        trust = source.get("trust_level", 3)
        score *= trust / 5.0

        # Boost by freshness
        last_verified = doc.get("last_verified") or svc.get("last_verified")
        if last_verified:
            try:
                dt = dateparser.parse(str(last_verified))
                if dt:
                    days_old = (datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)).days
                    freshness = max(0.5, 1.0 - days_old / 365.0)
                    score *= freshness
            except Exception:
                pass

        # Build a text block from the structured service
        content = _service_to_text(svc)
        scored.append({
            "type": "service",
            "score": score,
            "content": content,
            "service_id": svc.get("id"),
            "source": source,
            "document": doc,
            "service_data": svc,
        })

    # Sort by score descending
    scored.sort(key=lambda r: r["score"], reverse=True)

    logger.info("Ranking: %d chunks + %d services = %d total scored", len(vector_chunks), len(keyword_services), len(scored))

    # Deduplicate similar content
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in scored:
        key = item["content"][:200]
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    # Build context string (top 8 blocks to keep prompt manageable)
    context_blocks: list[str] = []
    for i, item in enumerate(deduped[:8], 1):
        header = f"--- SOURCE {i} (relevance: {item['score']:.2f}) ---"
        context_blocks.append(f"{header}\n{item['content']}")

    context = "\n\n".join(context_blocks)
    return deduped, context


def _service_to_text(svc: dict[str, Any]) -> str:
    """Convert a government_services record to a readable text block."""
    parts: list[str] = []
    parts.append(f"Service: {svc.get('name', 'Unknown')}")
    if svc.get("description"):
        parts.append(f"Description: {svc['description']}")
    if svc.get("department"):
        parts.append(f"Department: {svc['department']}")
    if svc.get("province"):
        parts.append(f"Province: {svc['province']}")
    if svc.get("city"):
        parts.append(f"City: {svc['city']}")
    if svc.get("eligibility"):
        parts.append(f"Eligibility: {svc['eligibility']}")

    reqs = svc.get("requirements")
    if reqs:
        if isinstance(reqs, list):
            parts.append("Required Documents:\n" + "\n".join(f"  - {r}" for r in reqs))
        else:
            parts.append(f"Required Documents: {reqs}")

    steps = svc.get("steps")
    if steps:
        if isinstance(steps, list):
            parts.append("Steps:\n" + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps)))
        else:
            parts.append(f"Steps: {steps}")

    if svc.get("fee"):
        parts.append(f"Fee: {svc['fee']}")
    if svc.get("processing_time"):
        parts.append(f"Processing Time: {svc['processing_time']}")
    if svc.get("application_method"):
        parts.append(f"Application Method: {svc['application_method']}")
    if svc.get("application_url"):
        parts.append(f"Application URL: {svc['application_url']}")

    contact = svc.get("contact_info")
    if contact:
        if isinstance(contact, dict):
            parts.append("Contact: " + ", ".join(f"{k}: {v}" for k, v in contact.items() if v))
        else:
            parts.append(f"Contact: {contact}")

    doc = svc.get("documents") or {}
    if doc.get("url"):
        parts.append(f"Source URL: {doc['url']}")
    if doc.get("last_verified"):
        parts.append(f"Last Verified: {doc['last_verified']}")

    source = doc.get("sources") or {}
    if source.get("name"):
        parts.append(f"Source: {source['name']}")

    return "\n".join(parts)
