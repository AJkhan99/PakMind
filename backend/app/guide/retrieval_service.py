"""Retrieval service — smart multi-phase retrieval with deep scraping fallback.

When the database has the answer, use it. When it doesn't, go to the actual
government website and scrape the live page. Never return empty when web
content exists.

Flow:
  Phase 1: Parse query (fast heuristic, ~0ms)
  Phase 2: Parallel search — DB + web + YouTube (~2-3s)
  Phase 3: Assess context strength
  Phase 4: If DB is weak → deep-scrape known gov pages + top web results (~3-5s)
  Phase 5: Build unified context with source labels
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.guide import vector_search, keyword_search, ranking, web_search
from app.guide import deep_web
from app.guide.query_parser import parse_query, build_search_keywords
from app.guide.youtube_search import search_youtube_for_service, build_youtube_context
from app.guide.service_urls import get_urls_for_service, get_search_query
from app.db.supabase import search_services

logger = logging.getLogger(__name__)

# Context strength threshold — below this triggers deep scraping
_MIN_DB_SCORE = 0.4  # Minimum score from DB results to consider "strong"
_MIN_DB_CONTEXT_CHARS = 300  # Minimum chars of DB content to skip deep scraping


def retrieve(
    query: str,
    parsed_query: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Run smart multi-phase retrieval and return ranked results + context.

    Args:
        query: The raw user question.
        parsed_query: Optional pre-parsed query dict. If None, parsed here.

    Returns:
        (ranked_results, context_string)
    """
    # ---- Phase 1: Parse query (FAST — no LLM call) ----
    if parsed_query is None:
        parsed_query = parse_query(query)

    search_keywords = build_search_keywords(query, parsed_query)
    search_text = " ".join(search_keywords) if search_keywords else query

    service = parsed_query.get("service")
    province = parsed_query.get("province")
    city = parsed_query.get("city")
    intent = parsed_query.get("intent")

    logger.info("Parsed: service=%s, province=%s, city=%s, intent=%s, lang=%s",
                service, province, city, intent, parsed_query.get("language"))

    # ---- Phase 2: Parallel search (DB + web + YouTube) ----
    vector_chunks: list[dict[str, Any]] = []
    keyword_results: list[dict[str, Any]] = []
    web_results: list[dict[str, Any]] = []
    youtube_results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures: dict[Any, str] = {}

        # 2a. Vector search
        futures[pool.submit(_do_vector_search, query, parsed_query)] = "vector"

        # 2b. Keyword search
        futures[pool.submit(_do_keyword_search, search_text)] = "keyword"

        # 2c. Structured search
        futures[pool.submit(_do_structured_search, parsed_query)] = "structured"

        # 2d. Web search (DuckDuckGo)
        futures[pool.submit(_do_web_search, query, parsed_query)] = "web"

        # 2e. YouTube search
        if service:
            futures[pool.submit(_do_youtube_search, parsed_query)] = "youtube"

        for future in as_completed(futures):
            label = futures[future]
            try:
                result = future.result()
                if label == "vector":
                    vector_chunks = result
                elif label == "keyword":
                    keyword_results = result
                elif label == "structured":
                    seen_ids = {r.get("id") for r in keyword_results}
                    for svc in result:
                        if svc.get("id") not in seen_ids:
                            keyword_results.append(svc)
                            seen_ids.add(svc.get("id"))
                elif label == "web":
                    web_results = result
                elif label == "youtube":
                    youtube_results = result
            except Exception as exc:
                logger.warning("%s search failed: %s", label, exc)

    logger.info("Phase 2: %d vector, %d keyword, %d web, %d videos",
                len(vector_chunks), len(keyword_results), len(web_results), len(youtube_results))

    # ---- Phase 3: Rank DB results + assess strength ----
    ranked, db_context = ranking.rank_results(vector_chunks, keyword_results)

    db_score = ranked[0]["score"] if ranked else 0.0
    db_chars = len(db_context)
    db_strong = (db_score >= _MIN_DB_SCORE and db_chars >= _MIN_DB_CONTEXT_CHARS)

    logger.info("DB context: score=%.3f, chars=%d, strong=%s", db_score, db_chars, db_strong)

    # ---- Phase 4: Deep scraping (if DB is weak) ----
    gov_pages: list[dict[str, Any]] = []
    deep_web_results: list[dict[str, Any]] = []

    if not db_strong:
        logger.info("DB context weak — launching deep scraping phase")
        gov_pages, deep_web_results = _deep_scrape_phase(
            service=service,
            province=province,
            city=city,
            intent=intent,
            web_results=web_results,
        )
        logger.info("Deep scraping: %d gov pages, %d web pages scraped",
                     len(gov_pages), len(deep_web_results))

    # ---- Phase 5: Build unified context ----
    context = db_context
    source_type = "database" if db_strong else "mixed"

    # Add gov page content (highest quality web source)
    if gov_pages:
        gov_context = _build_gov_page_context(gov_pages)
        context = context + "\n\n" + gov_context if context else gov_context
        source_type = "gov_page" if not db_strong else "mixed"
        for gp in gov_pages:
            ranked.append({
                "type": "gov_page",
                "score": 0.7,  # High score — official gov content
                "content": gp["content"][:200],
                "gov_page": gp,
                "url": gp["url"],
                "title": gp["title"],
            })

    # Add web results
    if web_results:
        # If we deep-scraped web results, use the full page content
        if deep_web_results:
            web_context = _build_deep_web_context(deep_web_results)
        else:
            web_context = _build_web_context(web_results)
        if web_context:
            context = context + "\n\n" + web_context if context else web_context
            if not gov_pages and not db_strong:
                source_type = "web"
            for wr in (deep_web_results or web_results):
                ranked.append({
                    "type": "web",
                    "score": 0.3 if wr.get("trusted") else 0.15,
                    "content": wr.get("content", wr.get("snippet", ""))[:200],
                    "web_result": wr,
                })

    # Add YouTube results
    if youtube_results:
        yt_context = build_youtube_context(youtube_results)
        if yt_context:
            context = context + "\n\n" + yt_context if context else yt_context
            for v in youtube_results:
                ranked.append({
                    "type": "video",
                    "score": 0.2,
                    "content": f"Video: {v['title']}\nURL: {v['url']}\n{v['snippet']}",
                    "web_result": v,
                })

    # Store source_type metadata on the ranked list for the guide service
    _source_metadata = {
        "source_type": source_type,
        "db_strong": db_strong,
        "gov_pages_count": len(gov_pages),
        "deep_web_count": len(deep_web_results),
    }

    return ranked, context, _source_metadata


# ---------------------------------------------------------------------------
# Phase 4: Deep scraping
# ---------------------------------------------------------------------------

def _deep_scrape_phase(
    service: str | None,
    province: str | None,
    city: str | None,
    intent: str | None,
    web_results: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run deep scraping in parallel: gov pages + web search results.

    Returns:
        (gov_pages, deep_web_results)
    """
    gov_pages: list[dict[str, Any]] = []
    deep_web_results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures: dict[Any, str] = {}

        # A. Scrape known government pages (if service is identified)
        if service:
            gov_urls = get_urls_for_service(service, province)
            if gov_urls:
                futures[pool.submit(deep_web.scrape_pages, gov_urls)] = "gov_pages"

        # B. Deep-scraping top web search results (full page content)
        if web_results:
            futures[pool.submit(deep_web.scrape_search_results, web_results)] = "deep_web"

        # C. If no service detected but we have web results, scrape those
        if not service and web_results:
            futures[pool.submit(deep_web.scrape_search_results, web_results)] = "deep_web"

        for future in as_completed(futures):
            label = futures[future]
            try:
                result = future.result()
                if label == "gov_pages":
                    gov_pages.extend(result)
                elif label == "deep_web":
                    deep_web_results.extend(result)
            except Exception as exc:
                logger.warning("Deep scrape (%s) failed: %s", label, exc)

    return gov_pages, deep_web_results


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _build_gov_page_context(gov_pages: list[dict[str, Any]]) -> str:
    """Build context from scraped government pages."""
    blocks: list[str] = []
    for i, page in enumerate(gov_pages, 1):
        province_label = f" ({page['province']})" if page.get("province") else ""
        blocks.append(
            f"--- GOV PAGE {i} [OFFICIAL GOVERNMENT WEBSITE{province_label}] ---\n"
            f"Title: {page['title']}\n"
            f"URL: {page['url']}\n"
            f"Content:\n{page['content']}"
        )
    return "\n\n".join(blocks)


def _build_deep_web_context(deep_results: list[dict[str, Any]]) -> str:
    """Build context from deep-scraped web results (full page content)."""
    blocks: list[str] = []
    for i, result in enumerate(deep_results, 1):
        trust_label = "TRUSTED GOV SOURCE" if result.get("trusted") else "WEB RESULT"
        source_name = result.get("source_name", "Web Source")
        blocks.append(
            f"--- WEB SOURCE {i} [{trust_label} — {source_name}] ---\n"
            f"Title: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Content:\n{result['content'][:MAX_WEB_CONTEXT_CHARS]}"
        )
    return "\n\n".join(blocks)


def _build_web_context(web_results: list[dict[str, Any]]) -> str:
    """Build context from DuckDuckGo snippets (when deep scrape wasn't done)."""
    blocks: list[str] = []
    for i, wr in enumerate(web_results, 1):
        trust_label = "TRUSTED GOV SOURCE" if wr.get("trusted") else "WEB RESULT"
        blocks.append(
            f"--- WEB SOURCE {i} [{trust_label}] ---\n"
            f"Title: {wr['title']}\n"
            f"URL: {wr['url']}\n"
            f"Source: {wr['source_name']}\n"
            f"Content: {wr['snippet']}"
        )
    return "\n\n".join(blocks)


MAX_WEB_CONTEXT_CHARS = 6000  # Limit per deep-scraped web result in context


# ---------------------------------------------------------------------------
# Parallel search workers (unchanged)
# ---------------------------------------------------------------------------

def _do_vector_search(query: str, parsed_query: dict) -> list[dict[str, Any]]:
    """Vector search on document chunks (involves embedding API call)."""
    try:
        vector_filters: dict[str, Any] = {"module": "guide"}
        if parsed_query.get("service"):
            vector_filters["service"] = parsed_query["service"]
        if parsed_query.get("province"):
            vector_filters["province"] = parsed_query["province"]
        return vector_search.search(query, filters=vector_filters)
    except Exception as exc:
        logger.warning("Vector search failed: %s", exc)
        return []


def _do_keyword_search(search_text: str) -> list[dict[str, Any]]:
    """Keyword search on government_services (fast DB query)."""
    try:
        return keyword_search.search(search_text)
    except Exception as exc:
        logger.warning("Keyword search failed: %s", exc)
        return []


def _do_structured_search(parsed_query: dict) -> list[dict[str, Any]]:
    """Structured search by service/province/city (fast DB query)."""
    try:
        return search_services(
            name=parsed_query.get("service"),
            province=parsed_query.get("province"),
            city=parsed_query.get("city"),
            limit=5,
        )
    except Exception as exc:
        logger.warning("Structured search failed: %s", exc)
        return []


def _do_web_search(query: str, parsed_query: dict) -> list[dict[str, Any]]:
    """Live web search via DuckDuckGo."""
    try:
        service = parsed_query.get("service")
        province = parsed_query.get("province")
        if service:
            return web_search.search_web_for_service(service, province)
        else:
            return web_search.search_web(query)
    except Exception as exc:
        logger.warning("Web search failed: %s", exc)
        return []


def _do_youtube_search(parsed_query: dict) -> list[dict[str, Any]]:
    """YouTube video search for government service tutorials."""
    try:
        return search_youtube_for_service(
            service=parsed_query.get("service", ""),
            province=parsed_query.get("province"),
        )
    except Exception as exc:
        logger.warning("YouTube search failed: %s", exc)
        return []
