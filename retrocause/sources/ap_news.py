"""AP News search adapter for time-sensitive news retrieval."""

from __future__ import annotations

import html
import logging
import re
import time

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult
from retrocause.sources.web import _extract_main_text

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://apnews.com/search"
_TIMEOUT = 12.0
_QUERY_CACHE_TTL = 600.0
_PAGE_CACHE_TTL = 900.0
_query_cache: dict[tuple[str, int], tuple[float, list[SearchResult]]] = {}
_page_cache: dict[str, tuple[float, tuple[str, str]]] = {}
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_STOPWORDS = {"the", "and", "for", "with", "from", "what", "why", "did", "does", "this"}


def _query_tokens(query: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z]{3,}", query.lower())
        if token not in _STOPWORDS
    }


def _url_rank(url: str, query_tokens: set[str]) -> tuple[int, str]:
    lowered = url.lower()
    score = sum(1 for token in query_tokens if token in lowered)
    return score, lowered


def _fetch_article(url: str) -> tuple[str, str] | None:
    cached = _page_cache.get(url)
    if cached and time.time() - cached[0] <= _PAGE_CACHE_TTL:
        return cached[1]

    try:
        response = httpx.get(
            url,
            timeout=_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.info("AP article fetch failed for %s: %s", url, exc)
        return None

    page_title_match = re.search(r'<meta property="og:title" content="(.*?)"', response.text)
    if page_title_match:
        title = html.unescape(page_title_match.group(1)).strip()
    else:
        title_match = re.search(r"<title>(.*?)</title>", response.text, re.S)
        title = html.unescape(title_match.group(1)).strip() if title_match else ""

    content = _extract_main_text(response.text)
    if len(content) < 280:
        return None

    payload = (title, content)
    _page_cache[url] = (time.time(), payload)
    return payload


class APNewsAdapter(BaseSourceAdapter):
    @property
    def name(self) -> str:
        return "ap_news"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.NEWS

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        cache_key = (query.strip().lower(), max_results)
        cached = _query_cache.get(cache_key)
        if cached and time.time() - cached[0] <= _QUERY_CACHE_TTL:
            return cached[1]

        try:
            response = httpx.get(
                _SEARCH_URL,
                params={"q": query},
                timeout=_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": _USER_AGENT},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("AP News search failed: %s", exc)
            return cached[1] if cached else []

        urls = re.findall(r"https://apnews.com/article/[a-z0-9-]+", response.text, re.I)
        deduped_urls: list[str] = []
        seen: set[str] = set()
        for url in urls:
            key = url.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped_urls.append(url)

        query_tokens = _query_tokens(query)
        ranked_urls = sorted(
            deduped_urls,
            key=lambda item: _url_rank(item, query_tokens),
            reverse=True,
        )

        results: list[SearchResult] = []
        for url in ranked_urls[: max_results * 3]:
            article = _fetch_article(url)
            if article is None:
                continue
            title, content = article
            lowered_title = f"{title} {content[:400]}".lower()
            if query_tokens:
                overlap = sum(1 for token in query_tokens if token in lowered_title)
                if overlap == 0:
                    continue
            results.append(
                SearchResult(
                    title=title or url.rsplit("/", 1)[-1].replace("-", " "),
                    content=title or "",
                    url=url,
                    source_type=EvidenceType.NEWS,
                    metadata={
                        "source_domain": "apnews.com",
                        "trusted_domain": True,
                        "page_content": content[:12000],
                        "content_quality": "trusted_fulltext",
                    },
                )
            )
            if len(results) >= max_results:
                break

        if results:
            _query_cache[cache_key] = (time.time(), results)
        return results
