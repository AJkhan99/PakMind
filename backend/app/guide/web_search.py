"""Live web search using Serper.dev (primary) with DuckDuckGo fallback.

Used as a fallback when the database doesn't have enough verified information.
Searches for official Pakistani government sources in real-time.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Trusted domains — only results from these domains are considered authoritative
TRUSTED_DOMAINS = [
    "gov.pk",
    "punjab.gov.pk",
    "sindh.gov.pk",
    "kp.gov.pk",
    "balochistan.gov.pk",
    "islamabad.gov.pk",
    "nadra.gov.pk",
    "dgip.gov.pk",
    "fbr.gov.pk",
    "excise.punjab.gov.pk",
    "punjabpolice.gov.pk",
    "sindhpolice.gov.pk",
    "dcrawalpindi.punjab.gov.pk",
    "citizenportal.gov.pk",
    "passport.gov.pk",
    "moipp.gov.pk",
    "nhmp.gov.pk",
    "hec.gov.pk",
    "pakistan.gov.pk",
]


def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the web for Pakistani government service information.

    Tries Serper.dev first (if API key configured), falls back to DuckDuckGo.
    Returns a list of { title, url, snippet, source_name, trusted } dicts.
    """
    # Try Serper.dev first
    from app.config import get_settings
    settings = get_settings()

    if settings.serper_api_key:
        results = _serper_search(query, max_results, settings.serper_api_key)
        if results:
            return results
        logger.info("Serper returned no results, falling back to DuckDuckGo")

    # Fallback to DuckDuckGo
    return _duckduckgo_search(query, max_results)


def _serper_search(query: str, max_results: int, api_key: str) -> list[dict[str, Any]]:
    """Search using Serper.dev Google Search API."""
    import httpx

    enhanced_query = f"{query} Pakistan government"

    try:
        response = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": enhanced_query, "num": max_results * 2, "gl": "pk", "hl": "en"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.error("Serper search failed: %s", exc)
        return []

    results: list[dict[str, Any]] = []
    for r in data.get("organic", [])[:max_results * 2]:
        url = r.get("link", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        trusted = any(domain in url.lower() for domain in TRUSTED_DOMAINS)

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "source_name": _domain_to_name(url),
            "trusted": trusted,
        })

    # Prefer trusted sources first
    results.sort(key=lambda r: not r["trusted"])
    return results[:max_results]


def _duckduckgo_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search using DuckDuckGo (free, no API key needed)."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("ddgs (or duckduckgo-search) not installed — web search unavailable")
            return []

    enhanced_query = f"{query} site:gov.pk Pakistan government"

    results: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(enhanced_query, max_results=max_results * 2):
                url = r.get("href", "")
                title = r.get("title", "")
                snippet = r.get("body", "")

                trusted = any(domain in url.lower() for domain in TRUSTED_DOMAINS)

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source_name": _domain_to_name(url),
                    "trusted": trusted,
                })

    except Exception as exc:
        logger.error("DuckDuckGo search failed: %s", exc)
        return []

    # Prefer trusted sources first, then others
    results.sort(key=lambda r: not r["trusted"])
    return results[:max_results]


def search_web_for_service(service: str, province: str | None = None) -> list[dict[str, Any]]:
    """Targeted web search for a specific government service.

    Constructs a query optimized for finding official service pages.
    """
    parts = [service, "Pakistan"]
    if province:
        parts.append(province)
    parts.extend(["requirements", "procedure", "fee"])

    query = " ".join(parts)
    return search_web(query, max_results=5)


def _domain_to_name(url: str) -> str:
    """Extract a human-readable source name from a URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")

        # Map known domains to friendly names
        domain_names = {
            "punjab.gov.pk": "Government of Punjab",
            "sindh.gov.pk": "Government of Sindh",
            "kp.gov.pk": "Government of KPK",
            "islamabad.gov.pk": "ICT Administration",
            "nadra.gov.pk": "NADRA",
            "dgip.gov.pk": "DG Immigration & Passports",
            "fbr.gov.pk": "Federal Board of Revenue",
            "excise.punjab.gov.pk": "Punjab Excise & Taxation",
            "punjabpolice.gov.pk": "Punjab Police",
            "dcrawalpindi.punjab.gov.pk": "DC Rawalpindi",
            "citizenportal.gov.pk": "Pakistan Citizen Portal",
            "passport.gov.pk": "Passport Office",
            "moipp.gov.pk": "Ministry of Interior",
            "pakistan.gov.pk": "Government of Pakistan",
            "hec.gov.pk": "Higher Education Commission",
        }

        for d, name in domain_names.items():
            if d in domain:
                return name
        return domain
    except Exception:
        return "Web Source"
