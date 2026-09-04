"""Query parser — extract intent, category, province, topic from natural-language queries.

Uses heuristic rules (fast, no LLM call) with optional LLM fallback for complex queries.
Supports English, Roman Urdu, and Urdu script questions.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Keyword mappings for heuristic parsing
_PROVINCE_KEYWORDS = {
    "punjab": "Punjab",
    "sindh": "Sindh",
    "kpk": "Khyber Pakhtunkhwa",
    "khyber pakhtunkhwa": "Khyber Pakhtunkhwa",
    "kp": "Khyber Pakhtunkhwa",
    "balochistan": "Balochistan",
    "islamabad": "Islamabad Capital Territory",
    "ict": "Islamabad Capital Territory",
    "federal": "Federal",
    "ajk": "Azad Jammu & Kashmir",
    "kashmir": "Azad Jammu & Kashmir",
    "gilgit": "Gilgit-Baltistan",
    "gb": "Gilgit-Baltistan",
}

_CATEGORY_KEYWORDS = {
    "policy": "policy",
    "policies": "policy",
    "notification": "notification",
    "notifications": "notification",
    "announcement": "announcement",
    "announcements": "announcement",
    "scheme": "scheme",
    "schemes": "scheme",
    "regulation": "regulation",
    "regulations": "regulation",
    "appointment": "appointment",
    "appointments": "appointment",
    "circular": "circular",
    "circulars": "circular",
    "public notice": "public_notice",
    "administrative": "administrative",
    "public service": "public_service",
}

_INTENT_PATTERNS = [
    (r"what.*(latest|recent|new|today)", "latest_updates"),
    (r"any.*(new|recent|update)", "latest_updates"),
    (r"what.*(changed|change|different)", "what_changed"),
    (r"what.*(policy|policies)", "policy_updates"),
    (r"any.*(notification|circular)", "notifications"),
    (r"who.*(affected|impact)", "specific_topic"),
]

_TOPIC_KEYWORDS = {
    "education": "education",
    "health": "health",
    "tax": "tax",
    "finance": "finance",
    "budget": "budget",
    "agriculture": "agriculture",
    "housing": "housing",
    "transport": "transport",
    "energy": "energy",
    "passport": "passport",
    "cnic": "cnic",
    "domicile": "domicile",
    "pension": "pension",
    "employment": "employment",
    "nadra": "nadra",
}

# ---------------------------------------------------------------------------
# Language detection (English / Roman Urdu / Urdu script) — PakGuide parity
# ---------------------------------------------------------------------------

# Roman Urdu question words → detection patterns (same approach as PakGuide)
ROMAN_URDU_PATTERNS: list[tuple[str, str]] = [
    # (pattern, normalized_meaning)
    (r"\b(kaise|kese|kaisy|کیسے)\b", "how"),
    (r"\b(kya|کیا)\b", "what"),
    (r"\b(kahan|kaha|کہاں)\b", "where"),
    (r"\b(kab|کب)\b", "when"),
    (r"\b(kitna|kitne|kitni|کتنا|کتنے)\b", "how_much"),
    (r"\b(kaun|kon|کون)\b", "who"),
    (r"\b(kyun|kyon|کیوں)\b", "why"),
    (r"\b(banwana|banane|بنوانا|بنانے)\b", "make"),
    (r"\b(milega|milegi|ملے گا|ملے گی)\b", "get"),
    (r"\b(lagega|lagegi|لگے گا|لگے گی)\b", "cost_or_time"),
    (r"\b(chahiye|chahye|چاہیے)\b", "need"),
    (r"\b(tarika|tareeqa|طریقہ)\b", "method"),
    (r"\b(darkar|ضرورت)\b", "required"),
]

_ROMAN_URDU_WORDS = {
    "kya", "kaise", "kahan", "kab", "kitna", "kitne", "kaun", "kon",
    "hai", "hain", "kar", "karo", "karna",
    "mein", "main", "mujhe", "hum", "tum", "aap",
    "ke", "ki", "ka", "ko", "se",
    "bhi", "nahi", "nahin", "agar", "toh",
    "banwa", "banwana", "mil", "milega",
    "lagega", "chahiye", "darkar", "hua", "hoga", "ne",
}


def detect_language(query: str) -> str:
    """Detect if the query is in English, Roman Urdu, or Urdu script."""
    total_chars = len(query.strip())
    if total_chars == 0:
        return "english"

    # Urdu script — Arabic Unicode block (اردو حروف)
    urdu_ratio = len(re.findall(r"[\u0600-\u06FF]", query)) / total_chars
    if urdu_ratio > 0.2:
        return "urdu"

    q = query.lower()
    # Strip punctuation (incl. Urdu ؟،؛) so trailing "?" doesn't hide words like "hai?"
    words = [w.strip("?,.!\"'()؛،؟۔") for w in q.split()]
    roman_count = sum(1 for w in words if w in _ROMAN_URDU_WORDS)
    has_pattern = any(re.search(p, q) for p, _ in ROMAN_URDU_PATTERNS)

    # Two or more Roman Urdu words, or a question word plus any Roman Urdu marker
    if roman_count >= 2 or (has_pattern and roman_count >= 1):
        return "roman_urdu"

    return "english"


def parse_query(query: str) -> dict[str, Any]:
    """Parse a natural-language query into structured intent.

    Fast heuristic parsing — no LLM call.
    """
    q = query.lower().strip()

    result: dict[str, Any] = {
        "intent": None,
        "category": None,
        "province": None,
        "department": None,
        "topic": None,
        "language": detect_language(query),
    }

    # Detect province
    for keyword, province in _PROVINCE_KEYWORDS.items():
        if keyword in q:
            result["province"] = province
            break

    # Detect category
    for keyword, category in _CATEGORY_KEYWORDS.items():
        if keyword in q:
            result["category"] = category
            break

    # Detect topic
    for keyword, topic in _TOPIC_KEYWORDS.items():
        if keyword in q:
            result["topic"] = topic
            break

    # Detect intent
    for pattern, intent in _INTENT_PATTERNS:
        if re.search(pattern, q):
            result["intent"] = intent
            break

    if not result["intent"]:
        if result["category"]:
            result["intent"] = "policy_updates" if result["category"] == "policy" else "specific_topic"
        else:
            result["intent"] = "latest_updates"

    return result


def build_search_keywords(query: str, parsed: dict[str, Any]) -> list[str]:
    """Build a list of search keywords from the query and parsed intent."""
    keywords = []

    if parsed.get("topic"):
        keywords.append(parsed["topic"])
    if parsed.get("category"):
        keywords.append(parsed["category"])
    if parsed.get("province"):
        keywords.append(parsed["province"])
    if parsed.get("department"):
        keywords.append(parsed["department"])

    # If no structured keywords, use the original query words (minus common words)
    if not keywords:
        stop_words = {"what", "are", "the", "latest", "new", "any", "has", "have",
                      "is", "did", "do", "in", "for", "about", "government", "update",
                      "updates", "pakistan", "pakistani"}
        words = [w.strip("?,.!") for w in query.lower().split() if w.strip("?,.!") not in stop_words]
        keywords = words[:5]

    return keywords
