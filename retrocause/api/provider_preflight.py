from __future__ import annotations

from collections.abc import Mapping


LIVE_FAILURE_TOKENS = [
    "401",
    "authentication",
    "permission",
    "user not found",
    "connection error",
    "apiconnectionerror",
    "timed out",
    "empty result",
    "rate limit",
]

PREFLIGHT_ACTIONS = {
    "missing_api_key": "Enter an API key before running live analysis.",
    "unknown_provider": "Choose a configured provider or add provider settings first.",
    "invalid_model": "Pick a model listed by the provider, then run preflight again.",
    "auth_or_permission": "Check that the API key is valid and has access to this provider/model.",
    "billing_or_quota": "Check provider balance, quota, or account limits before retrying.",
    "timeout": "Try a faster model or retry when the provider is responsive.",
    "invalid_or_empty_payload": (
        "Try a model with reliable JSON output before running the full analysis."
    ),
}

MODEL_ALIASES = {
    "openrouter": {
        "deepseek/deepseek-chat-v3-0324": "deepseek/deepseek-chat",
    },
}


def is_live_failure(error_msg: str | None) -> bool:
    if not error_msg:
        return False
    lowered = error_msg.lower()
    return any(token in lowered for token in LIVE_FAILURE_TOKENS)


def resolve_provider_model(
    providers: Mapping[str, dict],
    provider_key: str,
    explicit_model: str | None,
) -> tuple[dict | None, str]:
    provider_cfg = providers.get(provider_key)
    if explicit_model:
        normalized_model = MODEL_ALIASES.get(provider_key, {}).get(explicit_model, explicit_model)
        return provider_cfg, normalized_model
    if provider_cfg and provider_cfg.get("models"):
        return provider_cfg, list(provider_cfg["models"].keys())[0]
    return provider_cfg, provider_key


def classify_preflight_failure_code(error_msg: str | None) -> str:
    lowered = (error_msg or "").lower()
    if "invalid model" in lowered or ("model" in lowered and "not found" in lowered):
        return "invalid_model"
    if any(token in lowered for token in ["401", "authentication", "permission", "user not found"]):
        return "auth_or_permission"
    if any(token in lowered for token in ["balance", "quota", "insufficient", "credits"]):
        return "billing_or_quota"
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    if "unexpected payload" in lowered or "empty" in lowered or "json" in lowered:
        return "invalid_or_empty_payload"
    return "provider_error"


def preflight_user_action(failure_code: str | None) -> str:
    return PREFLIGHT_ACTIONS.get(
        failure_code or "",
        "Inspect the provider error, then retry preflight.",
    )
