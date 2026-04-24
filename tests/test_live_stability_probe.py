from __future__ import annotations

import json
from pathlib import Path

from scripts import live_stability_probe as probe


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_live_stability_probe_has_keyless_oss_scenarios():
    assert {scenario["id"] for scenario in probe.SCENARIOS} == {
        "market_zh_a_share",
        "policy_geopolitics_semiconductors",
        "postmortem_public_incident",
    }


def test_live_stability_probe_report_contains_no_secret_fields(monkeypatch, capsys):
    output_path = REPO_ROOT / ".agent-guardrails" / "evidence" / "local-stability-probe.json"
    monkeypatch.chdir(REPO_ROOT)

    try:
        exit_code = probe.main()
        assert exit_code == 0

        report_text = output_path.read_text(encoding="utf-8")
        payload = json.loads(report_text)
        assert payload["mode"] == "keyless_oss"
        assert payload["verdict"] == "pass"
        assert "keys" not in payload
        assert "api_key" not in report_text
        assert "OPENROUTER" not in report_text
        assert "OFOXAI" not in report_text

        printed = json.loads(capsys.readouterr().out)
        assert printed["mode"] == "keyless_oss"
    finally:
        output_path.unlink(missing_ok=True)
