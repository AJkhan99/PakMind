"""Citation service — builds source citation objects from retrieved data."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def build_citations(ranked_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract unique source citations from ranked results.

    Returns a list of source objects: { title, url, source_name, last_verified }.
    Never fabricates URLs — only returns URLs present in the database records.
    """
    seen_urls: set[str] = set()
    citations: list[dict[str, Any]] = []

    for item in ranked_results:
        citation: dict[str, Any] | None = None

        if item.get("type") == "service":
            svc = item.get("service_data") or {}
            doc = svc.get("documents") or {}
            # Sources are nested inside documents (documents → sources)
            source = doc.get("sources") or {}

            url = doc.get("url") or source.get("url")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            citation = {
                "title": doc.get("title") or svc.get("name", "Government Service"),
                "url": url,
                "source_name": source.get("name", "Official Source"),
                "last_verified": doc.get("last_verified") or svc.get("last_verified"),
            }

        elif item.get("type") == "chunk":
            meta = item.get("metadata") or {}
            # Chunks may carry source info in metadata
            url = meta.get("source_url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                citation = {
                    "title": meta.get("title", "Government Document"),
                    "url": url,
                    "source_name": meta.get("source_name", "Official Source"),
                    "last_verified": meta.get("last_verified"),
                }

        elif item.get("type") == "gov_page":
            # Deep-scraped government pages (high-quality web source)
            gp = item.get("gov_page") or {}
            url = gp.get("url") or item.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                citation = {
                    "title": gp.get("title") or item.get("title", "Government Website"),
                    "url": url,
                    "source_name": gp.get("source_name", "Official Government Website"),
                    "last_verified": None,
                    "from_web": True,
                    "from_gov_page": True,
                    "trusted": True,
                }

        elif item.get("type") == "web":
            # Web search results (live internet fallback)
            wr = item.get("web_result") or {}
            url = wr.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                citation = {
                    "title": wr.get("title", "Web Source"),
                    "url": url,
                    "source_name": wr.get("source_name", "Web Search"),
                    "last_verified": None,
                    "from_web": True,
                    "trusted": wr.get("trusted", False),
                }

        elif item.get("type") == "video":
            # YouTube video results (supplementary guidance)
            wr = item.get("web_result") or {}
            url = wr.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                citation = {
                    "title": wr.get("title", "Video Guide"),
                    "url": url,
                    "source_name": "YouTube",
                    "last_verified": None,
                    "from_web": True,
                    "from_video": True,
                    "trusted": False,
                }

        if citation:
            citations.append(citation)

    return citations
