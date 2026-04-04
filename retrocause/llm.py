"""LLM客户端 — 查询分解、证据提取、相关性评分"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import openai

from retrocause.models import HypothesisChain


@dataclass
class ExtractedEvidence:
    """从原始文本中提取的结构化证据"""

    content: str
    relevance: float
    variables: list[str] = field(default_factory=list)
    confidence: float = 0.5


class LLMClient:
    """封装 OpenAI API，为 RetroCause 提供证据收集能力。"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
    ):
        """
        初始化 LLM 客户端。

        Args:
            api_key: API 密钥，为 None 时依次尝试 OPENROUTER_API_KEY / OPENAI_API_KEY 环境变量。
            model: 模型名称（OpenRouter 格式如 "deepseek/deepseek-chat-v3-0324"）。
            base_url: API 地址，默认 https://openrouter.ai/api/v1 或 https://api.openai.com/v1。
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

        self.client = openai.OpenAI(
            api_key=resolved_key,
            base_url=resolved_base,
            timeout=float(os.environ.get("OPENAI_TIMEOUT", "60")),
        )
        self.model = model

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
            "You are a research assistant specializing in causal analysis. "
            "Given a causal query and its domain, generate 3 to 6 search sub-queries "
            "that would find diverse, high-quality evidence for building a causal graph. "
            "Each sub-query should target a different aspect or hypothesis of the causal "
            "question. Use domain-specific terminology. Prefer English queries for broader "
            "search coverage, but keep the original language if the query is not in English. "
            "Return a JSON object with a single key 'queries' containing a list of strings."
        )
        user_prompt = (
            f"Query: {query}\n"
            f"Domain: {domain}\n\n"
            "Generate search sub-queries for finding causal evidence."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            queries = data.get("queries", [])
            if not isinstance(queries, list):
                return []
            return [str(q) for q in queries if isinstance(q, str)]
        except openai.OpenAIError:
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
            "4) 'confidence': float 0-1 indicating your confidence in the extraction accuracy. "
            "Return a JSON object with key 'evidence' containing a list of objects, each with "
            "keys: content, relevance, variables, confidence."
        )
        user_prompt = (
            f"Query: {query}\n"
            f"Source type: {source_type}\n"
            f"Raw text:\n{raw_text}\n\n"
            "Extract factual evidence relevant to the causal query."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
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
                results.append(
                    ExtractedEvidence(
                        content=content.strip(),
                        relevance=max(0.0, min(1.0, relevance)),
                        variables=variables,
                        confidence=max(0.0, min(1.0, confidence)),
                    )
                )
            return results
        except openai.OpenAIError:
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            score = float(data.get("score", 0.5))
            return max(0.0, min(1.0, score))
        except openai.OpenAIError:
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
            "Edges represent direct causal relationships with estimated conditional "
            "probabilities (0.0-1.0) indicating how strongly the cause determines the effect. "
            "The graph MUST be a DAG (no cycles). "
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            if not isinstance(data, dict):
                return {}
            return data
        except (openai.OpenAIError, json.JSONDecodeError):
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            if not isinstance(data, dict):
                return {}
            return data
        except (openai.OpenAIError, json.JSONDecodeError):
            return {}
