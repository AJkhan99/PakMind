"""Web search for out-of-DB questions.

Primary: Serper.dev (Google results API, 2,500 free credits).
Fallback: DuckDuckGo HTML endpoint (no key, no quota, fragile parsing).

Also provides best-effort page-text fetching to enrich search snippets.
"""

from __future__ import annotations

import logging
import re
import html as _html
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

_RESULT_TAG_RE = re.compile(r'<a\b[^>]*class="result__a"[^>]*>(.*?)</a>', re.S)
_SNIPPET_RE = re.compile(r'<a\b[^>]*class="result__snippet"[^>]*>(.*?)</a>', re.S)
_HREF_RE = re.compile(r'href="([^"]+)"')
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def _strip_html(s: str) -> str:
    return _html.unescape(_TAG_RE.sub("", s)).strip()


def _decode_ddg_href(href: str) -> str | None:
    """Extract the real URL from a DuckDuckGo redirect href (uddg=...)."""
    if not href or "uddg=" not in href:
        return None
    try:
        from urllib.parse import parse_qs, unquote, urlparse

        if href.startswith("//"):
            href = "https:" + href
        qs = parse_qs(urlparse(href).query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    except Exception:
        pass
    return None


def search_duckduckgo(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search DuckDuckGo's HTML-only endpoint. No API key, no quota."""
    try:
        resp = httpx.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=_HEADERS,
            timeout=15,
            follow_redirects=True,
        )
    except Exception as exc:
        logger.warning("DDG search request failed: %s", exc)
        return []

    if resp.status_code != 200:
        logger.warning("DDG search returned status %s", resp.status_code)
        return []

    body = resp.text
    result_tags = _RESULT_TAG_RE.findall(body)
    snippet_tags = _SNIPPET_RE.findall(body)

    results: list[dict[str, str]] = []
    for i, tag in enumerate(result_tags):
        href_match = _HREF_RE.search(tag)
        if not href_match:
            continue
        real_url = _decode_ddg_href(href_match.group(1))
        if not real_url:
            continue
        title = _strip_html(tag)
        snippet = _strip_html(snippet_tags[i]) if i < len(snippet_tags) else ""
        results.append({"title": title, "url": real_url, "snippet": snippet})
        if len(results) >= max_results:
            break

    logger.info("DDG search for %r returned %d results", query, len(results))
    return results


def search_serper(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search Google via Serper.dev (2,500 free credits)."""
    from app.config import get_settings

    settings = get_settings()
    if not settings.serper_api_key or settings.serper_api_key.startswith("your_"):
        return []

    try:
        resp = httpx.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": settings.serper_api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": max_results},
            timeout=15,
        )
    except Exception as exc:
        logger.warning("Serper search request failed: %s", exc)
        return []

    if resp.status_code != 200:
        logger.warning("Serper search returned status %s", resp.status_code)
        return []

    results: list[dict[str, str]] = []
    for item in resp.json().get("organic", []):
        results.append(
            {
                "title": item.get("title") or "",
                "url": item.get("link") or "",
                "snippet": item.get("snippet") or "",
            }
        )
        if len(results) >= max_results:
            break

    logger.info("Serper search for %r returned %d results", query, len(results))
    return results


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Unified web search: Serper (primary) → DuckDuckGo HTML (fallback)."""
    results = search_serper(query, max_results=max_results)
    if results:
        return results
    logger.info("Serper unavailable/empty — falling back to DDG for: %s", query)
    return search_duckduckgo(query, max_results=max_results)


def fetch_page_text(url: str, max_chars: int = 3000) -> str:
    """Best-effort fetch of page text. Strips script/style blocks + tags.

    Used to enrich DDG snippets with actual page content for LLM context.
    Silently returns '' on any failure — best-effort, never critical.
    """
    try:
        resp = httpx.get(
            url, headers=_HEADERS, timeout=8, follow_redirects=True
        )
    except Exception:
        return ""
    if resp.status_code != 200:
        return ""
    text = _SCRIPT_STYLE_RE.sub("", resp.text)
    text = _strip_html(text)
    return text[:max_chars]
