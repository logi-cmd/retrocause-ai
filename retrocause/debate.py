"""6角色Agent结构化辩论"""

from __future__ import annotations

from retrocause.protocols import LLMProvider
from retrocause.models import HypothesisChain, HypothesisStatus


class DebateAgent:
    def __init__(self, name: str, role: str, llm_client: LLMProvider | None = None):
        self.name = name
        self.role = role
        self._llm_client = llm_client

    def argue(self, hypothesis: HypothesisChain, context: str) -> str:
        role_labels = {
            "abductive": "从结果推断可能的原因",
            "deductive": "从假说推导预期的观察",
            "inductive": "从具体证据总结规律",
            "devil_advocate": "寻找攻击点",
            "arbiter": "评估论证质量",
            "meta_reviewer": "综合评估并生成改进建议",
        }

        if self._llm_client is not None and hasattr(self._llm_client, "debate_hypothesis"):
            data = self._llm_client.debate_hypothesis(hypothesis, context)
            value = data.get(self.role, "") if isinstance(data, dict) else ""
            if isinstance(value, str) and value.strip():
                return value.strip()

        return f"[{self.name}][{role_labels.get(self.role, '')}] {hypothesis.name}"


class DebateOrchestrator:
    agents: dict[str, DebateAgent]
    max_rounds: int

    def __init__(self, max_rounds: int = 3, llm_client: LLMProvider | None = None):
        self.max_rounds = max_rounds
        self.agents = {
            "abductive": DebateAgent("Abductor", "abductive", llm_client=llm_client),
            "deductive": DebateAgent("Deducer", "deductive", llm_client=llm_client),
            "inductive": DebateAgent("Inducer", "inductive", llm_client=llm_client),
            "devil": DebateAgent("DevilAdvocate", "devil_advocate", llm_client=llm_client),
            "arbiter": DebateAgent("Arbiter", "arbiter", llm_client=llm_client),
            "meta_reviewer": DebateAgent("MetaReviewer", "meta_reviewer", llm_client=llm_client),
        }

    def run_debate(self, hypotheses: list[HypothesisChain]) -> list[HypothesisChain]:
        for h in hypotheses:
            h.status = HypothesisStatus.DEBATING
            context = f"讨论假说: {h.name}"
            for round_num in range(self.max_rounds):
                round_record = {"round": round_num + 1}
                for agent in self.agents.values():
                    round_record[agent.role] = agent.argue(h, context)
                h.debate_rounds.append(round_record)
            h.status = HypothesisStatus.REFINED
        return hypotheses
