"""Fast heuristic query parser — no LLM call needed.

Extracts service, province, city, intent, and language from user questions.
Supports English, Roman Urdu, and Urdu script.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service keywords — English + Roman Urdu + Urdu
# ---------------------------------------------------------------------------

SERVICE_MAP: dict[str, list[str]] = {
    "domicile": [
        "domicile", "domicile certificate", "domisile", "domisail",
        "ڈومیسائل", "ڈومیسائل سرٹیفکیٹ", "مقامی سرٹیفکیٹ",
        "rahayshi", "rihaishi", "stayi",
    ],
    "passport": [
        "passport", "pasport", "pass port",
        "پاسپورٹ", "پاسپورٹ بنوانا",
    ],
    "driving licence": [
        "driving licence", "driving license", "drive licence", "drive license",
        "licence", "license", "driving",
        "ڈرائیونگ لائسنس", "لائسنس",
        "gari ka licence", "gaari ka license",
    ],
    "cnic": [
        "cnic", "nicop", "identity card", "id card", "nadra card",
        "شناختی کارڈ", "قومی شناختی", "نادرا",
        "shanakhti card", "shinakhti",
    ],
    "b-form": [
        "b-form", "bform", "b form", "birth registration",
        "ب فارم",
    ],
    "birth certificate": [
        "birth certificate", "birth registration",
        "پیدائش کا سرٹیفکیٹ", "برتھ سرٹیفکیٹ",
        "pedaish", "birth",
    ],
    "death certificate": [
        "death certificate", "death registration",
        "وفات کا سرٹیفکیٹ", "ڈیتھ سرٹیفکیٹ",
        "death", "wafat",
    ],
    "marriage certificate": [
        "marriage certificate", "nikah nama", "marriage registration",
        "شادی کا سرٹیفکیٹ", "نکاح نامہ",
        "shadi", "nikah", "marriage", "byah",
    ],
    "police character certificate": [
        "police character", "character certificate", "police clearance",
        "پولیس کریکٹر", "کریکٹر سرٹیفکیٹ", "پولیس کلیرنس",
        "police certificate", "character",
    ],
    "vehicle registration": [
        "vehicle registration", "car registration", "bike registration",
        "registration book", "transfer",
        "گاڑی کی رجسٹریشن", "رجسٹریشن",
        "gari", "gaari", "vehicle",
    ],
    "arms licence": [
        "arms licence", "arms license", "gun licence", "weapon licence",
        "اسلحہ لائسنس",
        "bandook", "hathiyar",
    ],
    "property mutation": [
        "mutation", "inteqal", "property transfer", "fard",
        "فرد", "انتقال", "میوٹیشن",
        "zameen", "property",
    ],
    "income tax": [
        "income tax", "tax return", "ntn", "filer", "non-filer",
        "انکم ٹیکس", "ٹیکس",
        "tax", "ntn number",
    ],
    "domestic helper registration": [
        "domestic helper", "maid registration", "house help",
    ],
    "pension": [
        "pension", "pension book", "retirement",
        "پنشن",
    ],
    "electricity connection": [
        "electricity", "bijli connection", "new connection", "meter",
        "بجلی کنکشن",
        "bijli", "wapda", "lesco", "iesco", "fesco", "gepco", "hesco", "sepco", "qesco", "pesco", "meuco",
    ],
    "gas connection": [
        "gas connection", "sui gas", "new gas connection",
        "گیس کنکشن", "سوئی گیس",
        "sui gas", "sgc",
    ],
}

# ---------------------------------------------------------------------------
# Province keywords
# ---------------------------------------------------------------------------

PROVINCE_MAP: dict[str, list[str]] = {
    "Punjab": [
        "punjab", "panjab", "پنجاب", "pnjab",
        "lahore", "lahor", "لاہور",
        "rawalpindi", "pindi", "راولپنڈی",
        "faisalabad", "فیصل آباد",
        "multan", "ملتان",
        "gujranwala", "گوجرانوالہ",
        "sialkot", "سیالکوٹ",
        "bahawalpur", "بہاولپور",
    ],
    "Sindh": [
        "sindh", "sind", "سندھ", "سنده",
        "karachi", "کراچی",
        "hyderabad", "حیدرآباد",
        "sukkur", "سکھر",
        "larkana", "لاڑکانہ",
    ],
    "KPK": [
        "kpk", "khyber", "pakhtunkhwa", "khyber pakhtunkhwa",
        "خیبر پختونخوا", "صوبہ سرحد", "nwfp",
        "peshawar", "پشاور",
        "abbottabad", "ایبٹ آباد",
        "mardan", "مردان",
        "swat", "سوات",
    ],
    "Balochistan": [
        "balochistan", "baluchistan", "بلوچستان",
        "quetta", "کوئٹہ",
        "gwadar", "گوادر",
    ],
    "ICT": [
        "islamabad", "ict", "capital", "اسلام آباد", "فاطمہ",
        "federal capital",
    ],
    "AJK": [
        "azad kashmir", "ajk", "kashmir", "آزاد کشمیر", "کشمیر",
        "muzaffarabad", "مظفرآباد",
    ],
    "Gilgit-Baltistan": [
        "gilgit", "baltistan", "gb", "گلگت", "بلتستان",
        "northern areas",
    ],
}

# ---------------------------------------------------------------------------
# Intent keywords
# ---------------------------------------------------------------------------

INTENT_MAP: dict[str, list[str]] = {
    "requirements": [
        "requirements", "documents needed", "what do i need", "required",
        "kya chahiye", "kya lagega", "kya darkar", "zaruri kagzat",
        "کن دستاویزات", "کیا ضرورت", "کیا چاہیے",
        "kaun se kagaz", "kya kagaz",
    ],
    "fee": [
        "fee", "cost", "price", "kitna lagega", "kitne ka", "charges",
        "فیس", "کتنے", "قیمت", "خرچہ",
        "kitne paise", "paise", "rupey", "paisa",
    ],
    "steps": [
        "steps", "procedure", "process", "how to", "how do i", "kaise",
        "kya tarika", "kis tarah", "tarika",
        "طریقہ", "کیسے", "عمل", "مرحلے",
        "apply kaise", "apply karna", "banwana", "banane ka",
    ],
    "processing_time": [
        "time", "how long", "kitna time", "kitne din", "duration",
        "کتنے دن", "کتنا وقت", "مدت",
        "kitne din mein", "kab milega", "waiting",
    ],
    "eligibility": [
        "eligible", "eligibility", "who can", "qualification", "kaun",
        "کون", "اہلیت", "شرائط",
        "kaun banwa sakta", "shart",
    ],
    "location": [
        "where", "kahan", "کہاں", "office", "daftar", "دفتر",
        "kis jagah", "address", "pata",
    ],
    "application_method": [
        "online", "apply", "form", "آن لائن", "درخواست", "فارم",
        "apply kaise", "form kahan",
    ],
    "renewal": [
        "renew", "renewal", "renovate", "تجدید", "نیا کرنا",
        "dobara banwana", "phir se",
    ],
    "status": [
        "status", "track", "check", "حالت", "ٹریک",
        "kahan tak", "kitna hua",
    ],
}

# ---------------------------------------------------------------------------
# Roman Urdu question words → English intent mapping
# ---------------------------------------------------------------------------

ROMAN_URDU_PATTERNS: list[tuple[str, str]] = [
    # (pattern, normalized_meaning)
    (r"\b(kaise|kese|kaisy|کیسے)\b", "how"),
    (r"\b(kya|کیا)\b", "what"),
    (r"\b(kahan|kaha|کہاں)\b", "where"),
    (r"\b(kab|کب)\b", "when"),
    (r"\b(kitna|kitne|کتنا|کتنے)\b", "how_much"),
    (r"\b(kaun|kon|کون)\b", "who"),
    (r"\b(kyun|kyon|کیوں)\b", "why"),
    (r"\b(banwana|banane|بنوانا|بنانے)\b", "make"),
    (r"\b(milega|milegi|ملے گا|ملے گی)\b", "get"),
    (r"\b(lagega|lagegi|لگے گا|لگے گی)\b", "cost_or_time"),
    (r"\b(chahiye|chahye|چاہیے)\b", "need"),
    (r"\b(tarika|tareeqa|طریقہ)\b", "method"),
    (r"\b(darkar|ضرورت)\b", "required"),
]


def parse_query(query: str) -> dict[str, Any]:
    """Parse a user query using fast heuristics (no LLM call).

    Returns:
        dict with keys: service, province, city, intent, language, raw_query
    """
    query_lower = query.lower().strip()

    # Detect language
    language = _detect_language(query)

    # Extract components
    service = _extract_service(query_lower)
    province = _extract_province(query_lower)
    city = _extract_city(query_lower)
    intent = _extract_intent(query_lower)

    # If no intent found, default to general
    if not intent:
        intent = "general"

    result = {
        "service": service,
        "province": province,
        "city": city,
        "intent": intent,
        "language": language,
        "raw_query": query,
    }

    logger.info("Query parsed (heuristic): %s", result)
    return result


def _detect_language(query: str) -> str:
    """Detect if the query is in English, Roman Urdu, or Urdu script."""
    # Check for Urdu script characters (Unicode range 0x0600–0x06FF)
    urdu_chars = len(re.findall(r"[\u0600-\u06FF]", query))
    total_chars = len(query.strip())

    if total_chars == 0:
        return "english"

    urdu_ratio = urdu_chars / total_chars

    if urdu_ratio > 0.2:
        return "urdu"

    # Check for Roman Urdu patterns
    for pattern, _ in ROMAN_URDU_PATTERNS:
        if re.search(pattern, query.lower()):
            # Additional Roman Urdu indicators
            roman_urdu_words = [
                "kya", "kaise", "kahan", "kab", "kitna", "kaun",
                "hai", "hain", "kar", "karo", "karna",
                "mein", "main", "mujhe", "hum", "tum", "aap",
                "ke", "ki", "ka", "ko", "se", "mein",
                "bhi", "nahi", "nahin", "agar", "toh",
                "banwa", "banwana", "mil", "milega",
                "lagega", "chahiye", "darkar",
            ]
            words = query.lower().split()
            roman_count = sum(1 for w in words if w in roman_urdu_words)
            if roman_count >= 2:
                return "roman_urdu"
            # Even one Roman Urdu word with non-English structure
            if roman_count >= 1 and any(w in ["hai", "hain", "kar", "karo"] for w in words):
                return "roman_urdu"

    return "english"


def _extract_service(query: str) -> str | None:
    """Extract the government service being asked about."""
    best_match: str | None = None
    best_score = 0

    for service, keywords in SERVICE_MAP.items():
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in query:
                # Prefer longer matches (more specific)
                score = len(kw_lower)
                if score > best_score:
                    best_score = score
                    best_match = service

    return best_match


def _extract_province(query: str) -> str | None:
    """Extract the Pakistani province mentioned."""
    for province, keywords in PROVINCE_MAP.items():
        for kw in keywords:
            if kw.lower() in query:
                return province
    return None


def _extract_city(query: str) -> str | None:
    """Extract a specific city if mentioned."""
    cities: dict[str, list[str]] = {
        "Rawalpindi": ["rawalpindi", "pindi", "راولپنڈی"],
        "Islamabad": ["islamabad", "اسلام آباد"],
        "Lahore": ["lahore", "lahor", "لاہور"],
        "Karachi": ["karachi", "کراچی"],
        "Faisalabad": ["faisalabad", "فیصل آباد"],
        "Multan": ["multan", "ملتان"],
        "Peshawar": ["peshawar", "پشاور"],
        "Quetta": ["quetta", "کوئٹہ"],
        "Hyderabad": ["hyderabad", "حیدرآباد"],
        "Sialkot": ["sialkot", "سیالکوٹ"],
        "Gujranwala": ["gujranwala", "گوجرانوالہ"],
        "Bahawalpur": ["bahawalpur", "بہاولپور"],
        "Abbottabad": ["abbottabad", "ایبٹ آباد"],
        "Mardan": ["mardan", "مردان"],
        "Sukkur": ["sukkur", "سکھر"],
        "Larkana": ["larkana", "لاڑکانہ"],
    }

    for city, keywords in cities.items():
        for kw in keywords:
            if kw.lower() in query:
                return city
    return None


def _extract_intent(query: str) -> str | None:
    """Extract what the user wants to know."""
    best_match: str | None = None
    best_score = 0

    for intent, keywords in INTENT_MAP.items():
        for kw in keywords:
            if kw.lower() in query:
                score = len(kw)
                if score > best_score:
                    best_score = score
                    best_match = intent

    return best_match


def build_search_keywords(query: str, parsed: dict[str, Any]) -> list[str]:
    """Build a list of search keywords from the parsed query.

    Useful for keyword search and web search queries.
    """
    keywords: list[str] = []

    if parsed.get("service"):
        keywords.append(parsed["service"])
    if parsed.get("province"):
        keywords.append(parsed["province"])
    if parsed.get("city"):
        keywords.append(parsed["city"])

    # If no structured data was extracted, use the raw query
    if not keywords:
        # Remove common stop words and short words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "i", "me", "my", "we", "our", "you", "your", "he", "she",
            "it", "they", "them", "this", "that", "these", "those",
            "how", "what", "where", "when", "why", "who", "which",
            "kya", "kaise", "kahan", "kab", "kaun", "kitna",
            "hai", "hain", "kar", "mein", "ko", "se", "ke",
        }
        words = re.findall(r"\w+", query.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]

    return keywords[:5]  # max 5 keywords
