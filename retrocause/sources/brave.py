"""Optional Brave Search API adapter for hosted retrieval."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

_API_URL = "https://api.search.brave.com/res/v1/web/search"
_TIMEOUT = 15.0


def _normalized_host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _published_date(value: object) -> str | None:
    text = str(value or "").strip()
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    return None


class BraveSearchSourceAdapter(BaseSourceAdapter):
    """Brave Search Web API adapter, enabled only when an API key is provided."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = (api_key or os.environ.get("BRAVE_SEARCH_API_KEY", "")).strip()
        if not self._api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY is required to use BraveSearchSourceAdapter.")

    @property
    def name(self) -> str:
        return "brave"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.NEWS

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        response = httpx.get(
            _API_URL,
            params={
                "q": query,
                "count": max(1, min(max_results, 20)),
            },
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self._api_key,
                "User-Agent": "RetroCause/0.1 (research tool)",
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            logger.warning("Brave response JSON parse failed: %s", exc)
            raise

        results: list[SearchResult] = []
        for item in (data.get("web") or {}).get("results") or []:
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            description = str(item.get("description", "")).strip()
            if not title or not url:
                continue

            metadata = {
                "provider": "brave",
                "source_domain": _normalized_host(url),
                "content_quality": "snippet",
                "cache_policy": "transient_results_only",
            }
            published = _published_date(item.get("age") or item.get("page_age"))
            if published:
                metadata["published"] = published

            results.append(
                SearchResult(
                    title=title,
                    content=description or title,
                    url=url,
                    source_type=EvidenceType.NEWS,
                    metadata=metadata,
                )
            )

            if len(results) >= max_results:
                break

        return results
