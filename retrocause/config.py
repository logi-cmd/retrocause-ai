"""统一配置"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetroCauseConfig:
    """全局配置，不可变"""

    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    max_sub_queries: int = 4
    max_results_per_source: int = 3
    debate_max_rounds: int = 1
    debate_confidence_threshold: float = 0.8
    reliability_cross_validation_enabled: bool = True
    request_timeout_seconds: float = 120.0
    hot_query_cache_seconds: float = 90.0
    evergreen_query_cache_seconds: float = 600.0
    source_min_interval_seconds: float = 0.2
    bayesian_num_samples: int = 2000
    bayesian_num_warmup: int = 1000
    counterfactual_sensitivity_threshold: float = 0.3
    counterfactual_min_score: float = 0.0

    @classmethod
    def from_env(cls) -> RetroCauseConfig:
        import os

        return cls(
            llm_api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"),
            llm_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            max_sub_queries=int(os.environ.get("RETROCAUSE_MAX_SUB_QUERIES", "4")),
            max_results_per_source=int(os.environ.get("RETROCAUSE_MAX_RESULTS_PER_SOURCE", "3")),
            debate_max_rounds=int(os.environ.get("RETROCAUSE_DEBATE_MAX_ROUNDS", "0")),
            request_timeout_seconds=float(os.environ.get("OPENAI_TIMEOUT", "60")),
            hot_query_cache_seconds=float(os.environ.get("RETROCAUSE_HOT_QUERY_CACHE_SECONDS", "90")),
            evergreen_query_cache_seconds=float(
                os.environ.get("RETROCAUSE_EVERGREEN_QUERY_CACHE_SECONDS", "600")
            ),
            source_min_interval_seconds=float(
                os.environ.get("RETROCAUSE_SOURCE_MIN_INTERVAL_SECONDS", "0.2")
            ),
            counterfactual_min_score=float(
                os.environ.get("RETROCAUSE_COUNTERFACTUAL_MIN_SCORE", "0.0")
            ),
        )
