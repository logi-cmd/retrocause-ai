from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from retrocause.api.provider_preflight import resolve_provider_model


@dataclass(frozen=True)
class LiveAnalysisSettings:
    provider_cfg: dict | None
    model_name: str
    base_url: str | None


def resolve_live_analysis_settings(
    providers: Mapping[str, dict],
    provider_key: str,
    explicit_model: str | None,
) -> LiveAnalysisSettings:
    provider_cfg, model_name = resolve_provider_model(
        providers,
        provider_key,
        explicit_model,
    )
    base_url = provider_cfg["base_url"] if provider_cfg else None
    return LiveAnalysisSettings(
        provider_cfg=provider_cfg,
        model_name=model_name,
        base_url=base_url,
    )
