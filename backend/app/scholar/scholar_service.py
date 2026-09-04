"""PakScholar service — AI-powered eligibility matching with web-search fallback.

Two-phase matching:
  Phase 1 — Check the local Supabase database for eligible opportunities.
  Phase 2 — If no eligible matches are found, search the web via Serper.dev
            and ask the AI to summarise which results look relevant.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx

from app.ai.llm_router import call_llm_json
from app.config import get_settings
from app.db.supabase import get_all_opportunities
from app.scholar.prompts import DB_SYSTEM_PROMPT, WEB_SYSTEM_PROMPT, URDU_LANGUAGE_INSTRUCTION

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """Detect whether the text contains Urdu script characters.
    
    Urdu uses the Arabic Unicode block (U+0600–U+06FF) and Extended Arabic (U+0750–U+077F).
    Returns 'ur' if Urdu characters are found, otherwise 'en'.
    """
    urdu_char_count = 0
    for ch in text:
        cp = ord(ch)
        # Arabic/Urdu script ranges
        if (0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F) or (0xFB50 <= cp <= 0xFDFF) or (0xFE70 <= cp <= 0xFEFF):
            urdu_char_count += 1
    # If at least 3 Urdu-script characters are present, treat the whole query as Urdu
    return "ur" if urdu_char_count >= 3 else "en"


# ---------------------------------------------------------------------------
# Helper: build a search query from the user's profile text
# ---------------------------------------------------------------------------

def build_search_query(profile: str) -> str:
    """Turn the user's free-text profile into a focused Google search query."""
    return f"scholarships Pakistan {profile} eligibility 2026"


# ---------------------------------------------------------------------------
# Helper: search the web using Serper.dev
# ---------------------------------------------------------------------------

def search_web(query: str) -> list[dict]:
    """Call the Serper.dev Google Search API and return the top 5 organic results."""
    settings = get_settings()
    response = httpx.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": settings.serper_api_key,
            "Content-Type": "application/json",
        },
        json={"q": query, "num": 5},
        timeout=15.0,
    )
    response.raise_for_status()
    data = response.json()

    # Serper returns results under the "organic" key
    results = []
    for item in data.get("organic", [])[:5]:
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", ""),
        })
    return results


# ---------------------------------------------------------------------------
# Phase 1: Match against database opportunities
# ---------------------------------------------------------------------------

def match_opportunities(user_query: str, opportunities: list[dict], language: str) -> dict:
    """Check eligibility against database opportunities using the LLM.
    
    Returns a dict with 'matches' and 'answer_summary' keys.
    """
    # Build the system prompt (add Urdu instructions if needed)
    system_prompt = DB_SYSTEM_PROMPT
    if language == "ur":
        system_prompt += URDU_LANGUAGE_INSTRUCTION

    # Build the user message with profile + opportunities data
    user_message = (
        f"User profile / query:\n{user_query}\n\n"
        f"Opportunities database ({len(opportunities)} records):\n"
        f"{json.dumps(opportunities, indent=2, default=str)}"
    )

    # Call the LLM with system + user messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    
    result = call_llm_json(messages, provider="google")
    
    return {
        "matches": result.get("matches", []),
        "answer_summary": result.get("answer_summary", ""),
    }


# ---------------------------------------------------------------------------
# Phase 2: Web search fallback
# ---------------------------------------------------------------------------

def search_web_for_opportunities(user_query: str, language: str) -> dict:
    """Search the web and filter results for relevance using the LLM.
    
    Returns a dict with 'web_matches' and 'web_summary' keys.
    """
    # Build the system prompt (add Urdu instructions if needed)
    system_prompt = WEB_SYSTEM_PROMPT
    if language == "ur":
        system_prompt += URDU_LANGUAGE_INSTRUCTION

    # Build a search query from the user's profile
    search_query = build_search_query(user_query)

    # Search the web via Serper.dev
    search_results = search_web(search_query)
    
    if not search_results:
        return {"web_matches": [], "web_summary": ""}

    # Build the user message with profile + search results
    user_message = (
        f"User profile / query:\n{user_query}\n\n"
        f"Web search results ({len(search_results)} results):\n"
        f"{json.dumps(search_results, indent=2)}"
    )

    # Call the LLM to filter relevant results
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    
    result = call_llm_json(messages, provider="google")
    
    web_matches = result.get("web_matches", [])
    web_summary = result.get("web_summary", "")

    # Stamp every web result with the time the search was performed
    now_iso = datetime.now(timezone.utc).isoformat()
    for wm in web_matches:
        wm["found_on"] = now_iso

    return {
        "web_matches": web_matches,
        "web_summary": web_summary,
    }


# ---------------------------------------------------------------------------
# Main orchestration: two-phase matching
# ---------------------------------------------------------------------------

async def process_query(user_query: str) -> dict:
    """Process a scholar query through two-phase matching.
    
    Phase 1: Check the verified database for eligible opportunities.
    Phase 2: If none are eligible, fall back to a web search.
    
    Returns a response dict with database_matches, web_matches, summaries, etc.
    """
    settings = get_settings()
    
    # Step 1: Detect the language of the user's query
    lang = detect_language(user_query)

    # Step 2: Fetch every opportunity from the database
    try:
        opportunities = get_all_opportunities()
    except Exception as exc:
        logger.error("Database fetch failed: %s", exc)
        return {
            "error": True,
            "message": "We're having trouble reaching our database right now. Please try again shortly.",
            "database_matches": [],
            "web_matches": [],
            "answer_summary": "",
            "web_summary": "",
            "detected_language": lang,
        }

    # Step 3: Phase 1 — Database matching
    database_matches = []
    answer_summary = ""

    if opportunities:
        try:
            result = match_opportunities(user_query, opportunities, lang)
            database_matches = result["matches"]
            answer_summary = result["answer_summary"]
        except Exception as exc:
            logger.error("LLM eligibility matching failed: %s", exc)
            return {
                "error": True,
                "message": "Our AI service is temporarily busy. Please try again in a moment.",
                "database_matches": [],
                "web_matches": [],
                "answer_summary": "",
                "web_summary": "",
                "detected_language": lang,
            }

    # Step 4: Merge last_verified from the original DB rows into each match
    verified_lookup = {}
    for opp in (opportunities or []):
        title = opp.get("title", "")
        verified_lookup[title] = opp.get("last_verified")

    for match in database_matches:
        title = match.get("title", "")
        if title in verified_lookup and verified_lookup[title]:
            match["last_verified"] = verified_lookup[title]

    # Step 5: Check if at least one opportunity was marked eligible
    has_eligible = any(
        m.get("eligible") is True or m.get("eligible") == "maybe"
        for m in database_matches
    )

    # Step 6: Phase 2 — Web search fallback (only if no eligible DB matches)
    web_matches = []
    web_summary = ""
    web_search_note = None

    if not has_eligible and settings.serper_api_key:
        try:
            web_result = search_web_for_opportunities(user_query, lang)
            web_matches = web_result["web_matches"]
            web_summary = web_result["web_summary"]
        except Exception as exc:
            logger.warning("Web search failed: %s — skipping gracefully", exc)
            web_matches = []
            web_summary = ""
            web_search_note = "Web search unavailable right now, showing verified database results only."

    # Step 7: Build the final response
    if not database_matches and not web_matches:
        response = {
            "database_matches": [],
            "web_matches": [],
            "answer_summary": "",
            "web_summary": "",
            "detected_language": lang,
            "message": "No matching opportunities found in our verified database or the web right now.",
        }
        if web_search_note:
            response["web_search_note"] = web_search_note
        return response

    response = {
        "database_matches": database_matches,
        "web_matches": web_matches,
        "answer_summary": answer_summary,
        "web_summary": web_summary,
        "detected_language": lang,
    }
    if web_search_note:
        response["web_search_note"] = web_search_note
    
    return response
