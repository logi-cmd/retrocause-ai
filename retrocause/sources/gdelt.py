"""GDELT article-list adapter for time-sensitive news retrieval."""

from __future__ import annotations

import logging
import re
import time

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult
from retrocause.sources.web import _fetch_page_content, _is_trusted_domain, _normalized_host

logger = logging.getLogger(__name__)

_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_TIMEOUT = 12.0
_MIN_INTERVAL_SECONDS = 5.5
_DISABLE_SECONDS = 180.0
_PAGE_FETCH_LIMIT = 2
_QUERY_CACHE_TTL = 600.0
_last_request_at = 0.0
_disabled_until = 0.0
_query_cache: dict[tuple[str, int], tuple[float, list[SearchResult]]] = {}


def _rank_article(article: dict) -> tuple[float, str]:
    url = str(article.get("url", ""))
    domain = _normalized_host(url)
    score = 0.0
    if article.get("language") == "English":
        score += 1.0
    if _is_trusted_domain(url):
        score += 3.0
    return score, domain


def _sanitize_query(query: str) -> str:
    sanitized = re.sub(r"\bUS\b", "United States", query)
    sanitized = re.sub(r"\bU\.S\.\b", "United States", sanitized)
    return sanitized


class GdeltNewsAdapter(BaseSourceAdapter):
    @property
    def name(self) -> str:
        return "gdelt_news"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.NEWS

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        global _last_request_at, _disabled_until
        query = _sanitize_query(query)

        cache_key = (query.strip().lower(), max_results)
        cached = _query_cache.get(cache_key)
        now = time.time()
        if cached and now - cached[0] <= _QUERY_CACHE_TTL:
            return cached[1]

        if now < _disabled_until:
            logger.info("GDELT search temporarily disabled after recent failures")
            return cached[1] if cached else []

        remaining = _MIN_INTERVAL_SECONDS - (now - _last_request_at)
        if remaining > 0:
            time.sleep(remaining)

        try:
            data = self._request_articles(query, max_results)
        except (httpx.HTTPError, ValueError) as exc:
            _disabled_until = time.time() + _DISABLE_SECONDS
            logger.warning("GDELT request failed: %s", exc)
            return cached[1] if cached else []

        articles = data.get("articles") or []
        ranked_articles = sorted(articles, key=_rank_article, reverse=True)
        results: list[SearchResult] = []
        for index, article in enumerate(ranked_articles[:max_results]):
            url = str(article.get("url", "")).strip()
            title = str(article.get("title", "")).strip()
            if not url or not title:
                continue

            trusted_domain = _is_trusted_domain(url)
            metadata = {
                "published": str(article.get("seendate", ""))[:10],
                "source_domain": _normalized_host(url),
                "trusted_domain": trusted_domain,
            }
            if index < _PAGE_FETCH_LIMIT:
                page_content = _fetch_page_content(url)
                if page_content:
                    metadata["page_content"] = page_content[:12000]
                    metadata["content_quality"] = (
                        "trusted_fulltext" if trusted_domain else "fulltext"
                    )
                else:
                    metadata["content_quality"] = (
                        "trusted_snippet" if trusted_domain else "snippet"
                    )
            else:
                metadata["content_quality"] = "trusted_snippet" if trusted_domain else "snippet"

            results.append(
                SearchResult(
                    title=title,
                    content=title,
                    url=url,
                    source_type=EvidenceType.NEWS,
                    metadata=metadata,
                )
            )

        if results:
            _query_cache[cache_key] = (time.time(), results)
        return results

    @staticmethod
    def _request_articles(query: str, max_results: int) -> dict:
        global _last_request_at

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_results,
            "sort": "datedesc",
        }
        headers = {"User-Agent": "RetroCause/0.1 (research tool)"}

        response = httpx.get(_API_URL, params=params, timeout=_TIMEOUT, headers=headers)
        _last_request_at = time.time()
        if response.status_code == 429:
            time.sleep(_MIN_INTERVAL_SECONDS)
            response = httpx.get(_API_URL, params=params, timeout=_TIMEOUT, headers=headers)
            _last_request_at = time.time()
        response.raise_for_status()
        return response.json()
