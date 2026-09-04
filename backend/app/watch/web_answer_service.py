"""Out-of-DB query fallback with cache + grounded web search.

Pipeline:
    1. Cache lookup — cosine similarity on question_embedding in web_answers
       (skipped if embedding quota is exhausted)
    2. Gemini google_search grounding (best quality citations; fails on quota)
    3. Web search (Serper → DuckDuckGo fallback) + LLM generation via the
       router chain (Groq fallback if Gemini is also quota-exhausted)

Stores every freshly-generated answer in the web_answers cache table so
subsequent similar questions hit the cache.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _parse_embedding(raw) -> np.ndarray | None:
    """Parse an embedding that may be a list or a stringified JSON array."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return np.array(raw, dtype=np.float64)
    try:
        return np.array(json.loads(raw), dtype=np.float64)
    except Exception:
        try:
            stripped = raw.strip("[]")
            return np.array(
                [float(x.strip()) for x in stripped.split(",") if x.strip()],
                dtype=np.float64,
            )
        except Exception:
            return None


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _find_cached(query: str, settings):
    """Look up a similar cached web answer by embedding similarity."""
    try:
        from app.ai.embeddings import embed_text

        q_emb = embed_text(query)
    except Exception as exc:
        logger.warning("Cannot embed query for cache lookup: %s", exc)
        return None

    from app.db.supabase import get_recent_web_answers

    try:
        rows = get_recent_web_answers(settings.web_answer_ttl_hours)
    except Exception as exc:
        logger.warning("Cache lookup failed: %s", exc)
        return None

    q = _parse_embedding(q_emb)
    best_score, best_row = 0.0, None
    for row in rows:
        emb = _parse_embedding(row.get("question_embedding"))
        if emb is None:
            continue
        score = _cosine(q, emb)
        if score > best_score:
            best_score, best_row = score, row

    if best_score >= settings.web_answer_sim_threshold:
        logger.info(
            "Cache hit (score=%.3f): %s", best_score, best_row.get("question")
        )
        return best_row
    return None


# ---------------------------------------------------------------------------
# Response building
# ---------------------------------------------------------------------------

def _build_web_response(
    row_or_result: dict[str, Any],
    cached: bool = False,
    web_sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    sources = []
    for s in web_sources or []:
        sources.append(
            {
                "title": s.get("title"),
                "url": s.get("url"),
                "source_name": s.get("source_name", "Web"),
                "last_verified": None,
                "published_date": None,
            }
        )
    warning = (
        "Answer from cached web search."
        if cached
        else "Answer from live web search — not from PakWatch's monitored sources."
    )
    last_verified = (
        row_or_result.get("created_at")
        if cached
        else datetime.now(timezone.utc).isoformat()
    )
    return {
        "module": "watch",
        "answer": row_or_result.get("answer") or "",
        "updates": [],
        "sources": sources,
        "what_changed": row_or_result.get("what_changed"),
        "who_affected": row_or_result.get("who_affected"),
        "effective_date": row_or_result.get("effective_date"),
        "last_verified": str(last_verified) if last_verified else None,
        "confidence": "medium",
        "warnings": [warning],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_or_fetch_web_answer(query: str, language: str = "english") -> dict[str, Any] | None:
    """Return a cached or freshly-generated web-search answer. Returns None on failure."""
    from app.config import get_settings

    settings = get_settings()

    # 1. Cache lookup (best-effort — skipped if embeddings are quota-blocked)
    cached = _find_cached(query, settings)
    if cached:
        try:
            sources = cached.get("sources") or []
        except Exception:
            sources = []
        return _build_web_response(cached, cached=True, web_sources=sources)

    # 2. Gemini grounded search (best quality citations)
    try:
        from app.watch.web_answer import generate_web_answer

        result = generate_web_answer(query, language=language)
        return _store_and_respond(query, result)
    except Exception as exc:
        logger.warning("Gemini grounded search failed: %s — falling back to web search", exc)

    # 3. Web search (Serper → DDG) + LLM generation via the router chain
    return _web_search_answer(query, language=language)


# ---------------------------------------------------------------------------
# Web-search fallback
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are PakWatch, an assistant that tracks Pakistani government updates. "
    "The search results below were fetched from the live web. Answer the user's "
    "question concisely (3-6 sentences), relying on the provided sources. "
    "Prefer official .gov.pk sources and reputable news outlets. Include dates "
    "where available. If the results do not answer the question, say so briefly.\n\n"
    "Respond with ONLY a JSON object (no markdown fences) with fields:\n"
    '{"answer": "...", "what_changed": "... or null", '
    '"who_affected": "... or null", "effective_date": "... or null"}'
)

_LANGUAGE_HINTS = {
    "urdu": " The user asked in Urdu script — reply in Urdu.",
    "roman_urdu": " The user asked in Roman Urdu (Urdu in English letters) — reply in Roman Urdu.",
    "english": "",
}


def _web_search_answer(query: str, language: str = "english") -> dict[str, Any] | None:
    """Fallback path: web search (Serper → DDG) + LLM generation via the router chain."""
    from app.watch.web_search import fetch_page_text, search_web
    from app.ai.llm_router import call_llm_json

    results = search_web(query, max_results=5)
    if not results:
        logger.warning("Web search returned no results for: %s", query)
        return None

    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(f"[{i}] {r['title']}\n    {r['url']}\n    {r['snippet']}")
    # Enrich top 2 results with best-effort page content
    for r in results[:2]:
        page_text = fetch_page_text(r["url"], max_chars=2000)
        if page_text:
            blocks.append(f"\n--- Page content: {r['title']} ---\n{page_text}\n")

    context = "\n\n".join(blocks)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT + _LANGUAGE_HINTS.get(language, "")},
        {
            "role": "user",
            "content": f"Question: {query}\n\nSearch results:\n{context}",
        },
    ]
    try:
        parsed = call_llm_json(messages)
    except Exception as exc:
        logger.error("LLM generation from DDG context failed: %s", exc)
        return None

    if parsed.get("error"):
        logger.warning("LLM parse error from DDG context: %s", parsed.get("error"))
        return None

    parsed["web_sources"] = [
        {"title": r["title"], "url": r["url"]} for r in results
    ]
    return _store_and_respond(query, parsed)


# ---------------------------------------------------------------------------
# Cache persistence
# ---------------------------------------------------------------------------

def _store_and_respond(query: str, result: dict[str, Any]) -> dict[str, Any]:
    web_sources = result.get("web_sources") or []

    # Best-effort: embed the question so future similar queries hit the cache.
    q_emb: list[float] | None = None
    try:
        from app.ai.embeddings import embed_text

        q_emb = embed_text(query)
    except Exception:
        pass  # embedding quota may be exhausted — that's OK

    try:
        from app.db.supabase import insert_web_answer

        insert_web_answer(
            {
                "question": query,
                "question_embedding": q_emb,
                "answer": result.get("answer"),
                "what_changed": result.get("what_changed"),
                "who_affected": result.get("who_affected"),
                "effective_date": result.get("effective_date"),
                "sources": web_sources,
                "model": result.get("model"),
            }
        )
    except Exception as exc:
        logger.warning("Failed to store web answer in cache: %s", exc)

    return _build_web_response(result, cached=False, web_sources=web_sources)
