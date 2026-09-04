"""Deep web scraper — fetches full page content from government websites.

When the database doesn't have enough information, instead of relying on
200-character DuckDuckGo snippets, we go directly to the actual government
web page and extract the full content for the LLM to use.

This is the single biggest improvement for real-world usefulness.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_PAGE_CHARS = 8000  # Limit per page to keep context manageable
FETCH_TIMEOUT = 15  # seconds per page
MAX_PAGES_PER_QUERY = 3  # Don't fetch too many pages

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
}

# Tags to strip from HTML (nav, footer, ads, etc.)
_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "iframe",
               "noscript", "svg", "form", "button"}

# Common CSS classes/IDs that indicate non-content elements
_NOISE_PATTERNS = re.compile(
    r"(menu|sidebar|footer|header|nav|widget|comment|social|share|"
    r"cookie|popup|modal|banner|ad-|advert|related)",
    re.IGNORECASE,
)

# Cache to avoid re-fetching the same page within a session
_page_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scrape_page(url: str, title: str | None = None) -> dict[str, Any] | None:
    """Fetch a URL and extract the main text content.

    Returns:
        {
            "url": str,
            "title": str,
            "content": str,  # Clean extracted text
            "char_count": int,
            "content_hash": str,
        }
        or None if fetch fails.
    """
    # Check cache
    cached = _page_cache.get(url)
    if cached:
        content, ts = cached
        if time.time() - ts < CACHE_TTL:
            logger.debug("Cache hit for %s", url)
            return {
                "url": url,
                "title": title or url,
                "content": content,
                "char_count": len(content),
                "content_hash": hashlib.md5(content.encode()).hexdigest(),
            }

    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=FETCH_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None

    content_type = resp.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        logger.warning("Non-HTML content from %s: %s", url, content_type)
        return None

    html = resp.text

    # Extract content
    content = _extract_content(html)
    if not content or len(content) < 100:
        # Page might be JS-rendered or have no useful content
        logger.info("Low content from %s (%d chars) — page may be JS-rendered", url, len(content or ""))
        # Try basic extraction as fallback
        content = _basic_extract(html)
        if not content or len(content) < 50:
            return None

    # Truncate to max chars
    content = content[:MAX_PAGE_CHARS]

    # Cache the result
    _page_cache[url] = (content, time.time())

    result = {
        "url": url,
        "title": title or _extract_title(html) or url,
        "content": content,
        "char_count": len(content),
        "content_hash": hashlib.md5(content.encode()).hexdigest(),
    }
    logger.info("Scraped %s: %d chars", url, result["char_count"])
    return result


def scrape_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scrape multiple pages and return successful results.

    Args:
        pages: list of {"url": str, "title": str, ...}

    Returns list of scrape results.
    """
    results: list[dict[str, Any]] = []
    for page in pages[:MAX_PAGES_PER_QUERY]:
        result = scrape_page(page["url"], page.get("title"))
        if result:
            result["page_title"] = page.get("title", "")
            result["province"] = page.get("province")
            results.append(result)
    return results


def scrape_search_results(search_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deep-scrape the top web search results to get full page content.

    Takes DuckDuckGo results (which only have snippets) and fetches the
    actual pages for richer context.

    Only scrapes trusted government sources to avoid wasting time on blogs.
    """
    if not search_results:
        return []

    # Only scrape trusted gov results
    trusted = [r for r in search_results if r and isinstance(r, dict) and r.get("trusted")]
    if not trusted:
        # If no trusted sources, scrape the first 2 results anyway
        trusted = [r for r in search_results[:2] if r and isinstance(r, dict)]

    if not trusted:
        return []

    results: list[dict[str, Any]] = []
    for sr in trusted[:MAX_PAGES_PER_QUERY]:
        url = sr.get("url")
        if not url:
            continue
        result = scrape_page(url, sr.get("title"))
        if result:
            result["trusted"] = sr.get("trusted", False)
            result["source_name"] = sr.get("source_name", "Web Source")
            results.append(result)

    return results


# ---------------------------------------------------------------------------
# HTML content extraction
# ---------------------------------------------------------------------------

def _extract_content(html: str) -> str:
    """Extract main text content from HTML.

    Uses BeautifulSoup if available, falls back to regex-based extraction.
    """
    try:
        from bs4 import BeautifulSoup
        return _bs_extract(html)
    except ImportError:
        return _regex_extract(html)


def _bs_extract(html: str) -> str:
    """Extract content using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Remove noise elements
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove elements with noise-related classes/IDs
    for tag in soup.find_all(True):
        classes = " ".join(tag.get("class", []))
        tag_id = tag.get("id", "")
        if _NOISE_PATTERNS.search(classes) or _NOISE_PATTERNS.search(tag_id):
            tag.decompose()

    # Try to find the main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find("div", class_=re.compile(r"content|main|article|post|entry", re.I))
        or soup.find("div", id=re.compile(r"content|main|article|post|entry", re.I))
        or soup.body
        or soup
    )

    # Extract text, preserving structure
    lines: list[str] = []
    for element in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "div", "span"]):
        text = element.get_text(strip=True)
        if not text or len(text) < 3:
            continue
        # Skip very short noise elements
        if element.name in ("span", "div") and len(text) < 10:
            continue
        # Add structure markers
        if element.name in ("h1", "h2", "h3", "h4"):
            lines.append(f"\n## {text}\n")
        elif element.name == "li":
            lines.append(f"  - {text}")
        elif element.name in ("td", "th"):
            lines.append(text)
        else:
            lines.append(text)

    content = "\n".join(lines)

    # Clean up multiple newlines
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r" {2,}", " ", content)

    return content.strip()


def _regex_extract(html: str) -> str:
    """Fallback: extract text using regex (no BeautifulSoup dependency)."""
    # Remove script and style blocks
    html = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)

    # Decode common entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")

    # Clean whitespace
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _basic_extract(html: str) -> str:
    """Very basic extraction for pages where main extraction fails."""
    # Just get all text between body tags
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.S | re.I)
    if body_match:
        text = re.sub(r"<[^>]+>", " ", body_match.group(1))
        text = re.sub(r"\s+", " ", text).strip()
        return text
    # Last resort: strip all tags
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_title(html: str) -> str | None:
    """Extract the page title from HTML."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if match:
        title = match.group(1).strip()
        # Clean up common suffixes
        for suffix in [" | ", " - ", " — "]:
            if suffix in title:
                title = title.split(suffix)[0].strip()
        return title
    return None
