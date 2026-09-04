"""Guide service — orchestrates the full query pipeline.

Smart flow: parse → retrieve (with deep scraping) → generate → verify → auto-enrich DB

Key philosophy: ALWAYS return useful information. If web sources have the answer,
use them — never return "not found" when content exists.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.ai.llm_router import call_llm_json
from app.guide.verifier import verify_and_refine
from app.guide.retrieval_service import retrieve
from app.guide.citation_service import build_citations
from app.guide.query_parser import parse_query
from app.guide.feedback_service import log_query
from app.guide.prompts import build_answer_prompt

logger = logging.getLogger(__name__)


def search_services(query: str) -> dict[str, Any]:
    """Handle the /api/guide/search endpoint logic.

    Returns matching services without AI answer generation.
    """
    parsed = parse_query(query)
    ranked, _, _meta = retrieve(query, parsed)

    services: list[dict[str, Any]] = []
    for item in ranked:
        if item.get("type") == "service":
            svc = item.get("service_data", {})
            services.append({
                "id": svc.get("id"),
                "name": svc.get("name"),
                "description": svc.get("description"),
                "department": svc.get("department"),
                "province": svc.get("province"),
                "city": svc.get("city"),
                "relevance_score": item.get("score"),
            })

    return {
        "module": "guide",
        "query": query,
        "parsed": parsed,
        "results": services[:10],
    }


def query_answer(query: str) -> dict[str, Any]:
    """Handle the /api/guide/query endpoint logic.

    Optimized pipeline with smart fallback:
      parse (~0ms) → retrieve (~2-5s) → generate (~2-3s) → verify (~2s) → auto-enrich
    Total: 4-10s depending on whether deep scraping was needed.
    """
    start = time.time()

    # Step 1: Parse the query (FAST — no LLM call, ~0ms)
    parsed = parse_query(query)
    language = parsed.get("language", "english")

    # Step 2: Smart retrieval (parallel + deep scraping fallback)
    ranked, context, source_meta = retrieve(query, parsed)
    logger.info("Retrieval: %d results, context=%d chars, source=%s (%.1fs)",
                len(ranked), len(context), source_meta.get("source_type"), time.time() - start)

    if not context.strip():
        # Truly no context at all — even web search returned nothing
        logger.warning("No context retrieved for query: %s", query)
        return _empty_response(query, language)

    # Step 3: Generate answer with primary LLM
    try:
        logger.info("Generating answer with %d chars of context...", len(context))
        messages = build_answer_prompt(context, query, language=language)
        draft = call_llm_json(messages)
        logger.info("Draft generated (%.1fs total)", time.time() - start)
    except Exception as exc:
        logger.error("Answer generation failed: %s", exc)
        return _error_response(str(exc))

    # Step 4: Verify with secondary LLM
    try:
        verified = verify_and_refine(context, draft)
        logger.info("Verification complete (%.1fs total)", time.time() - start)
    except Exception as exc:
        logger.warning("Verification failed: %s — using draft as-is", exc)
        verified = draft
        verified.setdefault("warnings", []).append(
            "Cross-verification was unavailable."
        )

    # Step 5: Override confidence based on source metadata
    # The LLM might set confidence too conservatively — we fix it here
    _adjust_confidence(verified, source_meta, ranked)

    # Step 6: Build citations
    citations = build_citations(ranked)

    # Step 7: Build warnings based on source quality
    warnings = verified.get("warnings") or []
    _add_source_warnings(warnings, source_meta, citations)

    # Step 8: Auto-enrich DB (non-blocking, learn from successful web answers)
    _auto_enrich(query, parsed, verified, ranked, source_meta)

    # Step 9: Extract last_verified from DB results
    last_verified = None
    for item in ranked:
        if item.get("type") == "service":
            doc = (item.get("service_data") or {}).get("documents") or {}
            lv = doc.get("last_verified")
            if lv:
                last_verified = str(lv)
                break

    elapsed = time.time() - start
    logger.info("Full pipeline complete in %.1fs (source_type=%s)", elapsed, source_meta.get("source_type"))

    # Log the query for analytics (non-blocking)
    try:
        log_query(
            query=query,
            parsed_query={
                "service": parsed.get("service"),
                "province": parsed.get("province"),
                "intent": parsed.get("intent"),
                "language": language,
            },
            response_summary=(verified.get("answer") or "")[:200],
            confidence=verified.get("confidence") or "medium",
            sources_count=len(citations),
            response_time_ms=int(elapsed * 1000),
        )
    except Exception:
        pass  # Analytics should never break the main flow

    # Build final response
    return {
        "module": "guide",
        "answer": verified.get("answer") or "",
        "requirements": verified.get("requirements") or [],
        "steps": verified.get("steps") or [],
        "fee": verified.get("fee"),
        "processing_time": verified.get("processing_time"),
        "application_method": verified.get("application_method"),
        "application_url": verified.get("application_url"),
        "contact_info": verified.get("contact_info"),
        "eligibility": verified.get("eligibility"),
        "sources": citations or [],
        "last_verified": last_verified,
        "confidence": verified.get("confidence") or "medium",
        "source_type": source_meta.get("source_type", "mixed"),
        "warnings": warnings or [],
    }


# ---------------------------------------------------------------------------
# Confidence adjustment
# ---------------------------------------------------------------------------

def _adjust_confidence(
    draft: dict[str, Any],
    source_meta: dict[str, Any],
    ranked: list[dict[str, Any]],
) -> None:
    """Adjust confidence based on actual source quality, not just LLM judgment.

    Confidence tiers:
    - high:   DB records + corroborating gov pages
    - medium: Gov pages or trusted web sources
    - low:    Only generic web results or conflicting info
    """
    source_type = source_meta.get("source_type", "none")
    db_strong = source_meta.get("db_strong", False)
    gov_pages_count = source_meta.get("gov_pages_count", 0)
    deep_web_count = source_meta.get("deep_web_count", 0)

    # Count trusted web sources in ranked results
    trusted_web = sum(
        1 for r in ranked
        if r.get("type") == "web" and (r.get("web_result") or {}).get("trusted")
    )

    if db_strong and (gov_pages_count > 0 or trusted_web > 0):
        # DB + gov/web corroboration → high
        draft["confidence"] = "high"
    elif db_strong:
        # DB only, strong match → high
        draft["confidence"] = "high"
    elif gov_pages_count > 0:
        # Official gov pages scraped → medium-high
        draft["confidence"] = "medium"
    elif trusted_web > 0:
        # Trusted web sources → medium
        draft["confidence"] = "medium"
    elif deep_web_count > 0 or any(r.get("type") == "web" for r in ranked):
        # Generic web → low-medium (keep LLM's judgment)
        if draft.get("confidence") not in ("high", "medium"):
            draft["confidence"] = "low"
    else:
        # Only YouTube or nothing → low
        draft["confidence"] = "low"


# ---------------------------------------------------------------------------
# Source warnings
# ---------------------------------------------------------------------------

def _add_source_warnings(
    warnings: list[str],
    source_meta: dict[str, Any],
    citations: list[dict[str, Any]],
) -> None:
    """Add contextual warnings based on source quality."""
    source_type = source_meta.get("source_type", "none")
    db_strong = source_meta.get("db_strong", False)
    gov_pages_count = source_meta.get("gov_pages_count", 0)

    web_citations = [c for c in citations if c.get("from_web")]
    db_citations = [c for c in citations if not c.get("from_web") and not c.get("from_video")]
    video_citations = [c for c in citations if c.get("from_video")]

    if not citations:
        warnings.append("No official source citations could be linked. Please verify independently.")

    if not db_strong and not db_citations:
        if gov_pages_count > 0:
            warnings.append(
                "This answer is based on live content from official government websites. "
                "Information may have been updated since last check."
            )
        elif web_citations:
            warnings.append(
                "This answer is based on web search results. For the most accurate information, "
                "please visit the official government website linked below."
            )
        elif not video_citations:
            warnings.append(
                "Limited source information available. Please verify with the relevant government department."
            )

    if video_citations:
        warnings.append(
            "YouTube videos are provided as supplementary guidance only. "
            "Always refer to official government sources for authoritative information."
        )


# ---------------------------------------------------------------------------
# Auto-enrich DB (learn from successful web answers)
# ---------------------------------------------------------------------------

def _auto_enrich(
    query: str,
    parsed: dict[str, Any],
    verified: dict[str, Any],
    ranked: list[dict[str, Any]],
    source_meta: dict[str, Any],
) -> None:
    """If we answered well using web/gov sources but DB was weak, cache the
    answer into the DB for next time.

    This makes the system smarter over time — common queries get cached.
    """
    db_strong = source_meta.get("db_strong", False)
    if db_strong:
        return  # DB already had the answer, no enrichment needed

    # Only enrich if the answer has useful structured data
    answer = verified.get("answer", "")
    if len(answer) < 100:
        return  # Answer too short, probably not useful

    service = parsed.get("service")
    if not service:
        return  # Need a service name to store it

    # Collect source URLs from ranked results
    source_urls: list[str] = []
    for item in ranked:
        if item.get("type") == "gov_page":
            source_urls.append(item.get("url", ""))
        elif item.get("type") == "web":
            wr = item.get("web_result", {})
            if wr.get("url"):
                source_urls.append(wr["url"])

    if not source_urls:
        return  # No URLs to cite

    # Build enrichment content
    content_parts: list[str] = []
    if answer:
        content_parts.append(answer)
    reqs = verified.get("requirements") or []
    if reqs:
        content_parts.append("Required Documents: " + "; ".join(reqs))
    steps = verified.get("steps") or []
    if steps:
        content_parts.append("Steps: " + " → ".join(steps))
    fee = verified.get("fee")
    if fee:
        content_parts.append(f"Fee: {fee}")

    enrichment_content = "\n".join(content_parts)

    # Try to store in DB (non-blocking, best-effort)
    try:
        _store_enrichment(
            service=service,
            province=parsed.get("province"),
            content=enrichment_content,
            source_urls=source_urls[:3],
            confidence=verified.get("confidence", "low"),
        )
    except Exception as exc:
        logger.debug("Auto-enrich skipped: %s", exc)


def _store_enrichment(
    service: str,
    province: str | None,
    content: str,
    source_urls: list[str],
    confidence: str,
) -> None:
    """Store web-derived information in the database for future queries.

    Creates/updates government_services + documents + chunks.
    """
    from app.db.supabase import get_supabase
    from app.ai.embeddings import embed_text
    import uuid
    from datetime import datetime, timezone

    sb = get_supabase()

    # Check if we already have an auto-enriched record for this service+province
    check_name = f"{service} (web-enriched)"
    existing = sb.table("government_services").select("id").eq("name", check_name).execute()
    if existing.data:
        return  # Already enriched, skip

    # Create a new government_services record
    service_id = str(uuid.uuid4())
    sb.table("government_services").insert({
        "id": service_id,
        "name": check_name,
        "description": f"Auto-enriched information about {service} from web sources.",
        "department": None,
        "province": province,
        "city": None,
        "module": "guide",
    }).execute()

    # Create a document record
    doc_id = str(uuid.uuid4())
    source_url = source_urls[0] if source_urls else "web-search"
    sb.table("documents").insert({
        "id": doc_id,
        "service_id": service_id,
        "source_id": None,  # No formal source — web-derived
        "url": source_url,
        "title": f"Web-enriched: {service}",
        "content": content,
        "last_verified": datetime.now(timezone.utc).isoformat(),
        "module": "guide",
    }).execute()

    # Create chunks with embeddings
    # Split content into chunks of ~500 chars
    chunk_size = 500
    chunks_text = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]

    for chunk_text in chunks_text[:5]:  # Max 5 chunks
        embedding = embed_text(chunk_text)
        chunk_id = str(uuid.uuid4())
        sb.table("document_chunks").insert({
            "id": chunk_id,
            "document_id": doc_id,
            "section": "auto-enriched",
            "content": chunk_text,
            "embedding": embedding,
            "metadata": {
                "module": "guide",
                "service": service,
                "province": province,
                "source": "web-enriched",
                "confidence": confidence,
            },
        }).execute()

    logger.info("Auto-enriched DB for service=%s, province=%s (%d chunks)",
                service, province, len(chunks_text[:5]))


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def _empty_response(query: str, language: str = "english") -> dict[str, Any]:
    """Response when truly no information is found anywhere (very rare now)."""
    messages = {
        "english": (
            "I wasn't able to find information about this from any available source. "
            "Try rephrasing your question, or contact the relevant government department directly. "
            "Common helplines: NADRA 111-786-100, Passport Office 051-111-786-100."
        ),
        "urdu": (
            "معذرت، اس سوال کا جواب کسی بھی دستیاب ذریعے سے نہیں ملا۔ "
            "براہ کرم سوال دوبارہ لکھیں یا متعلقہ محکمے سے رابطہ کریں۔ "
            "نادرا ہیلپ لائن: 111-786-100"
        ),
        "roman_urdu": (
            "Maaf kijiye, is sawal ka jawab kisi bhi available source se nahi mila. "
            "Barah-e-karam sawal dobara likhein ya mutaliqa department se raabta karein. "
            "NADRA Helpline: 111-786-100"
        ),
    }
    return {
        "module": "guide",
        "answer": messages.get(language, messages["english"]),
        "requirements": [],
        "steps": [],
        "fee": None,
        "processing_time": None,
        "application_method": None,
        "application_url": None,
        "sources": [],
        "last_verified": None,
        "confidence": "low",
        "source_type": "none",
        "warnings": ["No information found from any source — DB, web, or YouTube."],
    }


def _error_response(error_msg: str) -> dict[str, Any]:
    """Response when an error occurs during processing."""
    return {
        "module": "guide",
        "answer": "An error occurred while generating the answer. Please try again.",
        "requirements": [],
        "steps": [],
        "fee": None,
        "processing_time": None,
        "application_method": None,
        "application_url": None,
        "sources": [],
        "last_verified": None,
        "confidence": "low",
        "source_type": "none",
        "warnings": [f"Error: {error_msg}"],
    }
