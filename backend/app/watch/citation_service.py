"""Citation service — build source citations from ranked results."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def build_citations(ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract source citations from ranked results.

    Returns a list of unique citation dicts.
    """
    seen_urls: set[str] = set()
    citations: list[dict[str, Any]] = []

    for item in ranked:
        if item["type"] in ("update", "structured"):
            update = item.get("update_data", {})
            docs = update.get("documents") or {}
            sources = docs.get("sources") or {}

            source_url = sources.get("url", "")
            if source_url and source_url not in seen_urls:
                seen_urls.add(source_url)
                citations.append({
                    "title": docs.get("title") or update.get("title", "Untitled"),
                    "url": source_url,
                    "source_name": sources.get("name", "Government Source"),
                    "published_date": str(update.get("published_date", "")) or None,
                    "last_verified": str(update.get("last_verified", "")) or None,
                })
        elif item["type"] == "vector":
            # Vector chunks don't directly carry source info
            # but their metadata might reference an update
            pass

    return citations
