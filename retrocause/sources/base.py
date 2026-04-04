"""证据源适配器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from retrocause.models import EvidenceType


@dataclass
class SearchResult:
    """单条搜索结果"""

    title: str
    content: str  # abstract / summary
    url: str
    source_type: EvidenceType
    metadata: dict = field(default_factory=dict)  # year, authors, etc.


class BaseSourceAdapter(ABC):
    """证据源适配器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """适配器名称"""

    @property
    @abstractmethod
    def source_type(self) -> EvidenceType:
        """返回的证据类型"""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """
        搜索证据源，返回原始搜索结果。

        Args:
            query: 搜索查询字符串
            max_results: 最大返回结果数

        Returns:
            SearchResult 列表
        """
