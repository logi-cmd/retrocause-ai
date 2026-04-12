"""DuckDuckGo HTML search adapter."""

from __future__ import annotations

import logging
import os
import re
import time
from html.parser import HTMLParser
from urllib.parse import unquote_plus, urlparse

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

_DD_URL = "https://html.duckduckgo.com/html/"
_TIMEOUT = 5.0
_DISABLE_SECONDS = 90.0
_PAGE_FETCH_LIMIT = 2
_PAGE_CACHE_TTL = 900.0
_QUERY_CACHE_TTL = 600.0
_DOMAIN_COOLDOWN = 15.0
_disabled_until = 0.0
_page_cache: dict[str, tuple[float, str]] = {}
_domain_fetch_at: dict[str, float] = {}
_query_cache: dict[str, tuple[float, list[SearchResult]]] = {}
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_DEFAULT_TRUSTED_DOMAINS = {
    "arxiv.org",
    "nature.com",
    "science.org",
    "nih.gov",
    "who.int",
    "faa.gov",
    "ntsb.gov",
    "icao.int",
    "gov.uk",
    "europa.eu",
    "reuters.com",
    "apnews.com",
    "bbc.com",
}


class _DDGResultParser(HTMLParser):
    """Very small DDG HTML parser for result title/snippet extraction."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._in_result = False
        self._current_url = ""
        self._current_title = ""
        self._current_snippet = ""
        self._capture = ""
        self._capture_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        class_names = set((attr_dict.get("class") or "").split())

        if tag == "div" and "result" in class_names:
            self._in_result = True
            self._current_url = ""
            self._current_title = ""
            self._current_snippet = ""
            return

        if not self._in_result:
            return

        if tag == "a" and "result__a" in class_names:
            href = attr_dict.get("href", "")
            if href:
                match = re.search(r"uddg=([^&]+)", href)
                self._current_url = unquote_plus(match.group(1)) if match else href
            self._capture = "title"
            self._capture_buf = []

        if tag == "a" and "result__snippet" in class_names:
            self._capture = "snippet"
            self._capture_buf = []

    def handle_endtag(self, tag: str) -> None:
        if self._capture == "title" and tag == "a":
            self._current_title = " ".join(self._capture_buf).strip()
            self._capture = ""
            self._capture_buf = []
        elif self._capture == "snippet" and tag == "a":
            self._current_snippet = " ".join(self._capture_buf).strip()
            self._capture = ""
            self._capture_buf = []

        if tag == "div" and self._in_result and self._current_title:
            self.results.append(
                {
                    "title": self._current_title,
                    "url": self._current_url,
                    "snippet": self._current_snippet,
                }
            )
            self._in_result = False

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._capture_buf.append(data.strip())


def _clean_html(html: str) -> str:
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    html = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", html)
    html = re.sub(r"(?is)<svg.*?>.*?</svg>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;|&#160;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def _extract_main_text(html: str, minimum_length: int = 500) -> str:
    article_match = re.search(r"(?is)<article.*?>(.*?)</article>", html)
    if article_match:
        article_text = _clean_html(article_match.group(1))
        if len(article_text) >= minimum_length:
            return article_text

    paragraph_blocks = re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", html)
    paragraph_text = " ".join(_clean_html(block) for block in paragraph_blocks)
    if len(paragraph_text) >= minimum_length:
        return paragraph_text

    body_match = re.search(r"(?is)<body.*?>(.*?)</body>", html)
    if body_match:
        body_text = _clean_html(body_match.group(1))
        if len(body_text) >= minimum_length:
            return body_text

    return _clean_html(html)


def _should_fetch_page(url: str) -> bool:
    if not url.startswith("http"):
        return False
    host = urlparse(url).netloc.lower()
    if not host:
        return False
    blocked_hosts = {"duckduckgo.com", "html.duckduckgo.com"}
    return host not in blocked_hosts


def _trusted_domains() -> set[str]:
    configured = {
        item.strip().lower()
        for item in os.environ.get("RETROCAUSE_TRUSTED_DOMAINS", "").split(",")
        if item.strip()
    }
    return _DEFAULT_TRUSTED_DOMAINS | configured


def _normalized_host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _is_trusted_domain(url: str) -> bool:
    host = _normalized_host(url)
    if not host:
        return False
    trusted = _trusted_domains()
    return any(host == domain or host.endswith(f".{domain}") for domain in trusted)


def _domain_rank(url: str) -> float:
    host = _normalized_host(url)
    if not host:
        return 0.0
    score = 0.0
    if _is_trusted_domain(url):
        score += 3.0
    if host.endswith(".gov") or ".gov." in host:
        score += 2.0
    if host.endswith(".edu") or ".edu." in host:
        score += 1.5
    if host.endswith(".org"):
        score += 0.4
    return score


def _cache_key(query: str, max_results: int) -> str:
    return f"{query.strip().lower()}::{max_results}"


def _fetch_page_content(url: str) -> str | None:
    now = time.time()
    cached = _page_cache.get(url)
    if cached and now - cached[0] <= _PAGE_CACHE_TTL:
        return cached[1]

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if not domain:
        return None

    last_fetch_at = _domain_fetch_at.get(domain, 0.0)
    if now - last_fetch_at < _DOMAIN_COOLDOWN:
        return None

    try:
        response = httpx.get(
            url,
            timeout=_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.info("Page fetch skipped for %s: %s", url, exc)
        _domain_fetch_at[domain] = time.time()
        return None

    _domain_fetch_at[domain] = time.time()
    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type:
        return None

    text = _extract_main_text(response.text)
    if len(text) < 280:
        return None

    _page_cache[url] = (time.time(), text)
    return text


class WebSearchAdapter(BaseSourceAdapter):
    """DuckDuckGo HTML adapter with a short-lived circuit breaker."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.NEWS

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        global _disabled_until
        cache_key = _cache_key(query, max_results)
        cached = _query_cache.get(cache_key)
        if cached and time.time() - cached[0] <= _QUERY_CACHE_TTL:
            return cached[1]

        if time.time() < _disabled_until:
            logger.info("DuckDuckGo search temporarily disabled after recent failures")
            if cached:
                return cached[1]
            return []

        try:
            response = httpx.get(
                _DD_URL,
                params={"q": query},
                timeout=_TIMEOUT,
                headers={
                    "User-Agent": _USER_AGENT,
                    "Referer": "https://html.duckduckgo.com/",
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            _disabled_until = time.time() + _DISABLE_SECONDS
            logger.warning("DuckDuckGo request failed: %s", exc)
            if cached:
                return cached[1]
            return []

        results = self._parse_html(response.text, max_results)
        if results:
            _query_cache[cache_key] = (time.time(), results)
        return results

    @staticmethod
    def _parse_html(html: str, max_results: int) -> list[SearchResult]:
        parser = _DDGResultParser()
        try:
            parser.feed(html)
        except Exception as exc:
            logger.warning("DDG HTML parse failed: %s", exc)
            return []

        ranked_items = sorted(
            parser.results,
            key=lambda item: (_domain_rank(item.get("url", "")), len(item.get("snippet", ""))),
            reverse=True,
        )

        results: list[SearchResult] = []
        for index, item in enumerate(ranked_items[:max_results]):
            title = item.get("title", "").strip()
            url = item.get("url", "").strip()
            snippet = item.get("snippet", "").strip()
            if not title:
                continue

            metadata: dict = {}
            trusted_domain = _is_trusted_domain(url)
            metadata["source_domain"] = _normalized_host(url)
            metadata["trusted_domain"] = trusted_domain
            if index < _PAGE_FETCH_LIMIT and _should_fetch_page(url):
                page_content = _fetch_page_content(url)
                if page_content:
                    metadata["page_content"] = page_content[:12000]
                    metadata["content_quality"] = "trusted_fulltext" if trusted_domain else "fulltext"
                else:
                    metadata["content_quality"] = "trusted_snippet" if trusted_domain else "snippet"
            else:
                metadata["content_quality"] = "trusted_snippet" if trusted_domain else "snippet"

            results.append(
                SearchResult(
                    title=title,
                    content=snippet,
                    url=url,
                    source_type=EvidenceType.NEWS,
                    metadata=metadata,
                )
            )
        return results
