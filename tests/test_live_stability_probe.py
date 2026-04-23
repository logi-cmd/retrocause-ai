from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from retrocause.app.demo_data import PROVIDERS
from scripts import live_stability_probe as probe


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_live_stability_probe_defaults_to_ofoxai_catalog(monkeypatch):
    monkeypatch.delenv("RETROCAUSE_LIVE_MODELS", raising=False)

    candidates = probe._models_from_env()

    assert probe.DEFAULT_PROVIDER == "ofoxai"
    assert candidates == list(PROVIDERS["ofoxai"]["models"].keys())
    assert candidates[0] == "openai/gpt-5.4-mini"
    assert "deepseek/deepseek-chat-v3-0324" not in candidates


def test_live_stability_probe_allows_explicit_model_override(monkeypatch):
    monkeypatch.setenv(
        "RETROCAUSE_LIVE_MODELS",
        "mistralai/mistral-small-3.1-24b-instruct, moonshotai/kimi-k2 ",
    )

    assert probe._models_from_env() == [
        "mistralai/mistral-small-3.1-24b-instruct",
        "moonshotai/kimi-k2",
    ]


def test_live_stability_probe_missing_key_writes_blocked_report(monkeypatch, capsys):
    output_dir = REPO_ROOT / ".tmp-tests"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{uuid4().hex}_live-probe.json"
    monkeypatch.delenv("OFOXAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("RETROCAUSE_LIVE_PROBE_OUTPUT", str(output_path))

    try:
        exit_code = probe.main()

        assert exit_code == 2
        report_text = output_path.read_text(encoding="utf-8")
        payload = json.loads(report_text)
        assert payload["verdict"] == "blocked"
        assert payload["provider"] == "ofoxai"
        assert payload["keys"]["OFOXAI_API_KEY"] == "missing"
        assert payload["blocker"] == "OFOXAI_API_KEY is missing."

        printed = json.loads(capsys.readouterr().out)
        assert printed["keys"]["OFOXAI_API_KEY"] == "missing"
        assert "sk-" not in report_text
    finally:
        output_path.unlink(missing_ok=True)
