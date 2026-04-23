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
    "queue is busy",
    "already running",
]

PREFLIGHT_ACTIONS = {
    "missing_api_key": "Enter an API key before running live analysis.",
    "unknown_provider": "Choose a configured provider or add provider settings first.",
    "invalid_model": "Pick a model listed by the provider, then run preflight again.",
    "auth_or_permission": "Check that the API key is valid and has access to this provider/model.",
    "billing_or_quota": "Check provider balance, quota, or account limits before retrying.",
    "rate_limited": "The provider is currently rate-limited; wait briefly or switch model/provider.",
    "queue_busy": "Another local live analysis is running; wait for it to finish, then retry.",
    "timeout": "Try a faster model or retry when the provider is responsive.",
    "invalid_or_empty_payload": (
        "Try a model with reliable JSON output before running the full analysis."
    ),
}

_FALLBACK_MODEL_LIMIT = 3

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
    if any(token in lowered for token in ["429", "rate limit", "rate-limited", "ratelimit"]):
        return "rate_limited"
    if "queue is busy" in lowered or "already running" in lowered:
        return "queue_busy"
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


def provider_recovery_actions(
    providers: Mapping[str, dict],
    provider_key: str,
    model_name: str | None,
    failure_code: str | None,
) -> list[str]:
    actions = [preflight_user_action(failure_code)]
    provider_cfg = providers.get(provider_key) or {}
    models = list((provider_cfg.get("models") or {}).keys())
    alternates = [model for model in models if model and model != model_name]

    if failure_code == "rate_limited":
        actions.append("Wait for the provider rate-limit window, then rerun preflight.")
        if alternates:
            choices = ", ".join(alternates[:_FALLBACK_MODEL_LIMIT])
            actions.append(f"Try another {provider_key} model your key can access: {choices}.")
        if provider_key == "openrouter" and model_name and model_name.startswith("deepseek/"):
            actions.append(
                "If this OpenRouter key is DeepSeek-only, retry DeepSeek later or use a direct "
                "DeepSeek provider key."
            )
    elif failure_code in {"invalid_or_empty_payload", "timeout"} and alternates:
        choices = ", ".join(alternates[:_FALLBACK_MODEL_LIMIT])
        actions.append(f"Try another {provider_key} model with reliable JSON output: {choices}.")

    deduped: list[str] = []
    for action in actions:
        if action and action not in deduped:
            deduped.append(action)
    return deduped


def provider_recovery_action(
    providers: Mapping[str, dict],
    provider_key: str,
    model_name: str | None,
    failure_code: str | None,
) -> str:
    return " ".join(provider_recovery_actions(providers, provider_key, model_name, failure_code))
