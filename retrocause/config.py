"""统一配置"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetroCauseConfig:
    """全局配置，不可变"""

    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    max_sub_queries: int = 6
    max_results_per_source: int = 5
    debate_max_rounds: int = 3
    debate_confidence_threshold: float = 0.8
    reliability_cross_validation_enabled: bool = True
    request_timeout_seconds: float = 120.0
    bayesian_num_samples: int = 2000
    bayesian_num_warmup: int = 1000
    counterfactual_sensitivity_threshold: float = 0.3
    counterfactual_min_score: float = 0.1

    @classmethod
    def from_env(cls) -> RetroCauseConfig:
        import os

        return cls(
            llm_api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"),
            llm_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            request_timeout_seconds=float(os.environ.get("OPENAI_TIMEOUT", "60")),
        )
