"""Retrieval service — multi-phase retrieval for PakWatch.

Flow: parse -> parallel(vector + keyword + structured) -> rank -> context
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.watch import vector_search, keyword_search, ranking
from app.watch.query_parser import parse_query, build_search_keywords
from app.db.supabase import search_updates

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    parsed_query: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    """Run multi-phase retrieval and return ranked results + context.

    Returns:
        (ranked_results, context_string, source_metadata)
    """
    if parsed_query is None:
        parsed_query = parse_query(query)

    search_keywords = build_search_keywords(query, parsed_query)
    search_text = " ".join(search_keywords) if search_keywords else query

    category = parsed_query.get("category")
    province = parsed_query.get("province")

    logger.info("Parsed: intent=%s, category=%s, province=%s, topic=%s",
                parsed_query.get("intent"), category, province, parsed_query.get("topic"))

    # Parallel search
    vector_chunks: list[dict[str, Any]] = []
    keyword_results: list[dict[str, Any]] = []
    structured_results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures: dict[Any, str] = {}

        # Vector search
        futures[pool.submit(_do_vector_search, query, parsed_query)] = "vector"

        # Keyword search
        futures[pool.submit(_do_keyword_search, search_text)] = "keyword"

        # Structured search
        futures[pool.submit(_do_structured_search, parsed_query)] = "structured"

        for future in as_completed(futures):
            label = futures[future]
            try:
                result = future.result()
                if label == "vector":
                    vector_chunks = result
                elif label == "keyword":
                    keyword_results = result
                elif label == "structured":
                    structured_results = result
            except Exception as exc:
                logger.warning("%s search failed: %s", label, exc)

    logger.info("Retrieval: %d vector, %d keyword, %d structured",
                len(vector_chunks), len(keyword_results), len(structured_results))

    # Rank and combine
    ranked, context = ranking.rank_results(vector_chunks, keyword_results, structured_results)

    # Source metadata
    has_updates = any(r["type"] in ("update", "structured") for r in ranked)
    source_meta = {
        "has_updates": has_updates,
        "update_count": sum(1 for r in ranked if r["type"] in ("update", "structured")),
        "chunk_count": sum(1 for r in ranked if r["type"] == "vector"),
    }

    return ranked, context, source_meta


def _do_vector_search(query: str, parsed_query: dict) -> list[dict[str, Any]]:
    try:
        # Only filter by module — strict category/province filters can exclude
        # relevant results (e.g. query says "policy" but the update is an
        # announcement); ranking already boosts on metadata matches.
        return vector_search.search(query, filters={"module": "watch"})
    except Exception as exc:
        logger.warning("Vector search failed: %s", exc)
        return []


def _do_keyword_search(search_text: str) -> list[dict[str, Any]]:
    try:
        return keyword_search.search(search_text)
    except Exception as exc:
        logger.warning("Keyword search failed: %s", exc)
        return []


def _do_structured_search(parsed_query: dict) -> list[dict[str, Any]]:
    try:
        results = search_updates(
            title=parsed_query.get("topic"),
            category=parsed_query.get("category"),
            province=parsed_query.get("province"),
            department=parsed_query.get("department"),
            limit=5,
        )
        if results:
            return results
        # Relaxed fallback — an exact category+province match is often too
        # strict when the corpus is small; try the single strongest filter
        if parsed_query.get("province"):
            results = search_updates(province=parsed_query["province"], limit=5)
        if not results and parsed_query.get("category"):
            results = search_updates(category=parsed_query["category"], limit=5)
        return results
    except Exception as exc:
        logger.warning("Structured search failed: %s", exc)
        return []
