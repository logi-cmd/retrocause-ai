"""因果推理质量守卫 — 声明式规则引擎"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HookAction(str, Enum):
    WARN = "warn"
    BLOCK = "block"


@dataclass(frozen=True)
class HookViolation:
    rule_name: str
    action: HookAction
    message: str


class HookRule(ABC):
    """规则基类"""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def action(self) -> HookAction: ...

    @abstractmethod
    def check(self, context: dict) -> HookViolation | None:
        """返回 HookViolation 表示违反，None 表示通过。"""
        ...


class HookEngine:
    """规则引擎 — 收集所有规则并执行检查"""

    def __init__(self, rules: list[HookRule] | None = None):
        self.rules: list[HookRule] = rules or []

    def add_rule(self, rule: HookRule) -> None:
        self.rules.append(rule)

    def evaluate(self, context: dict) -> list[HookViolation]:
        violations: list[HookViolation] = []
        for rule in self.rules:
            try:
                result = rule.check(context)
                if result is not None:
                    violations.append(result)
                    if result.action == HookAction.BLOCK:
                        logger.warning("BLOCK by rule '%s': %s", rule.name, result.message)
                    else:
                        logger.info("WARN from rule '%s': %s", rule.name, result.message)
            except Exception:
                logger.warning("Rule '%s' evaluation failed", rule.name)
        return violations
