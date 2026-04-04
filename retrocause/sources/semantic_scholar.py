"""Semantic Scholar 论文搜索适配器"""

from __future__ import annotations

import logging

import httpx

from retrocause.models import EvidenceType
from retrocause.sources.base import BaseSourceAdapter, SearchResult

logger = logging.getLogger(__name__)

_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_TIMEOUT = 15.0
_FIELDS = "title,abstract,url,year,authors"


class SemanticScholarAdapter(BaseSourceAdapter):
    """Semantic Scholar API 适配器 — 免费无需密钥"""

    @property
    def name(self) -> str:
        return "semantic_scholar"

    @property
    def source_type(self) -> EvidenceType:
        return EvidenceType.LITERATURE

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """调用 Semantic Scholar API 搜索论文，返回 SearchResult 列表。"""
        try:
            response = httpx.get(
                _API_URL,
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": _FIELDS,
                },
                timeout=_TIMEOUT,
                headers={"User-Agent": "RetroCause/0.1 (research tool)"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Semantic Scholar 请求失败: %s", exc)
            return []

        return self._parse_json(response.json())

    @staticmethod
    def _parse_json(data: dict) -> list[SearchResult]:
        """解析 Semantic Scholar JSON 响应。"""
        results: list[SearchResult] = []
        papers = data.get("data") or []

        for paper in papers:
            title = paper.get("title", "").strip()
            url = paper.get("url", "").strip()
            abstract = paper.get("abstract") or ""
            content = abstract.strip() if abstract else ""

            if not title:
                continue

            metadata: dict = {}

            year = paper.get("year")
            if year is not None:
                metadata["year"] = str(year)

            raw_authors = paper.get("authors") or []
            author_names: list[str] = []
            for a in raw_authors:
                name = a.get("name", "").strip()
                if name:
                    author_names.append(name)
            if author_names:
                metadata["authors"] = author_names

            paper_id = paper.get("paperId")
            if paper_id:
                metadata["paper_id"] = paper_id

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
