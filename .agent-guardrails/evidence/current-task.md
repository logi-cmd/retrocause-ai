# Current Task Evidence

## Task

Investigate and improve why every evidence chain appears to have `0` refuting evidence, and make the output more useful for users inspecting a causal explanation.

## Root Cause

- The data model already had `refuting_evidence_ids`, and uncertainty scoring could consume them.
- The live pipeline did not populate them: graph building and evidence anchoring treated every matched evidence item as supporting evidence.
- The homepage then rendered the empty list as `0 refute`, which read like a factual finding even though no dedicated refutation coverage had been performed.

## Files Touched For This Task

- `retrocause/models.py`
- `retrocause/llm.py`
- `retrocause/collector.py`
- `retrocause/anchoring.py`
- `retrocause/engine.py`
- `retrocause/api/main.py`
- `frontend/src/app/page.tsx`
- `tests/test_auto_collect.py`
- `tests/test_anchoring.py`
- `tests/test_comprehensive.py`
- `docs/superpowers/specs/2026-04-13-harness-value-design.md`
- `.agent-guardrails/evidence/current-task.md`

Note: the working tree already contained unrelated local edits before this task. This evidence note records the commands and risks for the current task only.

## Changes

- Added evidence stance metadata (`supporting`, `refuting`, `context`) to extracted and stored evidence.
- Updated the LLM evidence extraction prompt to request stance and parse it conservatively.
- Updated evidence collection to preserve stance and stance basis from LLM extraction or fallback summaries.
- Updated evidence anchoring to split matched evidence into `supporting_evidence_ids` and `refuting_evidence_ids` based on explicit stance.
- Added API fields:
  - evidence-level `stance` and `stance_basis`
  - edge/chain-level `refutation_status`
- Added honest refutation statuses:
  - `has_refutation`
  - `no_refutation_in_retrieved_evidence`
  - `not_checked`
- Updated the homepage to show challenge/refutation coverage status instead of presenting missing refutations as a definitive `0`.
- Expanded the left-panel reason summary so each edge can show a concrete evidence excerpt, not only factor names and counts.
- Added a targeted challenge retrieval pass for key causal edges after CausalRAG:
  - generates challenge queries such as evidence against `source -> target`
  - stores explicit challenge evidence with `stance="refuting"` and `stance_basis="challenge_retrieval"`
  - records per-edge check status, result counts, refuting counts, and context counts
- Re-anchors hypotheses after CausalRAG and challenge retrieval append new evidence, so UI bindings reflect the latest evidence pool.
- Added top-level V2 API fields:
  - `challenge_checks`
  - `analysis_brief`
- Added a user-facing analysis brief with:
  - likely explanation
  - top reasons with evidence excerpts
  - challenge summary
  - missing-evidence notes
  - source coverage summary
- Updated the homepage to render an "Analysis brief" card and a right-panel "Challenge coverage" card, both included in Chinese/English switching.
- Synchronized project documentation for the new challenge/brief behavior and added a project-state working rule that future behavior/API/UI/pipeline changes must update docs.
- Added provider preflight harness:
  - new `/api/providers/preflight` endpoint
  - checks provider config, API key presence, local model catalog status, and tiny JSON model access
  - returns actionable failure codes for missing key, invalid model, auth/permission, quota, timeout, and invalid/empty payloads
- Added product value harness:
  - new `product_harness` field on V2 analysis responses
  - scores causal chain presence, analysis summary, source trace, evidence stance, challenge coverage, and actionable failure detail
  - classifies outputs as `ready_for_review`, `needs_more_evidence`, `blocked_by_model`, or `not_reviewable`
- Updated the homepage advanced provider settings with a model preflight action and visible diagnosis.
- Updated the homepage left panel with a value harness card so users can see whether a result is reviewable or blocked.
- Added a harness design note under `docs/superpowers/specs/`.
- Updated OSS readiness documentation to state that the current repo is locally usable alpha, not yet a polished public OSS release.
- Added release-readiness gates for the US/Iran Islamabad talks golden case, first-run docs, screenshots, and direct monetization packaging.
- Documented that direct monetization needs a repeatable brief/report/share workflow, not only causal graph inspection.
- Ran the US/Iran Islamabad talks golden case through provider preflight, API, and browser UI with OpenRouter DeepSeek V3.
- Fixed the Chinese localization regex for `ear` so words like `nuclear` are no longer rendered as `nucl出口管理条例`.
- Added the live golden-case screenshot to `docs/images/golden-us-iran-live-ui.png`.
- Updated docs to reflect that the OSS repo is now a local alpha / release candidate, with remaining work focused on release packaging and first-time visitor review.

## Commands Run

- `pytest tests/test_anchoring.py tests/test_comprehensive.py -q`
  - Result: 61 passed.
- `pytest tests/test_auto_collect.py::test_collect_refutations_searches_challenge_queries_and_marks_stance tests/test_comprehensive.py::test_result_to_v2_surfaces_challenge_checks_and_analysis_brief -q`
  - Result: initially failed as expected before implementation, then passed after adding challenge retrieval and API brief fields.
- `pytest tests/test_auto_collect.py::test_collect_refutations_searches_challenge_queries_and_marks_stance tests/test_comprehensive.py::test_result_to_v2_surfaces_challenge_checks_and_analysis_brief tests/test_comprehensive.py::test_v2_schema_round_trip -q`
  - Result: 3 passed.
- `pytest tests/test_auto_collect.py tests/test_comprehensive.py tests/test_anchoring.py -q`
  - Result: 76 passed.
- `pytest tests/test_integration.py tests/test_causal_rag.py tests/test_engine.py -q`
  - Result: 28 passed.
- `ruff check retrocause tests`
  - Result: passed.
- `npm run lint` in `frontend/`
  - Result: 0 errors, 7 existing warnings in unrelated component files.
- `npm run build` in `frontend/`
  - Result: passed.
  - Warning: Next.js inferred workspace root because both root and frontend lockfiles exist.
- `npm test` at repo root
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 208 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: pass-with-concerns, 80/100.
  - Non-blocking warnings remain because the working tree already includes broad docs/state changes from earlier local work.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after documentation sync
  - Result: pass-with-concerns, 80/100.
  - Non-blocking warnings remain scope/continuity warnings for broad local diff; no missing required commands or evidence file.
- `pytest tests/test_comprehensive.py::test_provider_preflight_classifies_missing_api_key tests/test_comprehensive.py::test_provider_preflight_runs_model_health_check tests/test_comprehensive.py::test_product_harness_marks_model_blocked_empty_result_as_actionable tests/test_comprehensive.py::test_product_harness_rewards_useful_evidence_backed_result -q`
  - Result: initially failed as expected before implementation because the preflight and product harness API did not exist, then passed after implementation.
- `ruff check retrocause\api\main.py tests\test_comprehensive.py`
  - Result: passed.
- `npm --prefix frontend run lint`
  - Result: 0 errors, 7 existing warnings in unrelated component files.
- `npm --prefix frontend run build`
  - Result: passed.
  - Warning: Next.js inferred workspace root because both root and frontend lockfiles exist.
- `npm test`
  - First run result: failed only at `python scripts/e2e_test.py` because backend `127.0.0.1:8000` was not running; frontend lint/build, ruff, and pytest had passed before that failure.
- `python start.py` via background `Start-Process`
  - Result: started FastAPI on `127.0.0.1:8000` and Next.js on `localhost:3005`.
- `npm test`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 212 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: pass-with-concerns, 80/100.
  - Non-blocking warnings remain scope/continuity warnings for broad local diff and state-related files; no missing required commands or evidence file.
- Documentation sync for OSS readiness
  - Files updated: `README.md`, `docs/PROJECT_STATE.md`, `docs/roadmap-and-limitations.md`, `.agent-guardrails/evidence/current-task.md`.
  - Result: current docs now distinguish local alpha completeness from public OSS release completeness.
- `npm test` after OSS readiness documentation sync
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 212 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
  - Frontend lint still reports 7 existing warnings in unrelated component files.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after OSS readiness documentation sync
  - Result: pass-with-concerns, 80/100.
  - Non-blocking warnings remain scope/continuity warnings for broad local diff and state-related files; no missing required commands or evidence file.
- `POST /api/providers/preflight` with OpenRouter candidate models
  - Result: `deepseek/deepseek-chat-v3-0324`, `deepseek/deepseek-r1`, `openai/gpt-4o-mini`, `openai/gpt-4.1-mini`, `qwen/qwen3-235b-a22b`, `moonshotai/kimi-k2`, and `mistralai/mistral-small-3.1-24b-instruct` passed lightweight JSON preflight.
  - `google/gemini-2.5-flash-preview` returned invalid model ID.
- `POST /api/analyze/v2` for `美国和伊朗在伊斯兰堡谈判结束 未达成协议的原因是什么` using UTF-8 JSON bytes and OpenRouter `deepseek/deepseek-chat-v3-0324`
  - Result: live golden case passed.
  - `analysis_mode=live`, `freshness_status=fresh`, `is_demo=false`, 7 chains, 19 evidence items, 7 retrieval trace rows, 3 challenge checks, analysis brief present, `product_harness.status=ready_for_review`, score 1.0.
  - Saved response: `logs/golden-us-iran-utf8-deepseek-v2-response.json`.
- gstack browse golden browser run for the same query
  - Result: Live coverage 100%, source trace visible, challenge coverage visible, value harness visible, no console errors.
  - Screenshot saved to `logs/golden-us-iran-live-ui.png` and copied to `docs/images/golden-us-iran-live-ui.png`.
- `npm test` after golden-case docs and frontend localization fix
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 212 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
  - Frontend lint still reports 7 existing warnings in unrelated component files.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after golden-case docs and frontend localization fix
  - Result: pass-with-concerns, 80/100.
  - Non-blocking warnings remain scope/continuity warnings for broad local diff and state-related files; no missing required commands or evidence file.

## Residual Risks

- The challenge pass is deliberately bounded to a few key edges to control latency and source cost; it is not exhaustive adversarial research.
- LLM stance extraction is conservative by prompt and parser, but still depends on model behavior.
- `context` evidence is currently surfaced via challenge status and evidence cards rather than represented as a separate third edge bucket.
- The analysis brief is deterministic API synthesis over current graph/evidence fields, not an additional LLM-written conclusion.
- Provider preflight is a lightweight health check; a passing result does not guarantee that the full causal run will stay within provider latency/rate limits.
- The product value harness is a usability gate, not a truth oracle. It checks whether the result is reviewable and evidence-visible, not whether the causal conclusion is definitively correct.
- The OSS repo is usable as a local alpha, but should not be described as a polished public release until the OpenRouter golden case and first-run docs pass.
- Direct monetization value remains workflow-dependent; graph inspection alone is less sellable than brief/report/share outputs for repeated market, policy, or strategy use cases.
- The US/Iran golden case is now live-validated, but the visible Chinese UI still intentionally falls back to generic Chinese labels for some long English model labels instead of fully translating every generated phrase.
- API calls from Windows PowerShell need explicit UTF-8 JSON bytes for Chinese queries; otherwise the query can arrive as question marks and produce misleading failure results.
- Frontend lint warnings remain in pre-existing unrelated files; no lint errors were introduced.
