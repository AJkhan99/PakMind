"""YouTube video search — finds relevant government service tutorial videos.

Uses DuckDuckGo to search YouTube (free, no API key needed).
Strictly filters for tutorial/guide content only — excludes news and politics.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Keywords that indicate irrelevant content (news, politics, entertainment)
_IRRELEVANT_KEYWORDS = [
    "news", "update", "breaking", "headline", "bulletin",
    "war", "attack", "conflict", "crisis", "election",
    "samsung", "cricket", "match", "score",
    "sana", "geo news", "ary news", "dunya news", "samma", "bol news",
    "express news", "hum news", "aaj news", "24 news",
    "talk show", "debate", "interview", "press conference",
    "trailer", "song", "music", "drama", "episode",
    "live stream", "live now",
]

# Keywords that indicate useful tutorial/guide content
_USEFUL_KEYWORDS = [
    "procedure", "how to", "step by step", "guide", "tutorial",
    "apply", "application", "process", "tarika", "kaise",
    "requirements", "documents", "fee", "online",
    "complete guide", "full guide", "explained",
]


def search_youtube(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    """Search YouTube for Pakistani government service tutorial videos.

    Only returns results that look like actual tutorials/guides.
    News, politics, and entertainment content is filtered out.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("ddgs not installed — YouTube search unavailable")
            return []

    # Targeted search: only tutorials and guides
    search_query = f"site:youtube.com/watch {query} Pakistan procedure guide how to apply Urdu"

    candidates: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(search_query, max_results=max_results * 4):
                url = r.get("href", "")
                title = r.get("title", "")
                snippet = r.get("body", "")

                # Only include actual YouTube video watch pages
                if "youtube.com/watch" not in url and "youtu.be/" not in url:
                    continue

                # Filter out irrelevant content
                title_lower = title.lower()
                snippet_lower = snippet.lower()
                combined = title_lower + " " + snippet_lower

                # Check for irrelevant keywords
                if any(kw in combined for kw in _IRRELEVANT_KEYWORDS):
                    continue

                # Prefer results with useful keywords
                usefulness_score = sum(1 for kw in _USEFUL_KEYWORDS if kw in combined)

                # Clean up title
                title = re.sub(r"\s*[-–]\s*YouTube$", "", title)

                candidates.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source_name": "YouTube",
                    "trusted": False,
                    "type": "video",
                    "usefulness": usefulness_score,
                })

    except Exception as exc:
        logger.error("YouTube search failed: %s", exc)
        return []

    # Sort by usefulness (most tutorial-like first) and take top N
    candidates.sort(key=lambda c: c["usefulness"], reverse=True)
    results = candidates[:max_results]

    # If no result has at least 1 useful keyword, return empty (not relevant enough)
    if results and all(r["usefulness"] == 0 for r in results):
        logger.info("YouTube results filtered out — none contained tutorial keywords")
        return []

    # Remove the internal usefulness score before returning
    for r in results:
        del r["usefulness"]

    logger.info("YouTube search returned %d relevant videos", len(results))
    return results


def search_youtube_for_service(
    service: str,
    province: str | None = None,
) -> list[dict[str, Any]]:
    """Targeted YouTube search for a specific government service tutorial.

    Only returns videos whose title contains the service name,
    ensuring relevance.
    """
    parts = [service, "Pakistan"]
    if province:
        parts.append(province)
    parts.append("procedure apply kaise")

    query = " ".join(parts)
    results = search_youtube(query, max_results=6)

    # Strict filter: title must contain the service name (case-insensitive)
    service_lower = service.lower()
    service_words = set(service_lower.split())
    filtered = []
    for r in results:
        title_lower = r["title"].lower()
        # Title must contain the service name or at least 2 of its key words
        if service_lower in title_lower:
            filtered.append(r)
        elif sum(1 for w in service_words if w in title_lower and len(w) > 3) >= 2:
            filtered.append(r)

    return filtered[:3]


def build_youtube_context(videos: list[dict[str, Any]]) -> str:
    """Build a context string from YouTube search results."""
    if not videos:
        return ""

    blocks: list[str] = []
    for i, v in enumerate(videos, 1):
        blocks.append(
            f"--- VIDEO SOURCE {i} [SUPPLEMENTARY — NOT OFFICIAL] ---\n"
            f"Title: {v['title']}\n"
            f"URL: {v['url']}\n"
            f"Description: {v['snippet']}\n"
            f"Note: This is a community video, not an official government source."
        )
    return "\n\n".join(blocks)
