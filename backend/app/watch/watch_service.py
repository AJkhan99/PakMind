"""Watch service — orchestrates the full query pipeline for PakWatch.

Pipeline: parse -> retrieve -> generate -> verify -> cite
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.watch.prompts import generate_answer
from app.watch.verifier import verify_and_refine
from app.watch.retrieval_service import retrieve
from app.watch.citation_service import build_citations
from app.watch.query_parser import parse_query
from app.db.supabase import search_updates, get_latest_updates, get_update_categories

logger = logging.getLogger(__name__)

# Answers beginning with this marker mean the verifier could not support the
# answer from monitored sources — the question is likely out-of-DB territory
# (same text as _empty_response below).
_REFUSAL_MARKER = "I could not verify"


def search_updates_api(query: str) -> dict[str, Any]:
    """Handle the /api/watch/search endpoint — return updates without AI generation."""
    parsed = parse_query(query)
    ranked, _, _ = retrieve(query, parsed)

    updates: list[dict[str, Any]] = []
    for item in ranked:
        if item["type"] in ("update", "structured"):
            u = item.get("update_data", {})
            docs = u.get("documents") or {}
            sources = docs.get("sources") or {}
            updates.append({
                "id": u.get("id"),
                "title": u.get("title"),
                "category": u.get("category"),
                "organization": u.get("organization"),
                "department": u.get("department"),
                "province": u.get("province"),
                "importance": u.get("importance"),
                "summary": u.get("summary"),
                "published_date": str(u.get("published_date") or "") or None,
                "source_name": sources.get("name"),
                "source_url": sources.get("url"),
                "relevance_score": item.get("score"),
            })
        elif item["type"] == "vector":
            chunk = item.get("chunk", {})
            meta = chunk.get("metadata", {}) or {}
            updates.append({
                "id": None,
                "title": meta.get("title", "Document Excerpt"),
                "category": meta.get("category"),
                "organization": None,
                "department": meta.get("department"),
                "province": meta.get("province"),
                "importance": meta.get("importance"),
                "summary": chunk.get("content", "")[:200],
                "published_date": None,
                "source_name": None,
                "source_url": None,
                "relevance_score": item.get("score"),
            })

    return {
        "module": "watch",
        "query": query,
        "parsed": parsed,
        "results": updates[:10],
    }


def query_answer(query: str) -> dict[str, Any]:
    """Handle the /api/watch/query endpoint — full RAG pipeline with AI answer."""
    start = time.time()

    # Step 1: Parse query
    parsed = parse_query(query)
    language = parsed.get("language", "english")

    # Step 2: Retrieve
    ranked, context, source_meta = retrieve(query, parsed)
    logger.info("Retrieval: %d results, context=%d chars (%.1fs)",
                len(ranked), len(context), time.time() - start)

    if not context.strip():
        logger.warning("No context retrieved for query: %s — trying web fallback", query)
        try:
            from app.watch.web_answer_service import get_or_fetch_web_answer

            web_response = get_or_fetch_web_answer(query, language=language)
            if web_response:
                return web_response
        except Exception as exc:
            logger.error("Web fallback failed: %s", exc)
        return _empty_response(language)

    # Step 3: Generate answer
    try:
        draft = generate_answer(context, query, language=language)
        logger.info("Draft generated (%.1fs total)", time.time() - start)
    except Exception as exc:
        # All LLM providers failed — the web fallback may still answer (it
        # uses its own provider chain), so try it before giving up.
        logger.error("Answer generation failed: %s — trying web fallback", exc)
        try:
            from app.watch.web_answer_service import get_or_fetch_web_answer

            web_response = get_or_fetch_web_answer(query, language=language)
            if web_response and web_response.get("answer"):
                return web_response
        except Exception as web_exc:
            logger.error("Web fallback failed: %s", web_exc)
        return _error_response(str(exc))

    # Step 4: Verify
    try:
        verified = verify_and_refine(context, draft)
        logger.info("Verification complete (%.1fs total)", time.time() - start)
    except Exception as exc:
        logger.warning("Verification failed: %s — using draft", exc)
        verified = draft
        verified.setdefault("warnings", []).append("Cross-verification was unavailable.")

    # Step 4.5: Web fallback when verification refuses — the monitored sources
    # cannot answer this question, so fetch it from the live web (cached).
    if (verified.get("answer") or "").startswith(_REFUSAL_MARKER):
        logger.warning("Verification refused to answer: %s — trying web fallback", query)
        try:
            from app.watch.web_answer_service import get_or_fetch_web_answer

            web_response = get_or_fetch_web_answer(query, language=language)
            if web_response and web_response.get("answer"):
                return web_response
        except Exception as exc:
            logger.error("Web fallback failed: %s", exc)

    # Step 5: Build citations
    citations = build_citations(ranked)

    # Step 6: Extract last_verified from results
    last_verified = None
    for item in ranked:
        if item["type"] in ("update", "structured"):
            lv = (item.get("update_data") or {}).get("last_verified")
            if lv:
                last_verified = str(lv)
                break

    # Step 7: Build warnings
    warnings = verified.get("warnings") or []
    if not citations:
        warnings.append("No official source citations could be linked to this response.")

    elapsed = time.time() - start
    logger.info("Full pipeline complete in %.1fs", elapsed)

    return {
        "module": "watch",
        "answer": verified.get("answer") or "",
        "updates": verified.get("updates") or [],
        "sources": citations,
        "what_changed": verified.get("what_changed"),
        "who_affected": verified.get("who_affected"),
        "effective_date": verified.get("effective_date"),
        "last_verified": last_verified,
        "confidence": verified.get("confidence") or "medium",
        "warnings": warnings,
    }


def latest_updates(
    limit: int = 10,
    category: str | None = None,
    province: str | None = None,
) -> dict[str, Any]:
    """Handle GET /api/watch/latest — return newest updates."""
    updates = get_latest_updates(limit=limit, category=category, province=province)

    results = []
    for u in updates:
        docs = u.get("documents") or {}
        sources = docs.get("sources") or {}
        results.append({
            "id": u.get("id"),
            "title": u.get("title"),
            "category": u.get("category"),
            "organization": u.get("organization"),
            "department": u.get("department"),
            "province": u.get("province"),
            "importance": u.get("importance"),
            "summary": u.get("summary"),
            "what_changed": u.get("what_changed"),
            "published_date": str(u.get("published_date") or "") or None,
            "last_verified": str(u.get("last_verified") or "") or None,
            "source_name": sources.get("name"),
            "source_url": sources.get("url"),
        })

    return {
        "module": "watch",
        "updates": results,
        "count": len(results),
    }


def categories_endpoint() -> dict[str, Any]:
    """Handle GET /api/watch/categories."""
    cats = get_update_categories()
    return {
        "module": "watch",
        "categories": cats,
    }


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def _empty_response(language: str = "english") -> dict[str, Any]:
    messages = {
        "english": (
            "I could not verify an official government announcement confirming this "
            "from the sources currently available to PakWatch. Try rephrasing your "
            "question, or check back later after the next monitoring cycle."
        ),
        "urdu": (
            "معذرت، اس سوال کا جواب فی الحال دستیاب ذرائع سے تصدیق نہیں ہو سکا۔ "
            "براہ کرم سوال دوبارہ لکھیں یا اگلے مانیٹرنگ سائیکل کے بعد دوبارہ دیکھیں۔"
        ),
        "roman_urdu": (
            "Maaf kijiye, is sawal ka jawab abhi available sources se verify nahi ho "
            "saka. Barah-e-karam sawal dobara likhein ya agle monitoring cycle ke "
            "baad dubara check karein."
        ),
    }
    return {
        "module": "watch",
        "answer": messages.get(language, messages["english"]),
        "updates": [],
        "sources": [],
        "what_changed": None,
        "who_affected": None,
        "effective_date": None,
        "last_verified": None,
        "confidence": "low",
        "warnings": ["No relevant government updates found in the database."],
    }


def _error_response(error_msg: str) -> dict[str, Any]:
    return {
        "module": "watch",
        "answer": "An error occurred while generating the answer. Please try again.",
        "updates": [],
        "sources": [],
        "what_changed": None,
        "who_affected": None,
        "effective_date": None,
        "last_verified": None,
        "confidence": "low",
        "warnings": [f"Error: {error_msg}"],
    }
