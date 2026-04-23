"""LLM客户端 — 查询分解、证据提取、相关性评分"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field

import openai

from retrocause.models import HypothesisChain

logger = logging.getLogger(__name__)

# LLM 调用可重试的异常类型
_RETRYABLE_ERRORS = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
)
_AUTH_ERRORS = (
    openai.AuthenticationError,
    openai.PermissionDeniedError,
)

_DEFAULT_MAX_RETRIES = int(os.environ.get("RETROCAUSE_LLM_MAX_RETRIES", "1"))
_DEFAULT_RETRY_BASE_DELAY = 1.0  # seconds
_DEFAULT_RETRY_MAX_DELAY = float(os.environ.get("RETROCAUSE_LLM_RETRY_MAX_DELAY", "8"))
_DEFAULT_JSON_MAX_TOKENS = 1200
_GENERIC_DECOMPOSITION_PATTERNS = (
    "specific cause",
    "specific effect",
    "general context",
    "broad domains",
    "general causal",
    "causal relationships in a general context",
    "methods for identifying causality",
    "principles of building causal graphs",
    "tools and techniques for general causal inference",
    "casual reasoning across different fields",
)


def _graph_variable_count(data: dict) -> int:
    variables = data.get("variables", [])
    return len(variables) if isinstance(variables, list) else 0


def _should_retry_graph_coverage(
    query: str,
    domain: str,
    evidence_texts: list[str],
    data: dict,
) -> bool:
    if _graph_variable_count(data) >= 6:
        return False
    if len(evidence_texts) < 2:
        return False
    scope_text = f"{query} {domain}".lower()
    return any(
        marker in scope_text
        for marker in (
            "geopolitics",
            "policy",
            "news",
            "finance",
            "business",
            "crypto",
            "cryptocurrency",
            "bitcoin",
            "btc",
            "price",
            "selloff",
            "drop",
            "market",
            "export",
            "sanction",
            "tariff",
            "semiconductor",
            "chip",
            "管制",
            "制裁",
            "关税",
            "半导体",
            "芯片",
            "比特币",
            "加密货币",
            "价格",
            "跳水",
            "下跌",
        )
    )


@dataclass
class ExtractedEvidence:
    """从原始文本中提取的结构化证据"""

    content: str
    relevance: float
    variables: list[str] = field(default_factory=list)
    confidence: float = 0.5
    stance: str = "supporting"
    stance_basis: str = "llm_extraction"


def _safe_parse_json(content: str | None) -> dict | None:
    """安全解析 LLM 返回的 JSON。

    处理以下常见问题：
    - content 为 None（部分 provider 在特殊情况下返回 null）
    - Markdown 包裹的 JSON（```json ... ```）
    - 前后有多余空白或非 JSON 文本
    """
    if content is None:
        logger.warning("_safe_parse_json: LLM 返回 content=None")
        return None

    text = content.strip()
    if not text:
        logger.warning("_safe_parse_json: LLM 返回空 content")
        return None

    # 尝试直接解析
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            logger.warning("_safe_parse_json: LLM 返回了 JSON 数组而非对象，尝试包装")
            return {"items": parsed}
        return None
    except json.JSONDecodeError:
        pass

    # 尝试提取 Markdown 代码块中的 JSON
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        try:
            parsed = json.loads(fence_match.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"items": parsed}
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            parsed = json.loads(brace_match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    bracket_match = re.search(r"\[.*\]", text, re.DOTALL)
    if bracket_match:
        try:
            parsed = json.loads(bracket_match.group(0))
            if isinstance(parsed, list):
                return {"items": parsed}
        except json.JSONDecodeError:
            pass

    logger.error("_safe_parse_json: 无法解析 LLM 响应为 JSON (前200字符): %s", text[:200])
    return None


def _retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    retry_after = None
    if hasattr(headers, "get"):
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        delay = float(retry_after)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(delay, _DEFAULT_RETRY_MAX_DELAY))


def _retry_delay_seconds(exc: Exception, attempt: int) -> float:
    exponential_delay = _DEFAULT_RETRY_BASE_DELAY * (2**attempt)
    if isinstance(exc, openai.RateLimitError):
        retry_after = _retry_after_seconds(exc)
        if retry_after is not None:
            return max(exponential_delay, retry_after)
    return min(exponential_delay, _DEFAULT_RETRY_MAX_DELAY)


def _call_with_retry(fn, *args, max_retries=_DEFAULT_MAX_RETRIES, **kwargs):
    """带指数退避的 LLM 调用包装器。

    仅对可重试的异常（限流、超时、连接错误）进行重试。
    其他异常（如 AuthenticationError）立即抛出。
    """
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except _RETRYABLE_ERRORS as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = _retry_delay_seconds(exc, attempt)
                logger.warning(
                    "LLM 调用失败 (attempt %d/%d): %s — %.1fs 后重试",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error("LLM 调用最终失败 (共 %d 次尝试): %s", max_retries + 1, exc)
    raise last_exc  # type: ignore[misc]


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _normalize_queries(queries: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in queries:
        candidate = re.sub(r"\s+", " ", str(item).strip())
        if not candidate:
            continue
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(candidate)
    return normalized


def _english_token_count(text: str) -> int:
    return len(re.findall(r"[a-zA-Z]{3,}", text))


def _prefer_searchable_queries(queries: list[str]) -> list[str]:
    return sorted(
        _normalize_queries(queries),
        key=lambda item: (_english_token_count(item), len(item)),
        reverse=True,
    )


def _has_query_anchor(candidate: str, original_query: str) -> bool:
    candidate_lower = candidate.lower()
    original_lower = original_query.lower()
    ascii_tokens = re.findall(r"[a-zA-Z]{3,}", original_lower)
    if any(token in candidate_lower for token in ascii_tokens):
        return True
    if _contains_cjk(original_query) and _contains_cjk(candidate):
        return True
    if _contains_cjk(original_query):
        return len(re.findall(r"[a-zA-Z]{3,}", candidate_lower)) >= 3
    return False


def _has_unanchored_year(candidate: str, original_query: str) -> bool:
    candidate_years = set(re.findall(r"\b(?:19|20)\d{2}\b", candidate))
    if not candidate_years:
        return False
    original_years = set(re.findall(r"\b(?:19|20)\d{2}\b", original_query))
    return not candidate_years.issubset(original_years)


def _queries_look_invalid(original_query: str, queries: list[str]) -> bool:
    cleaned = _normalize_queries(queries)
    if not cleaned:
        return True
    if len(cleaned) < 2:
        return True
    if all(not _has_query_anchor(item, original_query) for item in cleaned):
        return True
    if _contains_cjk(original_query) and all(
        not _has_required_cjk_anchor(item, original_query) for item in cleaned
    ):
        return True
    if any(_has_unanchored_year(item, original_query) for item in cleaned):
        return True

    lowered = " || ".join(item.lower() for item in cleaned)
    if any(pattern in lowered for pattern in _GENERIC_DECOMPOSITION_PATTERNS):
        return True
    return False


_CJK_SEARCH_TRANSLATIONS = {
    "美国": "United States",
    "比特币": "Bitcoin BTC",
    "加密货币": "cryptocurrency crypto",
    "虚拟货币": "cryptocurrency crypto",
    "今日": "today",
    "今天": "today",
    "昨天": "yesterday",
    "昨日": "yesterday",
    "价格": "price",
    "币价": "price",
    "跳水": "price drop selloff",
    "下跌": "price drop",
    "暴跌": "crash selloff",
    "伊朗": "Iran",
    "中国": "China",
    "俄罗斯": "Russia",
    "乌克兰": "Ukraine",
    "以色列": "Israel",
    "谈判": "talks negotiations",
    "会谈": "talks negotiations",
    "首轮": "first round",
    "同意": "agree agrees agreed",
    "为什么": "why reasons",
    "原因": "reasons",
    "半导体": "semiconductor chips",
    "芯片": "semiconductor chips",
    "出口管制": "export controls",
    "出口限制": "export restrictions",
    "管制": "controls restrictions",
    "限制": "restrictions limits",
    "制裁": "sanctions",
    "关税": "tariffs",
    "政策": "policy",
    "新规": "new rules",
}


_CJK_GENERIC_QUERY_TERMS = {"为什么", "原因", "美国"}
_CJK_SEARCH_NOISE_TERMS = {"为什么", "原因"}


_CJK_SEARCH_TRANSLATIONS.update(
    {
        "今日": "today",
        "今天": "today",
        "午后": "afternoon",
        "股价": "share price stock price",
        "股票": "stock shares",
        "直线跳水": "plunge selloff",
        "跳水": "price drop selloff",
        "为什么": "why reasons",
    }
)

_CJK_FINANCE_ENTITY_SUFFIXES = (
    "股份",
    "集团",
    "科技",
    "银行",
    "证券",
    "控股",
    "公司",
    "电子",
    "电气",
    "能源",
    "药业",
    "汽车",
)
_CJK_FINANCE_ENTITY_BOUNDARIES = (
    "今日",
    "今天",
    "午后",
    "早盘",
    "尾盘",
    "股价",
    "股票",
    "为什么",
    "为何",
    "直线跳水",
    "跳水",
    "下跌",
    "暴跌",
)


def _significant_english_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z]{3,}", text.lower())
        if token not in {"why", "the", "and", "for", "new", "did", "does", "policy", "reasons"}
    }


def _required_cjk_anchor_tokens(original_query: str) -> set[str]:
    """Return translated event tokens that make English rewrites query-specific."""
    tokens: set[str] = set()
    for source, replacement in _CJK_SEARCH_TRANSLATIONS.items():
        if source not in original_query or source in _CJK_GENERIC_QUERY_TERMS:
            continue
        tokens.update(_significant_english_tokens(replacement))
    return tokens


def _extract_cjk_finance_entity(query: str) -> str:
    """Best-effort Chinese market entity anchor, e.g. `芯原股份`."""

    for suffix in _CJK_FINANCE_ENTITY_SUFFIXES:
        match = re.search(rf"([\u4e00-\u9fffA-Za-z0-9]{{2,20}}{re.escape(suffix)})", query)
        if match:
            return match.group(1)

    boundary_positions = [query.find(marker) for marker in _CJK_FINANCE_ENTITY_BOUNDARIES]
    boundary_positions = [pos for pos in boundary_positions if pos > 0]
    if not boundary_positions:
        return ""

    prefix = query[: min(boundary_positions)]
    prefix = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", prefix)
    if 2 <= len(prefix) <= 16:
        return prefix
    return ""


def _has_required_cjk_anchor(candidate: str, original_query: str) -> bool:
    entity_anchor = _extract_cjk_finance_entity(original_query)
    if entity_anchor and entity_anchor not in candidate and not _contains_cjk(candidate):
        return False

    required_tokens = _required_cjk_anchor_tokens(original_query)
    if not required_tokens:
        return True
    candidate_tokens = _significant_english_tokens(candidate)
    if candidate_tokens & required_tokens:
        return True
    return _contains_cjk(candidate)


def _heuristic_search_queries(query: str, domain: str) -> list[str]:
    if not _contains_cjk(query):
        return [query]

    matched_sources: list[str] = []
    for source in sorted(_CJK_SEARCH_TRANSLATIONS, key=len, reverse=True):
        if source in _CJK_SEARCH_NOISE_TERMS or source not in query:
            continue
        if any(source in existing for existing in matched_sources):
            continue
        matched_sources.append(source)
    translated_terms = [_CJK_SEARCH_TRANSLATIONS[source] for source in matched_sources]
    entity_anchor = _extract_cjk_finance_entity(query) if domain in {"finance", "business"} else ""
    if entity_anchor:
        translated_terms = [entity_anchor, *translated_terms]
    if len(translated_terms) < 2:
        return [query]

    translated = " ".join(translated_terms)
    queries = [
        translated,
        f"{translated} official statements",
    ]
    if domain in {"finance", "business"}:
        queries.append(f"{translated} market analysis")
        queries.append(f"{translated} liquidation ETF macro risk")
    elif domain == "geopolitics":
        translated_lower = translated.lower()
        if any(
            token in translated_lower
            for token in ["export controls", "export restrictions", "semiconductor", "sanctions"]
        ):
            queries.append(f"{translated} Commerce Department official statement")
            queries.append(f"{translated} policy rationale")
        else:
            queries.append(f"{translated} diplomacy foreign policy")
    queries.append(query)
    return _prefer_searchable_queries(queries)


class LLMClient:
    """封装 OpenAI API，为 RetroCause 提供证据收集能力。"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        """
        初始化 LLM 客户端。

        Args:
            api_key: API 密钥，为 None 时依次尝试 OPENROUTER_API_KEY / OPENAI_API_KEY 环境变量。
            model: 模型名称（OpenRouter 格式如 "deepseek/deepseek-chat-v3-0324"）。
            base_url: API 地址，默认 https://openrouter.ai/api/v1 或 https://api.openai.com/v1。
            timeout: 请求超时秒数，为 None 时回退到 OPENAI_TIMEOUT 环境变量（默认 60s）。
        """
        resolved_key = (
            api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
        )
        if base_url:
            resolved_base = base_url
        elif os.environ.get("OPENROUTER_API_KEY"):
            resolved_base = "https://openrouter.ai/api/v1"
        else:
            resolved_base = None

        resolved_timeout = timeout or float(os.environ.get("OPENAI_TIMEOUT", "60"))

        self.client = openai.OpenAI(
            api_key=resolved_key,
            base_url=resolved_base,
            timeout=resolved_timeout,
        )
        self.model = model

    def _json_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = _DEFAULT_JSON_MAX_TOKENS,
    ) -> dict | None:
        kwargs: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
        }
        kwargs["response_format"] = {"type": "json_object"}
        try:
            response = _call_with_retry(self.client.chat.completions.create, **kwargs)
        except openai.BadRequestError:
            kwargs.pop("response_format", None)
            logger.warning("Provider does not support response_format, retrying without it")
            response = _call_with_retry(self.client.chat.completions.create, **kwargs)
        raw_content = response.choices[0].message.content
        return _safe_parse_json(raw_content)

    def preflight_model_access(self) -> tuple[bool, str | None]:
        system_prompt = "Return a tiny JSON object with {'status':'ok'}."
        user_prompt = "Health check."
        try:
            data = self._json_chat_completion(system_prompt, user_prompt, max_tokens=80)
            if data and data.get("status") == "ok":
                return True, None
            return False, "Model preflight returned an unexpected payload."
        except _AUTH_ERRORS as exc:
            return False, f"{type(exc).__name__}: {exc}"
        except openai.OpenAIError as exc:
            return False, f"{type(exc).__name__}: {exc}"

    def preflight_analysis_smoke(self) -> tuple[bool, str | None]:
        smoke_query = "\u4e3a\u4ec0\u4e48\u7f8e\u56fd\u4f1a\u540c\u610f\u4e0e\u4f0a\u6717\u8fdb\u884c\u9996\u8f6e\u8c08\u5224\uff1f"
        try:
            queries = self.build_search_queries(smoke_query, "geopolitics")
            if _queries_look_invalid(smoke_query, queries):
                return False, "Analysis-stage smoke returned empty search queries."
            return True, None
        except _AUTH_ERRORS as exc:
            return False, f"{type(exc).__name__}: {exc}"
        except openai.OpenAIError as exc:
            return False, f"{type(exc).__name__}: {exc}"

    def _rewrite_search_queries(self, query: str, domain: str) -> list[str]:
        system_prompt = (
            "You rewrite why-questions into concrete retrieval queries. "
            "Return 2 to 4 search queries as a JSON object with key 'queries'. "
            "Rules: keep named entities, countries, companies, and dates; prefer English for search; "
            "focus on the actual event or decision; never output placeholders, methodology queries, or meta-causal prompts."
            " Never invent a year, date, company, country, or event detail that is not present in the original query."
        )
        user_prompt = (
            f"Original query: {query}\n"
            f"Domain: {domain}\n\n"
            "Produce concrete web/news retrieval queries for this exact question."
        )
        data = self._json_chat_completion(system_prompt, user_prompt, max_tokens=420)
        if data is None:
            return []
        queries = data.get("queries", [])
        if not isinstance(queries, list):
            return []
        return _normalize_queries([str(q) for q in queries if isinstance(q, str)])

    def build_search_queries(self, query: str, domain: str) -> list[str]:
        queries = self.decompose_query(query, domain)
        if not _queries_look_invalid(query, queries):
            normalized = _prefer_searchable_queries(queries)
            if not (_contains_cjk(query) and domain in {"geopolitics", "finance", "business"}):
                return normalized

        logger.warning(
            "build_search_queries: decomposition output invalid for query=%r domain=%s; using rewrite fallback",
            query,
            domain,
        )
        rewritten = self._rewrite_search_queries(query, domain)
        if not _queries_look_invalid(query, rewritten):
            return _prefer_searchable_queries(rewritten)

        heuristic = _heuristic_search_queries(query, domain)
        if not _queries_look_invalid(query, heuristic):
            return heuristic

        logger.warning("build_search_queries: rewrite fallback also invalid, using original query")
        return [query]

    # ------------------------------------------------------------------
    # 查询分解
    # ------------------------------------------------------------------

    def decompose_query(self, query: str, domain: str) -> list[str]:
        """
        将因果查询分解为 3-6 个可搜索的子查询。

        示例: "恐龙为什么灭绝？" → [
            "dinosaur extinction asteroid impact evidence",
            "dinosaur extinction volcanic activity Deccan Traps",
            "dinosaur extinction climate change Cretaceous-Paleogene",
            "K-Pg boundary iridium anomaly evidence",
        ]

        Args:
            query: 用户的因果查询问题。
            domain: 查询所属领域（如 biology、geology、economics）。

        Returns:
            搜索子查询字符串列表。
        """
        system_prompt = (
            "You are a retrieval planner for a causal reasoning engine. "
            "Given a why-question and domain, generate 2 to 4 concrete search sub-queries "
            "for finding evidence about the actual event. "
            "Rules: preserve named entities, countries, companies, and dates; prefer English for broader search; "
            "target plausible mechanisms or official explanations; never output placeholders, methodology questions, or generic causal-inference prompts. "
            "Never invent a year, date, country, company, or event detail that is not present in the original query. "
            "Return a JSON object with a single key 'queries' containing a list of strings."
        )
        user_prompt = (
            f"Query: {query}\n"
            f"Domain: {domain}\n\n"
            "Generate search sub-queries for finding event-specific causal evidence."
        )

        try:
            data = self._json_chat_completion(system_prompt, user_prompt, max_tokens=420)
            if data is None:
                logger.error("decompose_query: LLM response was not valid JSON")
                return []
            queries = data.get("queries", [])
            if not isinstance(queries, list):
                return []
            return _normalize_queries([str(q) for q in queries if isinstance(q, str)])
        except _AUTH_ERRORS as exc:
            logger.error("decompose_query: authentication/permission error — %s", exc)
            raise
        except openai.OpenAIError as exc:
            logger.error("decompose_query: OpenAI error — %s", exc)
            return []

    # ------------------------------------------------------------------
    # 证据提取
    # ------------------------------------------------------------------

    def extract_evidence(
        self, query: str, raw_text: str, source_type: str
    ) -> list[ExtractedEvidence]:
        """
        从原始搜索结果文本中提取结构化证据。

        仅提取有证据支撑的事实性陈述，不包含推测内容。

        Args:
            query: 原始因果查询。
            raw_text: 搜索返回的原始文本。
            source_type: 来源类型（如 literature、news、data）。

        Returns:
            ExtractedEvidence 列表。
        """
        system_prompt = (
            "You are an evidence extraction assistant for a causal reasoning engine. "
            "Given a causal query and raw text from a search result, extract ONLY factual "
            "claims that are directly supported by evidence in the text. Do NOT extract "
            "speculation, opinions, or unverified claims. "
            "For each extracted claim, provide: "
            "1) 'content': the factual claim as a concise statement, "
            "2) 'relevance': float 0-1 indicating how relevant this claim is to the query, "
            "3) 'variables': list of causal variables mentioned (e.g. 'temperature', 'CO2 levels'), "
            "4) 'confidence': float 0-1 indicating your confidence in the extraction accuracy, "
            "5) 'stance': one of 'supporting', 'refuting', or 'context'. Use 'refuting' only "
            "when the claim explicitly weakens, disputes, or contradicts a proposed causal "
            "explanation for the query; use 'context' for background facts that do not support "
            "or weaken a cause. "
            "Return a JSON object with key 'evidence' containing a list of objects, each with "
            "keys: content, relevance, variables, confidence, stance."
        )
        user_prompt = (
            f"Query: {query}\n"
            f"Source type: {source_type}\n"
            f"Raw text:\n{raw_text}\n\n"
            "Extract factual evidence relevant to the causal query."
        )

        try:
            kwargs: dict = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 1200,
            }
            kwargs["response_format"] = {"type": "json_object"}
            try:
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            except openai.BadRequestError:
                kwargs.pop("response_format", None)
                logger.warning("Provider does not support response_format, retrying without it")
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            raw_content = response.choices[0].message.content
            data = _safe_parse_json(raw_content)
            if data is None:
                logger.error("extract_evidence: LLM 响应无法解析为 JSON")
                return []
            items = data.get("evidence", [])
            if not isinstance(items, list):
                return []

            results: list[ExtractedEvidence] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", "")
                if not isinstance(content, str) or not content.strip():
                    continue
                relevance = float(item.get("relevance", 0.5))
                confidence = float(item.get("confidence", 0.5))
                variables = item.get("variables", [])
                if not isinstance(variables, list):
                    variables = []
                variables = [str(v) for v in variables if isinstance(v, str)]
                stance = str(item.get("stance", "supporting")).strip().lower()
                if stance not in {"supporting", "refuting", "context"}:
                    stance = "supporting"
                results.append(
                    ExtractedEvidence(
                        content=content.strip(),
                        relevance=max(0.0, min(1.0, relevance)),
                        variables=variables,
                        confidence=max(0.0, min(1.0, confidence)),
                        stance=stance,
                    )
                )
            return results
        except _AUTH_ERRORS as exc:
            logger.error("extract_evidence: authentication/permission error — %s", exc)
            raise
        except openai.OpenAIError as exc:
            logger.error("extract_evidence: OpenAI 错误 — %s", exc)
            return []

    # ------------------------------------------------------------------
    # 相关性评分
    # ------------------------------------------------------------------

    def score_relevance(self, query: str, evidence_content: str) -> float:
        """
        评估证据内容与因果查询的相关性。

        Args:
            query: 因果查询问题。
            evidence_content: 待评分的证据文本。

        Returns:
            0 到 1 之间的相关性分数。
        """
        system_prompt = (
            "You are a relevance scoring assistant for a causal reasoning engine. "
            "Given a causal query and a piece of evidence, score how relevant the "
            "evidence is to answering the causal question. Consider both direct "
            "relevance (does it address the specific causal relationship?) and "
            "indirect relevance (does it provide useful background or related "
            "causal factors?). "
            "Return a JSON object with a single key 'score' containing a float "
            "between 0 (completely irrelevant) and 1 (highly relevant)."
        )
        user_prompt = (
            f"Query: {query}\n"
            f"Evidence: {evidence_content}\n\n"
            "Score the relevance of this evidence to the query."
        )

        try:
            kwargs: dict = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 1000,
            }
            kwargs["response_format"] = {"type": "json_object"}
            try:
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            except openai.BadRequestError:
                kwargs.pop("response_format", None)
                logger.warning("Provider does not support response_format, retrying without it")
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            raw_content = response.choices[0].message.content
            data = _safe_parse_json(raw_content)
            if data is None:
                logger.warning("score_relevance: LLM 响应无法解析为 JSON, 返回默认分数")
                return 0.5
            score = float(data.get("score", 0.5))
            return max(0.0, min(1.0, score))
        except _AUTH_ERRORS as exc:
            logger.error("score_relevance: authentication/permission error — %s", exc)
            raise
        except openai.OpenAIError as exc:
            logger.error("score_relevance: OpenAI 错误 — %s", exc)
            return 0.5

    # ------------------------------------------------------------------
    # 因果图构建
    # ------------------------------------------------------------------

    def build_causal_graph(self, query: str, evidence_texts: list[str], domain: str) -> dict:
        """
        基于证据文本构建因果有向无环图（DAG）。

        Args:
            query: 用户的因果查询问题。
            evidence_texts: 证据文本列表。
            domain: 查询所属领域。

        Returns:
            包含 variables、edges、result_variable 的字典。
        """
        system_prompt = (
            "You are a causal analysis assistant. "
            "Given evidence about why something happened, extract the causal DAG. "
            "Variables should be short snake_case identifiers (e.g. 'asteroid_impact', "
            "'volcanic_activity', 'climate_change', 'dinosaur_extinction'). "
            "Each variable needs a name and a short description. "
            "For live/news/policy questions, prefer a coverage-rich graph with 7 to 12 "
            "evidence-supported variables when the evidence allows it. Include upstream "
            "drivers, policy motives, implementation mechanisms, intermediate channels, "
            "and the final outcome instead of collapsing several causes into one node. "
            "Do not add unsupported filler variables. "
            "Edges represent direct causal relationships with estimated conditional "
            "probabilities (0.0-1.0) indicating how strongly the cause determines the effect. "
            "The graph MUST be a DAG (no cycles). Prefer 8 to 16 direct edges when evidence "
            "supports them, but every edge must be grounded in the provided evidence. "
            "Return a JSON object with keys: "
            "'variables': list of {name: str, description: str}, "
            "'edges': list of {source: str, target: str, conditional_prob: float, description: str}, "
            "'result_variable': the name of the main result variable being explained."
        )
        evidence_block = "\n---\n".join(evidence_texts)
        user_prompt = (
            f"Query: {query}\n"
            f"Domain: {domain}\n"
            f"Evidence:\n{evidence_block}\n\n"
            "Extract the causal graph from the evidence above."
        )

        try:
            kwargs: dict = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            kwargs["response_format"] = {"type": "json_object"}
            try:
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            except openai.BadRequestError:
                kwargs.pop("response_format", None)
                logger.warning("Provider does not support response_format, retrying without it")
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            raw_content = response.choices[0].message.content
            data = _safe_parse_json(raw_content)
            if data is None:
                logger.error("build_causal_graph: LLM 响应无法解析为 JSON")
                return {}
            if not isinstance(data, dict):
                logger.error("build_causal_graph: LLM 响应不是 JSON 对象")
                return {}
            if _should_retry_graph_coverage(query, domain, evidence_texts, data):
                retry_prompt = (
                    f"{user_prompt}\n\n"
                    "The previous graph was too narrow for an evidence-board product. "
                    "Rebuild the graph with at least 6 distinct evidence-supported variables "
                    "if the evidence contains that many causal factors. Split collapsed concepts "
                    "into separate nodes only when each node is directly supported by the evidence. "
                    "Keep the graph acyclic and do not invent unsupported variables."
                )
                retry_kwargs = dict(kwargs)
                retry_kwargs["messages"] = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": retry_prompt},
                ]
                try:
                    retry_response = _call_with_retry(
                        self.client.chat.completions.create,
                        **retry_kwargs,
                    )
                except openai.BadRequestError:
                    retry_kwargs.pop("response_format", None)
                    retry_response = _call_with_retry(
                        self.client.chat.completions.create,
                        **retry_kwargs,
                    )
                retry_data = _safe_parse_json(retry_response.choices[0].message.content)
                if isinstance(retry_data, dict) and _graph_variable_count(
                    retry_data
                ) > _graph_variable_count(data):
                    logger.info(
                        "build_causal_graph: coverage retry expanded graph from %d to %d variables",
                        _graph_variable_count(data),
                        _graph_variable_count(retry_data),
                    )
                    data = retry_data
            return data
        except _AUTH_ERRORS as exc:
            logger.error("build_causal_graph: authentication/permission error — %s", exc)
            raise
        except (openai.OpenAIError, json.JSONDecodeError) as exc:
            logger.error("build_causal_graph: 错误 — %s", exc)
            return {}

    def debate_hypothesis(self, hypothesis: HypothesisChain, context: str) -> dict:
        system_prompt = (
            "You are a structured causal debate engine. "
            "Given a hypothesis chain and context, generate one debate round with five roles: "
            "abductive, deductive, inductive, devil_advocate, arbitrator. "
            "Each field must be a concise evidence-aware statement, not fluff. "
            "Return a JSON object with exactly these five keys."
        )

        variable_names = [variable.name for variable in hypothesis.variables]
        edge_names = [f"{edge.source}->{edge.target}" for edge in hypothesis.edges]
        user_prompt = (
            f"Context: {context}\n"
            f"Hypothesis: {hypothesis.name}\n"
            f"Description: {hypothesis.description}\n"
            f"Variables: {', '.join(variable_names)}\n"
            f"Edges: {', '.join(edge_names)}\n"
            f"Path probability: {hypothesis.path_probability:.2f}\n"
            f"Evidence coverage: {hypothesis.evidence_coverage:.2f}\n"
            f"Unanchored edges: {', '.join(hypothesis.unanchored_edges) if hypothesis.unanchored_edges else 'none'}"
        )

        try:
            kwargs: dict = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            kwargs["response_format"] = {"type": "json_object"}
            try:
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            except openai.BadRequestError:
                kwargs.pop("response_format", None)
                logger.warning("Provider does not support response_format, retrying without it")
                response = _call_with_retry(
                    self.client.chat.completions.create,
                    **kwargs,
                )
            raw_content = response.choices[0].message.content
            data = _safe_parse_json(raw_content)
            if data is None:
                logger.error("debate_hypothesis: LLM 响应无法解析为 JSON")
                return {}
            if not isinstance(data, dict):
                logger.error("debate_hypothesis: LLM 响应不是 JSON 对象")
                return {}
            return data
        except _AUTH_ERRORS as exc:
            logger.error("debate_hypothesis: authentication/permission error — %s", exc)
            raise
        except (openai.OpenAIError, json.JSONDecodeError) as exc:
            logger.error("debate_hypothesis: 错误 — %s", exc)
            return {}
