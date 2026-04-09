"""6角色Agent结构化辩论"""

from __future__ import annotations

import logging

from retrocause.protocols import LLMProvider
from retrocause.models import HypothesisChain, HypothesisStatus

logger = logging.getLogger(__name__)

ROLE_LABELS = {
    "abductive": "从结果推断可能的原因",
    "deductive": "从假说推导预期的观察",
    "inductive": "从具体证据总结规律",
    "devil_advocate": "寻找攻击点",
    "arbiter": "评估论证质量",
    "meta_reviewer": "综合评估并生成改进建议",
}


class DebateOrchestrator:
    agents: dict[str, object]
    max_rounds: int
    _llm_client: LLMProvider | None

    def __init__(self, max_rounds: int = 3, llm_client: LLMProvider | None = None):
        self.max_rounds = max_rounds
        self._llm_client = llm_client
        self.agents = {
            "abductive": "Abductor",
            "deductive": "Deducer",
            "inductive": "Inducer",
            "devil_advocate": "DevilAdvocate",
            "arbiter": "Arbiter",
            "meta_reviewer": "MetaReviewer",
        }

    def run_debate(self, hypotheses: list[HypothesisChain]) -> list[HypothesisChain]:
        for h in hypotheses:
            h.status = HypothesisStatus.DEBATING
            context = f"讨论假说: {h.name}"
            for round_num in range(self.max_rounds):
                round_record = {"round": round_num + 1}
                if self._llm_client is not None and hasattr(self._llm_client, "debate_hypothesis"):
                    data = self._llm_client.debate_hypothesis(h, context)
                    if isinstance(data, dict):
                        for role in self.agents:
                            value = data.get(role, "")
                            round_record[role] = (
                                value.strip()
                                if isinstance(value, str) and value.strip()
                                else self._fallback(role, h)
                            )
                    else:
                        for role in self.agents:
                            round_record[role] = self._fallback(role, h)
                else:
                    for role, name in self.agents.items():
                        round_record[role] = f"[{name}][{ROLE_LABELS.get(role, '')}] {h.name}"
                h.debate_rounds.append(round_record)
            h.status = HypothesisStatus.REFINED
        return hypotheses

    @staticmethod
    def _fallback(role: str, hypothesis: HypothesisChain) -> str:
        return f"[{ROLE_LABELS.get(role, '')}] {hypothesis.name}"
