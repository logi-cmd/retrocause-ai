"""管道抽象 — 可组合的分析步骤"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from retrocause.hooks import HookEngine

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    query: str = ""
    domain: str = "general"
    variables: list[Any] = field(default_factory=list)
    edges: list[Any] = field(default_factory=list)
    hypotheses: list[Any] = field(default_factory=list)
    total_evidence_count: int = 0
    total_uncertainty: float = 0.0
    extra: dict = field(default_factory=dict)
    violations: list[dict] = field(default_factory=list)
    step_errors: list[dict] = field(default_factory=list)


class PipelineStep(ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def checkpoint(self) -> bool:
        return False

    @abstractmethod
    def execute(self, ctx: PipelineContext) -> PipelineContext: ...


class Pipeline:
    def __init__(
        self,
        steps: list[PipelineStep] | None = None,
        hook_engine: HookEngine | None = None,
    ):
        self.steps: list[PipelineStep] = steps or []
        self._hook_engine = hook_engine

    def add_step(self, step: PipelineStep) -> Pipeline:
        self.steps.append(step)
        return self

    def run(self, ctx: PipelineContext | None = None) -> PipelineContext:
        ctx = ctx or PipelineContext()
        for step in self.steps:
            logger.info("Pipeline step: %s", step.name)
            try:
                ctx = step.execute(ctx)
            except Exception as exc:
                logger.error("Pipeline step %s failed: %s", step.name, exc)
                ctx.step_errors.append({"step": step.name, "error": str(exc)})

            if step.checkpoint:
                logger.info("Pipeline checkpoint after: %s", step.name)

            if self._hook_engine is not None:
                violations = self._hook_engine.evaluate({"hypotheses": ctx.hypotheses})
                for v in violations:
                    ctx.violations.append(
                        {"step": step.name, "rule": v.rule_name, "message": v.message}
                    )

        return ctx
