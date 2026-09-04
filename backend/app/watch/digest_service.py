"""Generate pre-computed topic digests after monitoring cycles.

Topic digests run the full RAG pipeline once per hot topic and store the
results in the topic_digests table so the frontend can serve them instantly
(with zero AI cost per view and no dependence on the embedding quota).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# Hot topics — curated queries regenerated after every monitoring cycle.
TOPIC_QUERIES: list[tuple[str, str]] = [
    ("Petrol Prices", "What are the latest petrol price updates in Pakistan?"),
    (
        "New Taxes",
        "What new taxes or tax changes have been announced in Pakistan recently?",
    ),
    (
        "Notifications & Circulars",
        "What are the latest government notifications and circulars in Pakistan?",
    ),
    ("Education", "What are the latest education policy updates in Pakistan?"),
    (
        "Schemes & Scholarships",
        "What new government schemes or scholarships have been announced in Pakistan?",
    ),
    (
        "Banking & Finance",
        "What are the latest banking and finance regulations or SBP announcements?",
    ),
]


# RAG answers beginning with this marker mean the verifier could not support
# the answer from monitored sources (watch_service._empty_response).
_REFUSAL_MARKER = "I could not verify"


def generate_topic_digests() -> list[dict[str, Any]]:
    """Run the RAG pipeline for each hot topic and upsert the digest row.

    Hot topics must always carry current info, so when the RAG pipeline
    declines to answer (refusal marker), the web fallback fills in.
    """
    from app.db.supabase import upsert_topic_digest
    from app.watch.watch_service import query_answer

    results: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()

    for topic, query in TOPIC_QUERIES:
        try:
            response = query_answer(query)

            # query_answer's web fallback marks its responses via warnings
            model = (
                "web"
                if any("web search" in str(w) for w in (response.get("warnings") or []))
                else "rag"
            )

            # Safety net: hot topics should never show a refusal (e.g. when
            # query_answer's own web attempt failed) — retry once here.
            if (response.get("answer") or "").startswith(_REFUSAL_MARKER):
                try:
                    from app.watch.web_answer_service import get_or_fetch_web_answer

                    web_response = get_or_fetch_web_answer(query)
                    if web_response and web_response.get("answer"):
                        logger.info("RAG refused %r — using web fallback", topic)
                        response = web_response
                        model = "web"
                except Exception as exc:
                    logger.warning("Web fallback for digest %s failed: %s", topic, exc)

            update_ids = [
                u.get("id")
                for u in (response.get("updates") or [])
                if isinstance(u, dict) and u.get("id")
            ]
            digest = {
                "topic": topic,
                "query": query,
                "answer": response.get("answer"),
                "what_changed": response.get("what_changed"),
                "who_affected": response.get("who_affected"),
                "effective_date": response.get("effective_date"),
                "confidence": response.get("confidence", "medium"),
                "update_ids": update_ids,
                "sources": response.get("sources", []),
                "model": model,
                "generated_at": now,
            }
            try:
                upsert_topic_digest(digest)
                logger.info("Digest stored: %s", topic)
            except Exception as exc:
                logger.error("Failed to store digest %s: %s", topic, exc)
            results.append(digest)
        except Exception as exc:
            logger.error("Digest generation failed for %s: %s", topic, exc)

    return results


def topic_digests_endpoint() -> dict[str, Any]:
    """Handle GET /api/watch/topics — return all topic digests newest first."""
    from app.db.supabase import get_topic_digests

    try:
        digests = get_topic_digests()
    except Exception as exc:
        logger.error("Failed to fetch topic digests: %s", exc)
        digests = []
    return {"module": "watch", "topics": digests, "count": len(digests)}
