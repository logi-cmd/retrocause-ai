"""DuckDuckGo HTML 搜索适配器"""

from __future__ import annotations

import logging
import re
from html.parser import HTMLParser
from urllib.parse import unquote_plus

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

_DD_URL = "https://html.duckduckgo.com/html/"
_TIMEOUT = 15.0
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class _DDGResultParser(HTMLParser):
    """极简 DDG HTML 结果解析器 — 只提取第一条结果链接列表。"""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._in_result = False
        self._current_url: str = ""
        self._current_title: str = ""
        self._current_snippet: str = ""
        self._capture: str = ""
        self._capture_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)

        if tag == "div" and attr_dict.get("class") and "result" in (attr_dict.get("class") or ""):
            self._in_result = True
            self._current_url = ""
            self._current_title = ""
            self._current_snippet = ""
            return

        if not self._in_result:
            return

        if tag == "a" and "result__a" in (attr_dict.get("class") or ""):
            href = attr_dict.get("href", "")
            if href:
                # DDG 用 //uddg= 参数传递真实 URL
                m = re.search(r"uddg=([^&]+)", href)
                if m:
                    self._current_url = unquote_plus(m.group(1))
                else:
                    self._current_url = href
            self._capture = "title"
            self._capture_buf = []

        if tag == "a" and "result__snippet" in (attr_dict.get("class") or ""):
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


class WebSearchAdapter(BaseSourceAdapter):
    """DuckDuckGo HTML 搜索适配器 — 免费无需密钥"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.NEWS

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """用 DuckDuckGo HTML 版搜索，返回 SearchResult 列表。"""
        try:
            response = httpx.post(
                _DD_URL,
                data={"q": query},
                timeout=_TIMEOUT,
                headers={"User-Agent": _USER_AGENT},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("DuckDuckGo 请求失败: %s", exc)
            return []

        return self._parse_html(response.text, max_results)

    @staticmethod
    def _parse_html(html: str, max_results: int) -> list[SearchResult]:
        """解析 DuckDuckGo HTML 搜索结果。"""
        parser = _DDGResultParser()
        try:
            parser.feed(html)
        except Exception as exc:
            logger.warning("DDG HTML 解析失败: %s", exc)
            return []

        results: list[SearchResult] = []
        for item in parser.results[:max_results]:
            title = item.get("title", "").strip()
            url = item.get("url", "").strip()
            snippet = item.get("snippet", "").strip()
            if not title:
                continue
            results.append(
                SearchResult(
                    title=title,
                    content=snippet,
                    url=url,
                    source_type=EvidenceType.NEWS,
                    metadata={},
                )
            )
        return results
