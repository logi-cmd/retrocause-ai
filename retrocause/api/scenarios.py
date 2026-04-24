from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionScenarioPayload:
    key: str
    label: str
    confidence: float
    detection_method: str
    user_value: str


PRODUCTION_SCENARIOS: dict[str, tuple[str, str]] = {
    "market": (
        "Market / Investment Brief",
        "Helps users inspect market-moving factors, evidence freshness, and trade/research risks.",
    ),
    "policy_geopolitics": (
        "Policy / Geopolitics Brief",
        "Helps users inspect policy or geopolitical drivers, source reliability, and negotiation constraints.",
    ),
    "postmortem": (
        "Postmortem Brief",
        "Helps teams inspect incident, product, or business causes and the evidence needed before action.",
    ),
    "general": (
        "General Causal Brief",
        "Helps users inspect likely causes, evidence, counterpoints, and gaps.",
    ),
}

SCENARIO_SIGNALS: dict[str, list[str]] = {
    "market": [
        "market",
        "stock",
        "bitcoin",
        "crypto",
        "price",
        "yield",
        "rate",
        "earnings",
        "etf",
    ],
    "policy_geopolitics": [
        "policy",
        "sanction",
        "talks",
        "ceasefire",
        "negotiation",
        "election",
        "treaty",
        "war",
    ],
    "postmortem": [
        "our",
        "incident",
        "outage",
        "conversion",
        "release",
        "churn",
        "customer",
        "retention",
    ],
}


def _scenario_payload_from_key(
    key: str,
    confidence: float,
    detection_method: str,
) -> ProductionScenarioPayload:
    normalized_key = key if key in PRODUCTION_SCENARIOS else "general"
    bounded_confidence = max(0.0, min(1.0, confidence))
    label, user_value = PRODUCTION_SCENARIOS[normalized_key]
    return ProductionScenarioPayload(
        key=normalized_key,
        label=label,
        confidence=bounded_confidence,
        detection_method=detection_method,
        user_value=user_value,
    )


def detect_production_scenario_payload(
    query: str,
    domain: str = "general",
    override: str | None = None,
) -> ProductionScenarioPayload:
    if override in PRODUCTION_SCENARIOS:
        return _scenario_payload_from_key(override, 1.0, "override")

    normalized = f"{query} {domain}".lower()
    scored = {
        key: sum(1 for token in tokens if token in normalized)
        for key, tokens in SCENARIO_SIGNALS.items()
    }
    key, count = max(scored.items(), key=lambda item: item[1])
    if count <= 0:
        return _scenario_payload_from_key("general", 0.35, "auto")
    return _scenario_payload_from_key(key, min(0.95, 0.45 + count * 0.15), "auto")
