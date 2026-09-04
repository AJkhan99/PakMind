"""Grounded web answer generation for PakWatch.

Uses Gemini's google_search grounding tool to answer out-of-DB questions
with live web results and grounded citations.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.llm_router import call_google_grounded
from app.config import get_settings

logger = logging.getLogger(__name__)


def generate_web_answer(query: str, language: str = "english") -> dict[str, Any]:
    """Answer an out-of-DB question using grounded Google Search.

    Returns a dict with answer/what_changed/who_affected/effective_date
    plus 'web_sources' (grounded citations) and 'model'.
    """
    language_hint = ""
    if language == "urdu":
        language_hint = (
            " The user asked in Urdu script (اردو) — reply in Urdu script.\n"
        )
    elif language == "roman_urdu":
        language_hint = (
            " The user asked in Roman Urdu (Urdu in English letters) — "
            "reply in Roman Urdu.\n"
        )
    system_instruction = (
        "You are PakWatch, an assistant that tracks Pakistani government updates. "
        "Search the web for current, official Pakistani government information "
        "answering the user's question (petrol prices, taxes, notifications, "
        "policies, schemes, etc.). Prefer official .gov.pk sources and reputable "
        "news outlets, and include dates where available.\n\n"
        "Respond with ONLY a JSON object (no markdown fences) with fields:\n"
        '{"answer": "...", "what_changed": "... or null", '
        '"who_affected": "... or null", "effective_date": "... or null"}\n'
        "Keep the answer concise (3-6 sentences). If the search yields nothing "
        "relevant, set answer to a short explanation and the other fields to null."
        + language_hint
    )

    text, web_sources = call_google_grounded(query, system_instruction=system_instruction)

    # Parse JSON from plain text (strip markdown fences if present)
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Grounded answer was not valid JSON — wrapping raw text")
        result = {
            "answer": text.strip(),
            "what_changed": None,
            "who_affected": None,
            "effective_date": None,
        }

    result["web_sources"] = web_sources
    result["model"] = get_settings().gemini_model
    return result
