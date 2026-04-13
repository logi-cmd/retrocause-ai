"""内置 Hook 规则 — 证据覆盖和概率边界守卫"""

from __future__ import annotations

from retrocause.hooks import HookAction, HookRule, HookViolation


class EvidenceCoverageRule(HookRule):
    def __init__(self, threshold: float = 0.5):
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "evidence_coverage_threshold"

    @property
    def action(self) -> HookAction:
        return HookAction.WARN

    def check(self, context: dict) -> HookViolation | None:
        hypotheses = context.get("hypotheses", [])
        if not hypotheses:
            return None

        low_coverage = [h for h in hypotheses if h.evidence_coverage < self._threshold]
        if not low_coverage:
            return None

        return HookViolation(
            rule_name=self.name,
            action=self.action,
            message=(
                f"证据覆盖不足: {len(low_coverage)} 条假说链 覆盖低于阈值 {self._threshold:.0%}"
            ),
        )


class ProbabilityBoundRule(HookRule):
    @property
    def name(self) -> str:
        return "probability_bound"

    @property
    def action(self) -> HookAction:
        return HookAction.WARN

    def check(self, context: dict) -> HookViolation | None:
        hypotheses = context.get("hypotheses", [])
        if not hypotheses:
            return None

        violations: list[str] = []
        for h in hypotheses:
            if not (0.0 <= h.path_probability <= 1.0):
                violations.append(f"{h.id} path_probability={h.path_probability}")
            if not (0.0 <= h.posterior_probability <= 1.0):
                violations.append(f"{h.id} posterior={h.posterior_probability}")
            lo, hi = h.confidence_interval
            if not (0.0 <= lo <= 1.0):
                violations.append(f"{h.id} CI lower={lo:.4f}")
            if not (0.0 <= hi <= 1.0):
                violations.append(f"{h.id} CI upper={hi:.4f}")

        if not violations:
            return None

        return HookViolation(
            rule_name=self.name,
            action=self.action,
            message="概率边界违反: " + "; ".join(violations),
        )


class CounterfactualBoundRule(HookRule):
    """反事实得分阈值守卫"""

    def __init__(self, min_score: float = 0.1):
        self._min_score = min_score

    @property
    def name(self) -> str:
        return "counterfactual_bound"

    @property
    def action(self) -> HookAction:
        return HookAction.WARN

    def check(self, context: dict) -> HookViolation | None:
        hypotheses = context.get("hypotheses", [])
        if not hypotheses:
            return None

        low_score = [h for h in hypotheses if h.counterfactual_score < self._min_score]
        if not low_score:
            return None

        return HookViolation(
            rule_name=self.name,
            action=self.action,
            message=(f"反事实得分不足: {len(low_score)} 条假说链得分低于 {self._min_score:.2f}"),
        )
