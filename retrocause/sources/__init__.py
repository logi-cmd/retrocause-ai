"""证据源适配器"""

from __future__ import annotations

from retrocause.sources.arxiv import ArxivSourceAdapter
from retrocause.sources.base import BaseSourceAdapter, SearchResult as SearchResult
from retrocause.sources.semantic_scholar import SemanticScholarAdapter
from retrocause.sources.web import WebSearchAdapter

ALL_SOURCES: list[BaseSourceAdapter] = [
    ArxivSourceAdapter(),
    SemanticScholarAdapter(),
    WebSearchAdapter(),
]
