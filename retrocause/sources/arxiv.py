"""ArXiv 论文搜索适配器"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

# ArXiv Atom feed 命名空间
_ATOM_NS = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"

_API_URL = "https://export.arxiv.org/api/query"
_TIMEOUT = 15.0


class ArxivSourceAdapter(BaseSourceAdapter):
    """ArXiv API 适配器 — 免费无需密钥"""

    @property
    def name(self) -> str:
        return "arxiv"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.LITERATURE

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """调用 ArXiv API 搜索论文，返回 SearchResult 列表。"""
        try:
            response = httpx.get(
                _API_URL,
                params={
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": "relevance",
                },
                timeout=_TIMEOUT,
                headers={"User-Agent": "RetroCause/0.1 (research tool)"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("ArXiv 请求失败: %s", exc)
            return []

        return self._parse_xml(response.text)

    @staticmethod
    def _parse_xml(raw_xml: str) -> list[SearchResult]:
        """解析 ArXiv Atom XML 响应。"""
        results: list[SearchResult] = []
        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError as exc:
            logger.warning("ArXiv XML 解析失败: %s", exc)
            return []

        for entry in root.findall(f"{_ATOM_NS}entry"):
            title_el = entry.find(f"{_ATOM_NS}title")
            summary_el = entry.find(f"{_ATOM_NS}summary")
            id_el = entry.find(f"{_ATOM_NS}id")
            published_el = entry.find(f"{_ATOM_NS}published")

            if title_el is None or id_el is None:
                continue

            title = (title_el.text or "").strip().replace("\n", " ")
            url = (id_el.text or "").strip()
            content = (
                (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
            )
            published = (published_el.text or "").strip()[:10] if published_el is not None else ""

            authors: list[str] = []
            for author_el in entry.findall(f"{_ATOM_NS}author"):
                name_el = author_el.find(f"{_ATOM_NS}name")
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())

            metadata: dict = {}
            if published:
                metadata["year"] = published[:4]
            if authors:
                metadata["authors"] = authors
            if published:
                metadata["published"] = published

            results.append(
                SearchResult(
                    title=title,
                    content=content,
                    url=url,
                    source_type=EvidenceType.LITERATURE,
                    metadata=metadata,
                )
            )

        return results
