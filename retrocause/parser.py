"""语义解析 + 领域识别"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedQuery:
    query: str
    event_description: str
    time_range: Optional[str] = None
    location: Optional[str] = None
    domain: str = "general"


DOMAIN_KEYWORDS = {
    "paleontology": ["灭绝", "恐龙", "化石", "地质", "dinosaur", "extinction"],
    "finance": ["金融", "危机", "崩盘", "通胀", "经济", "financial", "crash"],
    "aviation": ["坠毁", "失踪", "航班", "飞机", "mh370", "aircraft"],
    "history": ["帝国", "衰亡", "王朝", "历史", "empire", "collapse"],
    "epidemiology": ["疫情", "病毒", "流行病", "感染", "pandemic"],
    "business": ["产品", "公司", "企业", "市场", "startup", "product"],
}


def parse_input(raw_query: str) -> ParsedQuery:
    query_lower = raw_query.lower()
    domain = "general"
    for dom, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            domain = dom
            break
    return ParsedQuery(
        query=raw_query,
        event_description=raw_query.strip("？? "),
        domain=domain,
    )
