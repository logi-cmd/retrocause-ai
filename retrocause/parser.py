"""Query parsing and lightweight domain/time-window inference."""

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
    "paleontology": ["dinosaur", "extinction", "fossil", "cretaceous", "恐龙", "灭绝", "化石"],
    "finance": [
        "financial",
        "finance",
        "bitcoin",
        "btc",
        "crypto",
        "cryptocurrency",
        "crash",
        "market",
        "price",
        "stock",
        "share",
        "equity",
        "比特币",
        "币价",
        "加密货币",
        "虚拟货币",
        "价格",
        "跳水",
        "金融",
        "股价",
        "股票",
        "市场",
        "崩盘",
        "暴跌",
        "下跌",
    ],
    "aviation": ["mh370", "aircraft", "flight", "aviation", "plane", "航班", "飞机", "失踪"],
    "history": ["empire", "collapse", "dynasty", "history", "帝国", "王朝", "历史"],
    "epidemiology": ["pandemic", "virus", "epidemic", "disease", "疫情", "病毒", "流行病"],
    "business": ["company", "startup", "product", "business", "企业", "公司", "产品"],
    "postmortem": [
        "outage",
        "incident",
        "downtime",
        "service disruption",
        "root cause",
        "postmortem",
    ],
    "geopolitics": [
        "united states",
        "u.s.",
        " us ",
        "iran",
        "china",
        "russia",
        "israel",
        "tariff",
        "sanction",
        "negotiation",
        "talks",
        "diplomacy",
        "ceasefire",
        "美国",
        "伊朗",
        "中国",
        "俄罗斯",
        "以色列",
        "关税",
        "制裁",
        "谈判",
        "会谈",
        "外交",
        "停火",
    ],
}

TODAY_KEYWORDS = [
    "today",
    "this morning",
    "this afternoon",
    "tonight",
    "intraday",
    "今天",
    "今日",
    "今早",
]
YESTERDAY_KEYWORDS = ["yesterday", "昨天", "昨日"]
LAST_24H_KEYWORDS = ["last 24", "24h", "24 hours", "最近一天", "过去24小时"]
LAST_7D_KEYWORDS = ["last week", "7d", "7 days", "最近一周", "过去7天", "本周"]
MARKET_MOVE_KEYWORDS = [
    "bitcoin",
    "btc",
    "crypto",
    "cryptocurrency",
    "price",
    "selloff",
    "drop",
    "stock",
    "stocks",
    "share price",
    "shares",
    "market",
    "equity",
    "股票",
    "股价",
    "比特币",
    "币价",
    "加密货币",
    "价格",
    "跳水",
    "下跌",
    "暴跌",
    "大跌",
    "跌",
]


def _infer_domain(query_lower: str) -> str:
    normalized = f" {query_lower} "
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return domain
    return "general"


def _infer_time_range(query_lower: str, domain: str) -> Optional[str]:
    if any(keyword in query_lower for keyword in TODAY_KEYWORDS):
        return "today"
    if any(keyword in query_lower for keyword in YESTERDAY_KEYWORDS):
        return "yesterday"
    if any(keyword in query_lower for keyword in LAST_24H_KEYWORDS):
        return "last_24h"
    if any(keyword in query_lower for keyword in LAST_7D_KEYWORDS):
        return "last_7d"
    if domain == "finance" and any(keyword in query_lower for keyword in MARKET_MOVE_KEYWORDS):
        return "trading_day"
    return None


def parse_input(raw_query: str) -> ParsedQuery:
    query_lower = raw_query.lower()
    domain = _infer_domain(query_lower)
    return ParsedQuery(
        query=raw_query,
        event_description=raw_query.strip("？? "),
        time_range=_infer_time_range(query_lower, domain),
        domain=domain,
    )
