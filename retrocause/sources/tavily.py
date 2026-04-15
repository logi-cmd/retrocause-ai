"""Optional Tavily search adapter for hosted retrieval."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

_API_URL = "https://api.tavily.com/search"
_TIMEOUT = 15.0


def _normalized_host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


class TavilySourceAdapter(BaseSourceAdapter):
    """Tavily Search API adapter, enabled only when an API key is provided."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = (api_key or os.environ.get("TAVILY_API_KEY", "")).strip()
        if not self._api_key:
            raise ValueError("TAVILY_API_KEY is required to use TavilySourceAdapter.")

    @property
    def name(self) -> str:
        return "tavily"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.NEWS

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        response = httpx.post(
            _API_URL,
            json={
                "query": query,
                "max_results": max_results,
                "include_raw_content": "text",
            },
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "RetroCause/0.1 (research tool)",
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            logger.warning("Tavily response JSON parse failed: %s", exc)
            raise

        results: list[SearchResult] = []
        for item in data.get("results") or []:
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            content = str(item.get("content", "")).strip()
            if not title or not url:
                continue

            raw_content = str(item.get("raw_content") or "").strip()
            published = str(
                item.get("published_date") or item.get("published") or ""
            ).strip()
            metadata = {
                "provider": "tavily",
                "source_domain": _normalized_host(url),
                "content_quality": "fulltext" if raw_content else "snippet",
                "cache_policy": "derived_cache_allowed",
            }
            if raw_content:
                metadata["page_content"] = raw_content[:12000]
            if published:
                metadata["published"] = published[:10]
            if item.get("score") is not None:
                metadata["score"] = item.get("score")

            results.append(
                SearchResult(
                    title=title,
                    content=content or title,
                    url=url,
                    source_type=EvidenceType.NEWS,
                    metadata=metadata,
                )
            )

            if len(results) >= max_results:
                break

        return results
