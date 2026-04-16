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

- Multi-user/persona testing continuation
  - Scope: added repeatable regression coverage for user-facing value states instead of optimizing only one question.
  - Files updated: `tests/test_comprehensive.py`, `docs/PROJECT_STATE.md`, `.agent-guardrails/evidence/current-task.md`.
  - Persona paths covered:
    - new user without an API key gets a demo-mode response with an analysis brief, Markdown brief, product harness status, and next actions.
    - constrained user with an invalid live key gets `analysis_mode=partial_live`, `product_harness.status=blocked_by_model`, a Markdown failure report, and a provider-preflight next action.
    - reviewer user can audit degraded source rows (`rate_limited`, `forbidden`, and `ok`) and see source coverage plus retry/permission status in the Markdown brief.
- `pytest tests/test_comprehensive.py::test_multi_user_persona_outputs_are_actionable tests/test_comprehensive.py::test_multi_user_reviewer_can_audit_degraded_source_states -q`
  - Result: 2 passed.
- `ruff check tests\test_comprehensive.py`
  - Result: passed.
- `npm test`
  - First result: failed after frontend lint/build, `ruff check retrocause/`, and `pytest tests/ --basetemp=.pytest-tmp` passed.
  - Failure: Playwright E2E hit a disabled submit button because the browser harness interacted before the hydrated page exposed an enabled query button; the initial sticky-card count was also `0`.
  - Follow-up: restarted stale local RetroCause dev processes that had been running since 2026-04-15 and hardened `scripts/e2e_test.py` to wait for visible sticky cards plus an enabled Analyze/分析 button.
- `ruff check scripts\e2e_test.py tests\test_comprehensive.py`
  - Initial result: failed on pre-existing script lint issues exposed by the new touched-file check (`Any` unused, unused `cid`, two placeholder-free f-strings).
  - Final result after cleanup: passed.
- `python scripts\e2e_test.py`
  - Result after E2E harness stabilization and local service restart: passed, 604 passed / 0 failed / 0 skipped.
- `npm test`
  - Result after E2E harness stabilization: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 251 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after commit `56a7a53`
  - Initial result: blocked, 68.6/100.
  - Cause: the existing task contract did not include `scripts/e2e_test.py`, but the E2E harness fix was required after `npm test` exposed a disabled-button hydration race.
- `agent-guardrails plan --task "Add multi-user/persona regression coverage for user-value outputs and stabilize the browser E2E harness when hydration leaves the submit button disabled." --allow-paths "tests/,docs/,.agent-guardrails/evidence/,.agent-guardrails/task-contract.json,scripts/e2e_test.py" --required-commands "npm test" --evidence ".agent-guardrails/evidence/current-task.md" --risk-level low --allowed-change-types "tests,docs,guardrails-internal"`
  - Result: updated `.agent-guardrails/task-contract.json` so the contract matches the actual test/docs/harness scope.
  - Security/auth/secrets: no real API keys were added; the invalid-key persona uses a dummy `sk-test` and monkeypatched provider failure. No new permissions or sensitive-data storage paths were introduced.
  - Dependencies: no package or lockfile changes.
  - Performance/load: no runtime pipeline work was added; the only browser harness waits are capped at 10 seconds and run in tests only.
  - Maintainability tradeoff: the E2E script now waits for hydrated UI state instead of assuming `networkidle` is enough, which makes browser QA less flaky at the cost of a small test-only wait.
  - Continuity: reused the existing comprehensive API test file, existing project-state doc, existing evidence note, and existing E2E script; no new abstractions or test frameworks were introduced.

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
- OSS publishing preparation for `logi-cmd`
  - Result: created a clean export directory at `D:\opencode\retrocause-ai-public-20260413`.
  - Included root user-facing/project files, backend package, frontend source/config, examples, tests, scripts needed for smoke/E2E, GitHub workflows, and `docs/images/golden-us-iran-live-ui.png`.
  - Excluded local/internal/nonessential publish artifacts: `.agent-guardrails`, `.codex`, `.gstack`, `logs`, `docs-private`, `docs/superpowers`, root screenshot scratch files, `node_modules`, `.next`, and local caches.
  - Removed nonessential temporary test scripts from the export after secret scanning found old hardcoded OpenRouter keys in those scratch scripts.
  - Interpreted "publish with logi-cmd" as GitHub publishing through the authenticated `logi-cmd` account because no local `logi-cmd` CLI was present.
- `npm --prefix frontend install next@16.2.3`
  - Result: updated Next.js in the source repo after `npm audit` identified a high-severity advisory in 16.2.2.
- `npm --prefix frontend install eslint-config-next@16.2.3`
  - Result: synchronized ESLint config with the Next.js runtime version; `npm audit` reported 0 vulnerabilities.
- `npm install next@16.2.3` and `npm install eslint-config-next@16.2.3` in `D:\opencode\retrocause-ai-public-20260413\frontend`
  - Result: synchronized the publish export with the source dependency fix; `npm audit` reported 0 vulnerabilities.
- Secret scan in `D:\opencode\retrocause-ai-public-20260413`
  - Result: no `sk-or-v1-`, `ghp_`, `gho_`, or `GITHUB_PERSONAL_ACCESS_TOKEN` patterns remained in the export after removing scratch scripts.
- Publish export validation
  - `npm --prefix frontend run lint`: passed with 0 errors and the same 7 existing warnings.
  - `npm --prefix frontend run build`: passed on Next.js 16.2.3; retained the existing multi-lockfile workspace-root warning.
  - `ruff check retrocause/`: passed.
  - `pytest tests/ --basetemp=.pytest-tmp`: 212 passed.
  - `python scripts/e2e_test.py` against export backend `127.0.0.1:8002` and export frontend `localhost:3005`: passed with exit code 0.
- Source repo validation after release README, ignore rules, and dependency sync
  - `npm test`: passed with exit code 0 after starting the source frontend on `localhost:3005` and using the already-running source backend on `127.0.0.1:8000`.
- Alpha.2 public export validation in `D:\opencode\retrocause-ai-public-20260413`
  - `npm --prefix frontend run lint`: passed with 0 warnings and 0 errors.
  - `npm --prefix frontend run build`: passed on Next.js 16.2.3 without the previous multi-lockfile warning.
  - `ruff check retrocause/`: passed.
  - `pytest tests/ --basetemp=.pytest-tmp`: 212 passed.
- Alpha.2 source repo validation
  - Created/used local `.venv` because the global Python environment could not import `uvicorn` for backend startup.
  - `npm test`: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 212 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- GitHub publication
  - Created and pushed the clean public repository with GitHub CLI authenticated as `logi-cmd`.
  - Published URL: `https://github.com/logi-cmd/retrocause-ai`.
  - Initial public commit in the export repo: `8436920 Initial open-source release`.
- GitHub prerelease
  - Created prerelease tag `v0.1.0-alpha.1` for the public repository.
  - Release URL: `https://github.com/logi-cmd/retrocause-ai/releases/tag/v0.1.0-alpha.1`.
  - Release notes include working features, quick-start commands, validation results, and known limits.
- GitHub prerelease alpha.2
  - Created and published prerelease tag `v0.1.0-alpha.2` for the public repository.
  - Release URL: `https://github.com/logi-cmd/retrocause-ai/releases/tag/v0.1.0-alpha.2`.
  - Public commit: `26d043e Polish alpha release docs and lint`.
  - Release notes include README status polish, zero-warning frontend lint, Turbopack root config, validation results, and known limits.
- Source repo alpha.2 state commit
  - Created local source commit `Prepare alpha release polish`.
  - This keeps README, project state, frontend alpha.2 polish, dependency metadata, task contract, and evidence notes in one reviewable checkpoint.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after source alpha.2 commit
  - Result: pass-with-concerns, 80/100.
  - Blocking errors: 0.
  - Remaining warnings: cross-top-level release scope, dependency metadata config change, and project-state continuity notes.
  - Mitigation: task contract explicitly declares docs/config/guardrails/internal release polish, rollback notes, and risk justification.
- WSL default distro investigation and fix
  - `wsl.exe -l -v`: initially showed `docker-desktop` as the default distro and `Ubuntu-24.04` absent.
  - `wsl.exe -d docker-desktop -e /bin/sh -c 'ls -l /bin/bash /bin/sh 2>/dev/null; cat /etc/os-release 2>/dev/null || true'`: showed `/bin/sh -> /bin/busybox`, Docker Desktop, and no `/bin/bash`.
  - `bash.exe -lc 'echo bash-ok'`: reproduced `execvpe(/bin/bash) failed: No such file or directory`.

## 2026-04-14 Production Brief Harness Implementation

### Task

Implement the approved Production Brief Harness across API, frontend, Markdown export, tests, and docs.

### Files Touched

- `retrocause/api/main.py`
- `frontend/src/app/page.tsx`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/superpowers/plans/2026-04-14-production-brief-harness.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- `pytest tests/test_comprehensive.py::test_detects_market_production_scenario tests/test_comprehensive.py::test_detects_policy_geopolitics_production_scenario tests/test_comprehensive.py::test_detects_postmortem_production_scenario tests/test_comprehensive.py::test_scenario_override_wins_over_auto_detection -q`
  - Result: passed after adding scenario detection and override handling.
- `pytest tests/test_comprehensive.py::test_market_production_brief_has_expected_sections tests/test_comprehensive.py::test_policy_production_brief_has_expected_sections tests/test_comprehensive.py::test_postmortem_production_brief_has_expected_sections -q`
  - Result: passed after adding production brief sections.
- `pytest tests/test_comprehensive.py::test_recent_market_result_needs_fresh_evidence_before_ready tests/test_comprehensive.py::test_policy_result_with_weak_source_trace_surfaces_source_risk tests/test_comprehensive.py::test_postmortem_without_internal_evidence_is_not_actionable -q`
  - Result: passed after adding production harness readiness checks.
- `pytest tests/test_comprehensive.py::test_analyze_v2_accepts_scenario_override_without_live_key -q`
  - Result: passed after wiring `scenario_override` into V2 analysis paths.
- `pytest tests/test_comprehensive.py::test_frontend_renders_production_brief_and_use_case_selector tests/test_comprehensive.py::test_frontend_offers_three_production_use_cases -q`
  - Result: passed after frontend selector and production brief rendering.
- `pytest tests/test_comprehensive.py::test_markdown_brief_title_uses_detected_market_scenario tests/test_comprehensive.py::test_markdown_brief_includes_production_verification_steps -q`
  - Result: passed after Markdown export included production brief sections.
- `pytest tests/test_comprehensive.py::test_frontend_does_not_hardcode_single_case_product_labels -q`
  - Result: failed as expected before removing single-case frontend labels.
- `pytest tests/test_comprehensive.py::test_frontend_does_not_hardcode_single_case_product_labels tests/test_comprehensive.py::test_frontend_keeps_specific_live_node_labels -q`
  - Result: passed after removing single-case graph-label product logic.
- `npm --prefix frontend run lint`
  - Result: passed.
- `ruff check retrocause\api\main.py tests\test_comprehensive.py`
  - Result: passed.
- `pytest tests/test_comprehensive.py::test_markdown_brief_explains_checked_edges_without_refuting_evidence tests/test_comprehensive.py::test_markdown_brief_includes_production_verification_steps tests/test_comprehensive.py::test_policy_production_brief_has_expected_sections -q`
  - Result: passed after replacing the new `0 challenge evidence` phrasing with an explicit no-challenge-evidence sentence.
- `ruff check retrocause\api\main.py`
  - Result: passed.
- `npm test`
  - First result: failed only because `test_markdown_brief_explains_checked_edges_without_refuting_evidence` caught a new `0 challenge evidence` phrase in production brief verification text.
- `npm test`
  - Final result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 234 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: passed with trust score 95/100.
  - Blocking errors: 0.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed; this is expected because project documentation sync is required for this task.

### Residual Risks

- Scenario detection is deterministic keyword routing; deeper domain-specific source policies remain Pro/future work.
- Latest-info readiness still depends on available live retrieval sources and provider behavior.
- Production brief sections are evidence-anchored, but high-stakes publication still needs human review of source quality and missing-evidence notes.

## 2026-04-15 Retrieval And Small-Team Pro Strategy

### Task

Integrate the product discussion about source adapter rate limits, better retrieval sources, personal/small-team positioning, uploaded evidence, and why the output needs a retrieval-to-brief pipeline instead of a direct ChatGPT prompt.

### Files Touched

- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/pro-workflow-spec.md`
- `docs/retrieval-and-output-strategy.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, and the planned documentation files before editing.
- Reviewed current source adapters under `retrocause/sources/`.
- Searched project docs for retrieval, evidence, CausalRAG, source trace, harness, and Pro workflow references.
- Checked official provider documentation for candidate hosted retrieval sources:
  - Tavily rate limits: `https://docs.tavily.com/documentation/rate-limits`
  - Brave Search API terms: `https://api-dashboard.search.brave.com/documentation/resources/terms-of-service`
  - Exa contents retrieval: `https://docs.exa.ai/reference/contents-retrieval-with-exa-api`
  - SerpAPI high-volume/account API docs: `https://serpapi.com/high-volume` and `https://serpapi.com/account-api`
- `npm test`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 234 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: passed with trust score 95/100.
  - Blocking errors: 0.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed; this is expected because the task intentionally synchronizes project state documentation.

### Changes

- Added `docs/retrieval-and-output-strategy.md` with the retrieval-to-output pipeline, source adapter risks, source portfolio, scenario source policies, cache policy, run orchestrator direction, product output contract, and development-skill usage.
- Updated README to point to the retrieval strategy and clarify source-policy/rate-limit direction.
- Updated `docs/pro-workflow-spec.md` to focus on Solo Pro / Team Lite hosted reliability instead of enterprise/private deployment.
- Updated `docs/PROJECT_STATE.md` so the next implementation step is SourceBroker/run-orchestration planning.

### Residual Risks

- This pass is documentation and product/architecture strategy only; no source adapter or run orchestration code has been implemented yet.
- Hosted-source candidates have provider-specific pricing, storage, and rate-limit terms that must be rechecked before implementation.
- Public docs should avoid promising unlimited search, enterprise private deployment, or unsupported provider storage behavior.
  - `wsl.exe --install Ubuntu-24.04`: timed out after distro registration, but `wsl.exe -l -v` showed `Ubuntu-24.04` installed.
  - `wsl.exe --set-default Ubuntu-24.04`: default changed from `docker-desktop` to `Ubuntu-24.04`.
  - Killed stuck `wsl.exe` / `bash.exe` client processes after Ubuntu first-run initialization hung; WSL service remained running.
  - `bash.exe -lc "echo bash-ok; cat /etc/os-release | head -2"`: passed and reported `Ubuntu 24.04.4 LTS`.
- Documentation sync for OSS/Pro boundary
  - `README.md`: added explicit OSS vs Pro boundary and stated planned OSS Markdown research brief.
  - `docs/PROJECT_STATE.md`: updated current focus, blockers, done-recently, and next step for OSS Markdown brief vs Pro workflows.
  - `docs/roadmap-and-limitations.md`: clarified Markdown brief as OSS, with PDF/DOCX/team/scheduled/branded workflows Pro-first.
- Project state documentation
  - Updated `docs/PROJECT_STATE.md` to record that the OSS package is now published as an alpha prerelease rather than only a local release candidate.
- Guardrails scope maintenance
  - Updated `.agent-guardrails/task-contract.json` to include `.gitignore`, because release packaging intentionally added local-only publish exclusions for logs, caches, internal docs, and guardrail state.
- Alpha.2 polish
  - Cleaned frontend lint warnings in reusable UI components.
  - Added `turbopack.root` to `frontend/next.config.ts` so Next.js no longer warns about multiple lockfiles during build.
  - Updated README and project state to point at `v0.1.0-alpha.2`.
  - Validated the public export with frontend lint/build, backend lint, and full pytest.
  - Validated the source repo with root `npm test` using the local `.venv` Python environment.
- OSS/Pro boundary and local tooling follow-up
  - Confirmed the product boundary: OSS should include a copyable Markdown research brief for individual research and analysis workflows.
  - Confirmed Pro should focus on hosted operation, PDF/DOCX, team sharing, scheduled briefings, saved comparisons, source policy controls, domain packs, and branded deliverables.
  - Installed `Ubuntu-24.04` under WSL and set it as the default distro instead of Docker Desktop's internal `docker-desktop` distro.
  - Verified `bash.exe -lc "echo bash-ok"` now runs against Ubuntu 24.04.4 LTS.
  - Configured WSL's default Ubuntu user as non-root user `retrocause`; verified `/usr/bin/bash` and passwordless sudo are available.
  - Updated README, project state, and roadmap documentation with the OSS/Pro boundary.
  - Re-ran root `npm test` after starting the local API and frontend services; frontend lint/build, `ruff check retrocause/`, `pytest tests/`, and script E2E all passed.
  - Ran `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`; result was `pass-with-concerns` at 80/100 with 4 non-blocking warnings about broad historical release-scope diff, config metadata, and project-state files.
- OSS Markdown research brief follow-up
  - Added `markdown_brief` to the V2 API response.
  - Built the Markdown brief deterministically from existing grounded response fields: query, run status, likely explanation, top reasons, challenge coverage, gaps, evidence, source trace, and use note.
  - Added a browser "Copy Markdown" action on the analysis brief card.
  - Updated README, project state, and roadmap docs to state that the OSS Markdown brief now exists, while PDF/team/scheduled/branded workflows remain Pro-oriented.
  - TDD red check: `pytest tests/test_comprehensive.py::test_result_to_v2_builds_copyable_markdown_research_brief -q` failed because `AnalyzeResponseV2` had no `markdown_brief`.
  - Green check: `pytest tests/test_comprehensive.py::test_result_to_v2_builds_copyable_markdown_research_brief tests/test_comprehensive.py::test_result_to_v2_surfaces_challenge_checks_and_analysis_brief -q` passed.
  - Frontend checks: `npm --prefix frontend run lint` passed; `npm --prefix frontend run build` passed.
  - Focused verification: `ruff check retrocause\api\main.py tests\test_comprehensive.py` passed; `pytest tests/test_comprehensive.py::test_result_to_v2_builds_copyable_markdown_research_brief tests/test_comprehensive.py::test_v2_schema_round_trip tests/test_comprehensive.py::test_product_harness_rewards_useful_evidence_backed_result -q` passed.
  - Full verification: `npm test` passed after starting local FastAPI and Next.js services. Pytest result: 213 passed. E2E result: 604 passed, 0 failed, 0 skipped.
  - First feature guardrail check: `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` failed because the task contract still described the older docs/config-only release polish scope and did not allow `interface` or `tests` changes.
  - Contract correction: updated `.agent-guardrails/task-contract.json` to describe the OSS Markdown brief task, allow additive API/UI interface changes and tests, and keep Pro PDF/team/scheduled/branded workflows out of scope.
  - Second feature guardrail check: `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` passed as `safe-to-deploy`, 90/100. Remaining non-blocking warnings: feature touches 6 top-level areas because API/UI/test/docs/evidence are all involved, and `docs/PROJECT_STATE.md` changed as required by the project documentation-sync rule.

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
- Frontend lint warnings were cleaned for the alpha.2 polish pass.
- The publish export intentionally omits nonessential docs and local evidence logs, so public users see the bilingual README and runnable code but not the internal planning trail.
- The local `logi-cmd` command was not available; publishing uses the GitHub CLI authenticated as `logi-cmd`.

## 2026-04-14 Alpha.3 Readiness And Pro Workflow Follow-Up

### Task

Execute the next 1/2/3/4 sequence:

1. Run alpha.3 release readiness from a new-user path.
2. Re-verify the US/Iran Islamabad golden case and Markdown brief with OpenRouter.
3. Publish the OSS package as `v0.1.0-alpha.3` under `logi-cmd`.
4. Write a Pro workflow spec from user scenarios and monetizable value.

### Files Touched

- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/roadmap-and-limitations.md`
- `docs/pro-workflow-spec.md`
- `.agent-guardrails/evidence/current-task.md`
- `logs/golden-us-iran-alpha3-response.json`
- `logs/golden-us-iran-alpha3-brief.md`

### Commands Run

- `npm test`
  - First result: failed at `python scripts/e2e_test.py` because the E2E script assumes backend `127.0.0.1:8000` and frontend `localhost:3005` are already running.
  - Before that failure, frontend lint/build, `ruff check retrocause/`, and `pytest tests/ --basetemp=.pytest-tmp` all passed.
  - Pytest result in that run: 213 passed.
- `python -B -m uvicorn retrocause.api.main:app --host 127.0.0.1 --port 8000` via background `Start-Process`
  - Result: FastAPI listened on `127.0.0.1:8000`.
- `npm run dev -- -p 3005` in `frontend/` via background `Start-Process`
  - Result: Next.js listened on `localhost:3005`.
- `python scripts/e2e_test.py`
  - Result: passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
  - Covered demo transparency, panel toggles, zoom controls, chain B switching back to chain A, node selection, language toggle, and console health.
- OpenRouter provider preflight against `deepseek/deepseek-chat-v3-0324`
  - Result: `status=ok`, no failure code.
- `POST /api/analyze/v2` for `美国和伊朗在伊斯兰堡谈判结束 未达成协议的原因是什么` using OpenRouter `deepseek/deepseek-chat-v3-0324`
  - First PowerShell client attempt: provider preflight passed, but `Invoke-WebRequest` threw a client-side `NullReferenceException` after the backend returned `200`.
  - First Python inline attempt: returned `partial_live`, but investigation showed the Chinese query was corrupted to question marks by the Windows pipeline.
  - Corrected Python/httpx attempt using Unicode escapes for the query: passed.
  - Result: `analysis_mode=live`, `is_demo=false`, `freshness_status=fresh`, 20 evidence items, 5 chains, 3 challenge checks, 7 retrieval trace rows, product harness `ready_for_review`, score 1.0, Markdown brief length 4394.
  - Saved response: `logs/golden-us-iran-alpha3-response.json`.
  - Saved Markdown brief: `logs/golden-us-iran-alpha3-brief.md`.
- gstack browse setup/status commands
  - Result: Windows gstack browse binary exists under both `.codex` and `.claude` skill directories.
  - `goto http://localhost:3005` returned 200.
  - `console --errors` returned no console errors.
  - Snapshot/screenshot commands only printed `[browse] Starting server...` and did not produce the requested PNG, so Playwright E2E remains the reliable browser proof for this pass.
- `npm test` after README, project state, roadmap, Pro spec, and evidence sync
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, `pytest tests/ --basetemp=.pytest-tmp`, and `python scripts/e2e_test.py`.
  - Pytest result: 213 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- Public export sync to `D:\opencode\retrocause-ai-public-20260413`
  - Result: synchronized the OSS code and README for alpha.3.
  - Kept nonessential docs out of the public publish package; `docs/pro-workflow-spec.md`, `docs/PROJECT_STATE.md`, and roadmap/state docs remain source-repo documentation, not public alpha.3 payload.
  - Removed scratch scripts that contained old hardcoded OpenRouter keys before publishing.
- Public export secret scan
  - Result: clean for `sk-or-v1-`, `ghp_`, `gho_`, and `GITHUB_PERSONAL_ACCESS_TOKEN` patterns outside ignored build/cache/log folders.
- Public export validation
  - `npm --prefix frontend install`: installed frontend dependencies for verification only.
  - `npm --prefix frontend run lint`: passed.
  - `npm --prefix frontend run build`: passed.
  - `ruff check retrocause/`: passed.
  - `pytest tests/ --basetemp=.pytest-tmp`: 213 passed.
  - `python scripts/e2e_test.py` with `RETROCAUSE_E2E_BASE=http://127.0.0.1:8002` and `RETROCAUSE_E2E_FRONTEND=http://localhost:3007`: 604 passed, 0 failed, 0 skipped.
- Public GitHub publish
  - Public export commit: `8c96096 Add markdown research brief alpha`.
  - Pushed `main` to `git@github.com:logi-cmd/retrocause-ai.git`.
  - Created GitHub prerelease `v0.1.0-alpha.3`.
  - Release URL: `https://github.com/logi-cmd/retrocause-ai/releases/tag/v0.1.0-alpha.3`.
- Source documentation checkpoint
  - Source commit: `b62a692 docs: record alpha3 release and pro workflow spec`.
  - `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after the source docs commit: `safe-to-deploy`, 95/100.
  - Remaining warnings are non-blocking continuity warnings because the task intentionally updates multiple docs and `docs/PROJECT_STATE.md`.

### Observations

- The alpha.3 app is functionally ready for the Markdown brief OSS path: live golden case, challenge coverage, retrieval trace, value harness, and Markdown output all exist in the API result.
- The API field is `retrieval_trace`, not `source_trace`; user-facing docs can still call this "source trace", but tests and scripts should inspect the actual field.
- Windows Chinese API calls are fragile unless the query is sent as true UTF-8 JSON bytes or constructed without console encoding loss.
- The top reason text can still show `0 challenge` for particular top edges even when separate challenge checks found refuting/context evidence for other checked edges. This is honest per-edge reporting, but it may still read too negative to users and should be polished later.

### Residual Risks

- The 2026-04-14 golden case succeeded, but the live source mix still depends on external availability and quota.
- OpenRouter preflight passing does not guarantee every later LLM subcall will succeed under latency, quota, or provider behavior.
- gstack browse is installed but its screenshot command did not produce an artifact in this Windows session; Playwright E2E passed and is the verification source for UI behavior.
- Pro workflow remains documented direction only in this pass; no Pro persistence/export/team/schedule code has been added.

## 2026-04-14 Markdown Brief Challenge Wording Polish

### Task

Polish the OSS Markdown research brief so users do not misread per-edge zero refutation counts as "all evidence chains are unchallenged" or as a hidden scoring bug. Keep the change deterministic and evidence-grounded by using existing edge refutation status, evidence bindings, challenge checks, and source trace data.

### Files Touched

- `retrocause/api/main.py`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- `pytest tests\test_comprehensive.py::test_result_to_v2_builds_copyable_markdown_research_brief -q`
  - Result: passed before the new wording test, confirming the existing source-label and challenge-count behavior still worked.
- `pytest tests\test_comprehensive.py::test_markdown_brief_explains_checked_edges_without_refuting_evidence -q`
  - TDD red result: failed because the Markdown brief did not yet explain a checked edge with no attached refuting evidence.
- `pytest tests\test_comprehensive.py::test_markdown_brief_explains_checked_edges_without_refuting_evidence tests\test_comprehensive.py::test_result_to_v2_builds_copyable_markdown_research_brief -q`
  - Result after implementation: passed.
- `ruff check retrocause\api\main.py tests\test_comprehensive.py`
  - Result: passed.
- `pytest tests\test_comprehensive.py::test_markdown_brief_explains_checked_edges_without_refuting_evidence tests\test_comprehensive.py::test_result_to_v2_builds_copyable_markdown_research_brief tests\test_comprehensive.py::test_product_harness_rewards_useful_evidence_backed_result -q`
  - Result: passed.
- Started local FastAPI on `127.0.0.1:8000` and Next.js on `localhost:3005` for E2E.
  - FastAPI log reported `Uvicorn running on http://127.0.0.1:8000`.
  - Next.js log reported `Ready` on `http://localhost:3005`.
- `npm test`
  - Result: passed.
  - Included frontend lint, frontend build, `ruff check retrocause/`, full pytest, and Playwright E2E script.
  - Pytest result: 214 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result after committing this change: passed as `safe-to-deploy`, 90/100.
  - Non-blocking warnings: the change spans 5 top-level areas because implementation, tests, README, project state, and evidence were intentionally kept in sync; `docs/PROJECT_STATE.md` changed by project documentation-sync rule.

### Behavior Notes

- Top reasons now keep the existing positive count wording when a specific edge has refuting evidence: `Challenge evidence on this edge: N`.
- Top reasons now explain checked edges with no attached refuting evidence as: `No challenge evidence attached to this edge after targeted retrieval`.
- Challenge coverage rows now say `challenge evidence found: N` or `no challenge evidence found`, avoiding ambiguous `0 challenge` wording.
- Evidence source labels in the Markdown brief continue to render as readable labels such as `News`, not internal enum strings such as `EvidenceType.NEWS`.
- This change does not add new causal conclusions. It only translates existing retrieval/refutation status into clearer user-facing report text.

### Residual Risks

- The wording is clearer in English Markdown output, but deeper Chinese localization of generated brief sections remains future work.
- Challenge retrieval is still bounded to selected edges; "no challenge evidence found" means none was attached/found in that targeted retrieval pass, not that no refutation exists anywhere.

## 2026-04-14 In-App Readable Brief Polish

### Task

Make the OSS report output friendlier for product reading: keep Markdown as the portable copy/export format, but render a structured in-app readable brief by default.

### Files Touched

- `frontend/src/app/page.tsx`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- `python scripts\e2e_test.py`
  - TDD red result while shaping the behavior: failed with 604 passed, 2 failed.
  - Missing behavior: no `[data-testid='readable-brief']` structured report and copy action still read like raw Markdown.
- `python scripts\e2e_test.py`
  - Result after implementation: passed.
  - E2E result: 606 passed, 0 failed, 0 skipped.
- `pytest tests\test_comprehensive.py::test_frontend_renders_readable_brief_instead_of_raw_markdown_copy -q`
  - Result after moving the regression into the task-contract `tests/` scope: passed.
- `npm --prefix frontend run lint`
  - Result: passed.
- `npm test`
  - Result: passed.
  - Included frontend lint, frontend build, `ruff check retrocause/`, full pytest, and Playwright E2E script.
  - Pytest result: 215 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result after committing this change: passed as `safe-to-deploy`, 90/100.
  - Non-blocking warnings: the change spans implementation, tests, README, project state, and evidence; `docs/PROJECT_STATE.md` changed by project documentation-sync rule.

### Behavior Notes

- The browser now labels the result card as `Readable brief` / `阅读版简报`.
- The in-app card shows sections for likely explanation, confidence signal, top reasons, what to check, gaps, and evidence coverage.
- The copy button is now `Copy report` / `复制报告`; its title still makes clear that the portable format is Markdown.
- The API still returns `markdown_brief`, preserving OSS developer and integration value.

### Residual Risks

- This pass improves the existing left-panel card rather than building a full long-form report view.
- The readable brief still depends on current `analysis_brief` fields and does not add a new LLM-written narrative.

## 2026-04-14 Live Graph Label Dogfood Polish

### Task

Use the invoked `using-superpowers` and `gstack` flow to dogfood the readable brief and identify what the user actually sees in the browser. Fix the biggest product-readability issue found during the live path.

### Files Touched

- `frontend/src/app/page.tsx`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- gstack preamble via WSL bash
  - Result: gstack preamble ran after correcting shell quoting; WSL default distro is usable, telemetry is off, and the Boil the Lake intro was marked seen.
- Started local FastAPI on `127.0.0.1:8000` and Next.js on `localhost:3005`.
  - Result: API and browser app were reachable.
- OpenRouter provider preflight and live `/api/analyze/v2` golden case for `美国和伊朗在伊斯兰堡谈判结束 未达成协议的原因是什么`
  - Result: `status=ok`, `analysis_mode=live`, `freshness_status=fresh`, `is_demo=false`, 18 evidence items, 5 chains, 3 challenge checks, 7 retrieval trace rows, product harness `ready_for_review`, score 1.0, Markdown brief length 4303, and no `0 challenge` phrase.
- `C:\Users\97504\.claude\skills\gstack\browse\dist\browse.exe goto http://localhost:3005`
  - Result: navigated to the local app with HTTP 200.
- `C:\Users\97504\.claude\skills\gstack\browse\dist\browse.exe text`
  - Result: confirmed the app renders the evidence board, query panel, demo transparency, and evidence filters.
- `C:\Users\97504\.claude\skills\gstack\browse\dist\browse.exe console --errors`
  - Result: no console errors.
- Playwright live UI dogfood using the same local app and OpenRouter key from process environment only
  - Result: readable brief rendered with `关键原因`, `审阅重点`, `证据覆盖`, `复制报告`, live badge, ready-for-review signal, and no `0 challenge` phrase.
  - Screenshot: `logs/gstack-readable-brief-live.png`.
  - Finding: the central causal-map notes still showed generic `市场影响因素` labels for untranslated live nodes, hiding the specific causes users need to inspect.
- `pytest tests\test_comprehensive.py::test_frontend_keeps_specific_live_node_labels tests\test_comprehensive.py::test_frontend_renders_readable_brief_instead_of_raw_markdown_copy -q`
  - Result: passed, 2 tests.
- Playwright UI replay using the saved live response at `logs/alpha4-us-iran-response.json`
  - Result after implementation: graph note titles were `Iran Nuclear Program`, `Negotiation Refusal`, and `No Deal Reached`; `hasGenericMarketImpactFactor=false`, `hasSpecificGraphLabels=true`, readable brief present, no `0 challenge` phrase, and no console errors.
  - Screenshot: `logs/gstack-readable-brief-replay-specific-labels.png`.
- `npm test`
  - First full result after label fix: passed, but frontend lint reported one warning because the removed generic-label fallback left `hasUnlocalizedEnglishLabel` unused.
  - Cleanup: removed the now-unused helper so the UI change does not leave a lint warning behind.
- `npm test`
  - Final result after cleanup: passed.
  - Included frontend lint with no warnings, frontend build, `ruff check retrocause/`, full pytest, and Playwright E2E script.
  - Pytest result: 216 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 90/100.
  - Non-blocking warnings: this task spans 5 top-level areas because implementation, regression test, README, project state, and evidence were intentionally synchronized; `docs/PROJECT_STATE.md` changed by project documentation-sync rule.

### Behavior Notes

- Chinese-mode live graph notes now keep the specific model-provided labels after local phrase substitution instead of replacing remaining English labels with `市场影响因素`.
- This may leave some graph labels partly English in Chinese mode, but it preserves user-visible causal meaning and matches the README's honest known-limits wording.
- Added a regression test to keep the generic-label fallback from returning.

### Residual Risks

- Full Chinese localization of arbitrary model-generated geopolitical labels remains future work.
- Headless clipboard writes can fail in browser automation, so the live dogfood observed `复制失败` after clicking `Copy report`; existing E2E and source behavior still keep the copy action visible, and manual browsers should support the Clipboard API under normal permissions.

## 2026-04-14 Alpha.4 UX Polish And Release Sync

### Task

Execute the next 1/2/3/4 sequence:

1. Sync the live graph label fix into the public OSS release path.
2. Add a reliable `Copy report` fallback when clipboard permissions are blocked.
3. Improve Chinese readability and source transparency for the readable brief.
4. Verify with gstack/tests and publish alpha.4 if the release candidate is ready.

### Files Touched

- `frontend/src/app/page.tsx`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- gstack preamble via WSL bash
  - Result: preamble ran through stdin after an initial PowerShell quoting failure; WSL bash is usable, telemetry is off, and `LAKE_INTRO=yes`.
- `pytest tests\test_comprehensive.py::test_frontend_offers_manual_report_copy_fallback -q`
  - TDD red result: failed because no `data-testid="manual-copy-report"` fallback existed.
- `pytest tests\test_comprehensive.py::test_frontend_offers_manual_report_copy_fallback tests\test_comprehensive.py::test_frontend_renders_readable_brief_instead_of_raw_markdown_copy -q`
  - Result after implementation: passed, 2 tests.
- `pytest tests\test_comprehensive.py::test_frontend_summarizes_source_transparency_in_readable_brief -q`
  - TDD red result: failed because no `data-testid="source-health-summary"` source summary existed in the readable brief.
- `pytest tests\test_comprehensive.py::test_frontend_summarizes_source_transparency_in_readable_brief tests\test_comprehensive.py::test_frontend_offers_manual_report_copy_fallback -q`
  - Result after implementation: passed, 2 tests.
- `pytest tests\test_comprehensive.py::test_frontend_localizes_us_iran_golden_case_labels -q`
  - TDD red result: failed because the frontend localization table did not cover `nuclear program`, `negotiation refusal`, or `no deal reached`.
- `pytest tests\test_comprehensive.py::test_frontend_localizes_us_iran_golden_case_labels tests\test_comprehensive.py::test_frontend_summarizes_source_transparency_in_readable_brief -q`
  - Result after implementation: passed, 2 tests.
- `pytest tests\test_comprehensive.py::test_frontend_offers_manual_report_copy_fallback tests\test_comprehensive.py::test_frontend_summarizes_source_transparency_in_readable_brief tests\test_comprehensive.py::test_frontend_localizes_us_iran_golden_case_labels tests\test_comprehensive.py::test_frontend_keeps_specific_live_node_labels -q`
  - Result: passed, 4 tests.
- Playwright browser replay with saved live response and forced clipboard rejection
  - Result: `Copy report` changed to `复制失败`, `data-testid="manual-copy-report"` became visible, the textarea contained Markdown, `data-testid="source-health-summary"` was visible, source summary showed `AP News, web_search`, `stable=5/7`, `failed=0`, `hits=18`, and there were no console errors.
  - Screenshot: `logs/manual-copy-fallback.png`.
- `npm test`
  - Result: passed.
  - Included frontend lint, frontend build, `ruff check retrocause/`, full pytest, and Playwright E2E script.
  - Pytest result: 219 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 90/100.
  - Non-blocking warnings: this task spans implementation, tests, README, project state, and evidence; `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.
- Release docs sync
  - Updated source `README.md` and `docs/PROJECT_STATE.md` from `v0.1.0-alpha.3` to `v0.1.0-alpha.4` before publishing the public OSS export.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after alpha.4 release docs sync
  - Result: `safe-to-deploy`, 90/100.
  - Non-blocking warnings: broad release-scope documentation/evidence/test/frontend diff and intentional `docs/PROJECT_STATE.md` continuity update.
- Public export sync and validation for `v0.1.0-alpha.4`
  - Synchronized only user-facing OSS release files into `D:\opencode\retrocause-ai-public-20260413`: `README.md`, `frontend/src/app/page.tsx`, `retrocause/api/main.py`, and `tests/test_comprehensive.py`.
  - Secret scan result: no `sk-or-v1-`, `ghp_`, `gho_`, or `GITHUB_PERSONAL_ACCESS_TOKEN` patterns outside ignored cache/build/log folders.
  - `npm --prefix frontend run lint`: passed.
  - `npm --prefix frontend run build`: passed.
  - `ruff check retrocause/`: passed.
  - `pytest tests/ --basetemp=.pytest-tmp`: first failed because `retrocause/api/main.py` had not been synchronized with the newer alpha.4 tests; after syncing it, passed with 219 tests.
  - `python scripts/e2e_test.py` against export backend `127.0.0.1:8002` and export frontend `localhost:3007`: passed with 604/604 E2E checks.
  - Stopped the temporary export backend/frontend processes after E2E.
- Public GitHub publish for `v0.1.0-alpha.4`
  - Fixed local SSH private-key ACLs so Windows OpenSSH could authenticate as `logi-cmd`.
  - Pushed public export commit `beb9499 Polish alpha4 report UX` to `main`.
  - Created and pushed tag `v0.1.0-alpha.4`.
  - Created GitHub prerelease: `https://github.com/logi-cmd/retrocause-ai/releases/tag/v0.1.0-alpha.4`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after release outcome evidence sync
  - Result: `safe-to-deploy`, 95/100.
  - Non-blocking warning: intentional `docs/PROJECT_STATE.md` continuity update.

### Behavior Notes

- If the Clipboard API rejects `Copy report`, the readable brief now opens a manual-copy Markdown textarea and a `Select report text` action.
- The readable brief now includes a source-health summary: checked sources, stable-source count, failed-source count, and hit count.
- The US/Iran golden-case labels now have targeted Chinese replacements for terms such as `nuclear program`, `negotiation refusal`, `no deal reached`, `Iran`, and `United States`.

### Residual Risks

- Manual-copy fallback is intentionally a browser-side UX fallback; it does not replace the one-click clipboard path.
- The Chinese localization table remains targeted phrase substitution, not a full translation layer for arbitrary model-generated labels.

## 2026-04-14 Production Brief Harness Design

### Task

Respond to the product concern that optimizing around a single US/Iran question is not useful for production users. Design the next OSS direction as a general production-output layer for market, policy/geopolitics, and postmortem scenarios.

### Files Touched

- `docs/superpowers/specs/2026-04-14-production-brief-harness-design.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, and the brainstorming skill before writing the design.
- Reviewed recent commits and searched for US/Iran, readable brief, manual copy, and source-health references in the current implementation.
- Spec self-review
  - Result: no `TBD`, `TODO`, or placeholder markers found.
  - Confirmed the spec covers freshness gating, evidence anchoring, OSS/Pro boundary, and single-case regression boundaries.
- `npm test`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and Playwright E2E script.
  - Pytest result: 219 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 95/100.
  - Non-blocking warning: intentional `docs/PROJECT_STATE.md` continuity update.

### Behavior Notes

- No code implementation was performed in this pass.
- The spec defines Production Brief Harness as OSS scope because it is core single-run usefulness.
- Pro remains scoped to hosted, repeatable, collaborative, scheduled, saved, branded, and source-policy workflows.
- The spec explicitly says US/Iran should remain a regression case and should not drive hardcoded product behavior.
- The spec requires freshness gating for latest-information questions and evidence anchoring for every production claim.

### Residual Risks

- This is a design-only checkpoint; implementation still needs a separate plan and tests.
- The existing frontend still contains targeted US/Iran label mappings until the implementation pass replaces them with general scenario/role labeling.

## 2026-04-14 Production Brief Harness Implementation Plan

### Task

After user approval of the Production Brief Harness design, create a task-by-task implementation plan using the `writing-plans` workflow.

### Files Touched

- `docs/superpowers/plans/2026-04-14-production-brief-harness.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, and the `writing-plans` skill before writing the plan.
- Inspected current API, frontend, and test anchors for scenario additions, readable brief rendering, Markdown export, and product harness behavior.
- `Select-String -Path docs\superpowers\plans\2026-04-14-production-brief-harness.md -Pattern "TBD|TODO|implement later|fill in details|Similar to Task|appropriate error handling|Write tests for the above"`
  - Result: no placeholder markers found after self-review cleanup.
- `npm test`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and Playwright E2E script.
  - Pytest result: 219 passed.
  - E2E result: 604 passed, 0 failed, 0 skipped.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 95/100.
  - Non-blocking warning: intentional `docs/PROJECT_STATE.md` continuity update.

### Behavior Notes

- No feature implementation was performed in this pass.
- The plan decomposes the approved spec into TDD tasks with commit checkpoints.
- The plan covers scenario detection, scenario override, production brief sections, production harness gates, freshness and source-risk checks, frontend rendering, Markdown export, single-case product-logic cleanup, docs, tests, and guardrails verification.
- `rg` was unavailable in this Windows session because `rg.exe` returned `Access is denied`; PowerShell `Select-String` was used as the read-only fallback.

### Residual Risks

- This pass creates an implementation plan only; user-visible product behavior is unchanged until the plan is executed.
- The plan intentionally keeps the first implementation inside existing API/frontend files to minimize review scope, so follow-up refactoring may be warranted if the production brief code grows large.

## 2026-04-15 SourceBroker Retrieval Reliability Implementation Plan

### Task

Create the next implementation plan for retrieval reliability after documenting the retrieval/output strategy. The plan must keep the work grounded in user value: reliable latest-information retrieval, visible source limits, cache safety, and usable source trace output for OSS users and future Solo Pro / Team Lite workflows.

### Files Touched

- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `docs/PROJECT_STATE.md`
- `frontend/next.config.ts`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/retrieval-and-output-strategy.md`, `retrocause/evidence_access.py`, `tests/test_evidence_access.py`, `.agent-guardrails/task-contract.json`, and this evidence note before writing the plan.
- Inspected current SourceBroker-like implementation points: query planning, scenario routing, source ordering, cooldown, cache keys, time filtering, and source descriptions.
- Created `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md` with task-by-task implementation steps, named tests, target files, and commit checkpoints.
- `Select-String -Path docs\superpowers\plans\2026-04-15-sourcebroker-plan.md -Pattern "TBD|TODO|implement later|fill in details|Similar to Task|appropriate error handling|Write tests for the above"`
  - Result: no placeholder markers found.
- `npm test`
  - First result: frontend lint/build, `ruff check retrocause/`, and 234 pytest tests passed, then E2E failed because the backend was not running on `127.0.0.1:8000`.
- `cmd /c npm.cmd --prefix frontend run build`
  - Result after failed background job attempts: reproduced `spawn EPERM` during Next `type-checking`.
- Root-cause check:
  - `.next/trace` and `.next/diagnostics/build-diagnostics.json` showed the failure stage was Next type-checking with build worker enabled.
  - `frontend/node_modules/next/dist/build/type-check.js` confirmed type-checking runs through a worker by default.
- `cmd /c npm.cmd --prefix frontend run build` after enabling `experimental.workerThreads` in `frontend/next.config.ts`
  - Result: passed.
- `npm test` after the Next worker-thread fix with the backend running
  - Result: frontend lint/build and ruff passed, then pytest collection failed because the root script resolved `pytest` to global Anaconda Python, which lacked `openai`, `fastapi`, and `streamlit_agraph`.
- `.venv\Scripts\python.exe -m pytest tests\test_evidence_access.py -q`
  - Result: passed, confirming the project virtual environment has the required Python dependencies.
- Kept root `package.json` unchanged to stay inside the current task contract; full verification will run `npm test` with `.venv\Scripts` prepended to `PATH`.
- `cmd /c npm.cmd --prefix frontend run dev -- --port 3005`
  - Result: failed with `spawn EPERM`; Next dev also uses child-process spawning in this Windows environment.
- `cmd /c npm.cmd --prefix frontend run start -- --port 3005`
  - Result: started successfully after a production build and reported `Ready` on `http://localhost:3005`.
- `npm test` with `.venv\Scripts` prepended to `PATH`, API running on `127.0.0.1:8000`, and production frontend running on `localhost:3005`
  - Result: passed.
  - Included frontend lint, frontend build, `.venv` ruff, `.venv` pytest, and E2E smoke tests.
  - Pytest result: 234 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `npx agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: passed as `safe-to-deploy`, 95/100.
  - Non-blocking warnings: state-management continuity warnings because `docs/PROJECT_STATE.md` and evidence were intentionally synchronized.

### Behavior Notes

- No product code behavior changed in this pass.
- The plan deliberately extends the existing `retrocause.evidence_access` boundary before introducing any new run queue or database.
- The plan treats rate limits as a user-facing product state: source-limited, rate-limited, cached, forbidden, timed out, or source error.
- Optional hosted search providers are planned as key-gated adapters, so OSS can still run locally without Tavily or Brave keys.
- Next.js build behavior changed only in build execution mode: type-checking now uses worker threads to avoid Windows `spawn EPERM` in this environment.
- Local verification should use `.venv\Scripts` before global Python on `PATH`, matching how the app is launched locally.

### Residual Risks

- This is a planning checkpoint only; source trace behavior remains unchanged until the plan is executed.
- Tavily and Brave adapter details will need mocked HTTP tests first so CI does not depend on live external accounts.
- The current task contract is older and broad enough to allow docs/plans/evidence updates, but the implementation pass should create or refresh a task contract if the scope changes materially.
- Full `npm test` passes when the local API and production frontend are available for E2E and `.venv\Scripts` is first on `PATH`.

## 2026-04-15 SourceBroker Task 1: Source Profiles And Policy Selection

### Task

Execute Task 1 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: centralize source policy metadata and let the broker include optional hosted search sources without overriding explicit operator source choices.

### Files Touched

- `retrocause/evidence_access.py`
- `tests/test_evidence_access.py`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `retrocause/evidence_access.py`, `tests/test_evidence_access.py`, `.agent-guardrails/task-contract.json`, and this evidence note before implementation.
- `pytest tests\test_evidence_access.py::test_source_profiles_expose_budget_and_storage_policy tests\test_evidence_access.py::test_broker_source_names_can_include_optional_hosted_sources_when_enabled -q`
  - TDD red result: failed because `source_profile` did not exist yet.
- `pytest tests\test_evidence_access.py -q`
  - First result after implementation: 13 passed and 2 failed.
  - Failure 1: older source-description assertion needed the new `cache_policy` field.
  - Failure 2: policy/geopolitics optional hosted source ordering put `tavily` before AP News and Federal Register.
- `pytest tests\test_evidence_access.py -q`
  - Result after fixes: 15 passed.
- `pytest tests\test_evidence_access.py tests\test_api_retrieval_trace.py -q`
  - Result: 17 passed.
- `npm test` with `.venv\Scripts` prepended to `PATH`, API running on `127.0.0.1:8000`, and production frontend running on `localhost:3005`
  - Result: passed.
  - Included frontend lint, frontend build, ruff, pytest, and E2E smoke tests.
  - Pytest result: 236 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `npx agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after committing Task 1
  - Result: passed as `safe-to-deploy`, 90/100.
  - Non-blocking warnings: the task spans implementation, tests, docs, and evidence, and `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.

### Behavior Notes

- Added frozen `SourceProfile` metadata for `ap_news`, `gdelt`, `gdelt_news`, `web`, `federal_register`, `arxiv`, `semantic_scholar`, `tavily`, and `brave`.
- `describe_source_name` now returns `cache_policy` in addition to `source_label`, `source_kind`, and `stability`.
- `broker_source_names` now accepts `optional_sources`.
- Explicit configured source overrides still win unchanged.
- Fresh market/news queries can put optional hosted sources before default discovery sources.
- Policy/geopolitics queries keep AP News and Federal Register first, then optional hosted sources, then GDELT and web.

### Residual Risks

- This task only adds policy metadata and ordering. It does not yet classify rate-limit failures or expose degraded source status in the API/UI.
- Tavily and Brave are profiles only in this task; actual adapters remain later plan tasks.

## 2026-04-15 SourceBroker Task 2: Scoped Retrieval Cache Keys

### Task

Execute Task 2 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: prevent stale or cross-scenario evidence reuse by including source policy, scenario, language, absolute time bucket, normalized scoped query, adapter name, and result count in the process-local search cache key.

### Files Touched

- `retrocause/evidence_access.py`
- `retrocause/collector.py`
- `tests/test_evidence_access.py`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `retrocause/evidence_access.py`, `retrocause/collector.py`, `tests/test_evidence_access.py`, `.agent-guardrails/task-contract.json`, and this evidence note before implementation.
- `pytest tests\test_evidence_access.py::test_access_cache_key_separates_scenario_and_language tests\test_evidence_access.py::test_access_cache_key_reuses_same_absolute_time_bucket -q`
  - TDD red result: failed because `EvidenceAccessLayer.search()` did not accept `scenario`.
- `pytest tests\test_evidence_access.py::test_access_cache_key_separates_scenario_and_language tests\test_evidence_access.py::test_access_cache_key_reuses_same_absolute_time_bucket -q`
  - Result after implementation: 2 passed.
- `pytest tests\test_evidence_access.py -q`
  - Result: 17 passed.
- `pytest tests\test_evidence_access.py tests\test_auto_collect.py -q`
  - Result: 31 passed.
- `ruff check retrocause\evidence_access.py retrocause\collector.py tests\test_evidence_access.py`
  - Result: passed.
- `npm test` with `.venv\Scripts` prepended to `PATH`, API running on `127.0.0.1:8000`, and production frontend running on `localhost:3005`
  - Result: passed.
  - Included frontend lint, frontend build, ruff, pytest, and E2E smoke tests.
  - Pytest result: 238 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `npx agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: passed as `safe-to-deploy`, 90/100.
  - Non-blocking warnings: this task spans implementation, tests, docs, and evidence; `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.

### Behavior Notes

- `EvidenceAccessLayer.search()` now accepts backward-compatible keyword-only `scenario`, `language`, and `source_policy` parameters.
- Search cache entries are isolated by source adapter, source policy, scenario, language, absolute time bucket, normalized scoped query, and max result count.
- Collector live retrieval paths derive scenario and language from `plan_query()` and pass them into search, so market/news, policy/geopolitics, English, Chinese, and relative-date runs do not silently share incompatible cached search results.

### Residual Risks

- This task still uses a process-local in-memory cache. Multi-user hosted cache persistence, per-provider storage rules, and run-level usage ledgers remain future Solo Pro / Team Lite work.
- Source degradation is not classified yet; Task 3 remains needed before users can see rate-limited, forbidden, timeout, and cooldown statuses in retrieval traces.

## 2026-04-15 SourceBroker Task 3: Degraded Source Classification

### Task

Execute Task 3 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: classify upstream source failures and cache/cooldown states into stable retrieval-health statuses that can later be surfaced in the API/UI.

### Files Touched

- `retrocause/evidence_access.py`
- `tests/test_evidence_access.py`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `retrocause/evidence_access.py`, `tests/test_evidence_access.py`, `.agent-guardrails/task-contract.json`, and this evidence note before implementation.
- `pytest tests\test_evidence_access.py::test_access_layer_classifies_rate_limited_sources tests\test_evidence_access.py::test_access_layer_classifies_forbidden_sources tests\test_evidence_access.py::test_access_layer_marks_cooldown_as_source_limited -q`
  - TDD red result: failed because `EvidenceAccessBatch.errors` still contained raw exception class names and `SourceAttempt` had no `status`.
- `pytest tests\test_evidence_access.py::test_access_layer_classifies_rate_limited_sources tests\test_evidence_access.py::test_access_layer_classifies_forbidden_sources tests\test_evidence_access.py::test_access_layer_marks_cooldown_as_source_limited -q`
  - Result after implementation: 3 passed.
- `pytest tests\test_evidence_access.py -q`
  - First result after implementation: 19 passed and 1 failed because an older assertion still expected `ConnectionError` instead of `source_error`.
- `pytest tests\test_evidence_access.py -q`
  - Result after updating the old assertion: 20 passed.
- `ruff check retrocause\evidence_access.py tests\test_evidence_access.py`
  - Result: passed.
- `pytest tests\test_evidence_access.py tests\test_auto_collect.py tests\test_api_retrieval_trace.py -q`
  - Result: 36 passed.
- `npm test` with `.venv\Scripts` prepended to `PATH`, API running on `127.0.0.1:8000`, and production frontend running on `localhost:3005`
  - Result: passed.
  - Included frontend lint, frontend build, ruff, pytest, and E2E smoke tests.
  - Pytest result: 241 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `npx agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: passed as `safe-to-deploy`, 90/100.
  - Non-blocking warnings: this task spans implementation, tests, docs, and evidence; `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.

### Behavior Notes

- `SourceAttempt` now includes `status`, `retry_after_seconds`, `source_label`, `source_kind`, `stability`, and `cache_policy`.
- `classify_source_error()` maps HTTP 429 to `rate_limited`, HTTP 401/403 to `forbidden`, timeout-like failures to `timeout`, and general upstream failures to `source_error`.
- Cooldown skips are now represented as `source_limited` instead of the internal word `cooldown`.
- Cache hits are represented as `cached`, successful source calls as `ok`, and attempts carry source-profile metadata for later API/UI display.
- `EvidenceAccessBatch.errors` now stores stable status categories instead of raw exception class names for classified source failures.

### Residual Risks

- Task 3 only enriches backend attempt metadata. Task 4 still needs to expose these fields in the V2 retrieval trace and Markdown/readable brief output.
- Retry-after parsing handles numeric retry headers and common exception attributes; date-formatted retry headers are not parsed yet.

## 2026-04-15 SourceBroker Task 4: Degraded Source Trace API And Briefs

### Task

Execute Task 4 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: surface degraded source trace metadata in V2 API responses and Markdown/readable brief output so users can see rate-limited, source-limited, cached, and failed sources instead of silent zero-result rows.

### Files Touched

- `retrocause/api/main.py`
- `retrocause/engine.py`
- `tests/test_comprehensive.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `retrocause/api/main.py`, `retrocause/engine.py`, `tests/test_comprehensive.py`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `.agent-guardrails/task-contract.json`, and this evidence note before implementation.
- `pytest tests\test_comprehensive.py::test_retrieval_trace_exposes_degraded_source_metadata -q`
  - TDD red result: failed because `_result_to_v2()` assumed each trace item was a dict and did not handle `SourceAttempt` objects or expose status metadata.
- `pytest tests\test_comprehensive.py::test_retrieval_trace_exposes_degraded_source_metadata -q`
  - Result after implementation: 1 passed.
- `pytest tests\test_comprehensive.py::test_retrieval_trace_exposes_degraded_source_metadata tests\test_api_retrieval_trace.py -q`
  - Result: 3 passed.
- `ruff check retrocause\api\main.py retrocause\engine.py tests\test_comprehensive.py`
  - Result: passed.
- Started local verification services for E2E:
  - FastAPI on `127.0.0.1:8000`.
  - Next production frontend on `127.0.0.1:3005`.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and E2E smoke tests.
  - Pytest result: 242 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 90/100.
  - Blocking errors: 0.
  - Non-blocking warnings: this task spans `.agent-guardrails`, `docs`, `retrocause`, and `tests`, and `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.
- Committed Task 4 as `feat: expose degraded source trace metadata`.

### Behavior Notes

- `RetrievalTraceItemV2` now exposes `status`, `retry_after_seconds`, and `cache_policy` in addition to source label, source kind, stability, query, result count, cache hit, and error.
- `_result_to_v2()` now normalizes both dict trace rows and `SourceAttempt` objects, preserving source-profile metadata while keeping backward-compatible defaults.
- `Engine._compile_result()` now preserves the new `SourceAttempt` fields when compiling live pipeline results.
- Markdown source trace rows now include a visible retrieval-health status such as `rate-limited`, `source-limited`, `cached`, `timeout`, or `source-error`, plus retry-after seconds when available.
- Analysis brief source coverage now includes the count of source attempts and degraded or limited attempts.

### Residual Risks

- This task exposes backend/brief metadata. Frontend-specific bilingual badges and right-panel visual polish remain Task 7.
- Date-formatted `Retry-After` headers are still not parsed; numeric retry seconds are preserved when available.

## 2026-04-15 SourceBroker Task 5: Optional Tavily Adapter

### Task

Execute Task 5 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: add an optional Tavily hosted search adapter that is enabled only when the user provides `TAVILY_API_KEY`, maps Tavily search results into `SearchResult`, and does not make hosted search mandatory for OSS users.

### Files Touched

- `retrocause/sources/tavily.py`
- `retrocause/app/demo_data.py`
- `tests/test_evidence_access.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `retrocause/app/demo_data.py`, `retrocause/evidence_access.py`, `retrocause/sources/`, `tests/test_evidence_access.py`, `.agent-guardrails/task-contract.json`, and this evidence note before implementation.
- `pytest tests\test_evidence_access.py::test_optional_tavily_adapter_requires_api_key tests\test_evidence_access.py::test_tavily_adapter_maps_results_to_search_result -q`
  - TDD red result: failed because `_available_source_classes_from_env`, `_optional_hosted_source_names_from_env`, and `retrocause.sources.tavily` did not exist yet.
- `pytest tests\test_evidence_access.py::test_optional_tavily_adapter_requires_api_key tests\test_evidence_access.py::test_tavily_adapter_maps_results_to_search_result -q`
  - Result after implementation: 2 passed.
- `pytest tests\test_evidence_access.py -q`
  - Result: 22 passed.
- `ruff check retrocause\sources\tavily.py retrocause\app\demo_data.py tests\test_evidence_access.py`
  - Result: passed.
- `pytest tests\test_evidence_access.py tests\test_auto_collect.py -q`
  - Result: 36 passed.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - First result: failed after frontend lint/build, ruff, and 243 pytest tests passed because `TAVILY_API_KEY` was present in the environment and `_select_source_names(None, "geopolitics")` became non-deterministic by including optional Tavily.
- `pytest tests\test_query_routing.py::test_select_source_names_prefers_news_sources_for_geopolitics tests\test_evidence_access.py::test_optional_tavily_adapter_requires_api_key tests\test_evidence_access.py::test_tavily_adapter_maps_results_to_search_result -q`
  - Result after keeping `_select_source_names` deterministic and only adding Tavily in live run registration: 3 passed.
- `ruff check retrocause\sources\tavily.py retrocause\app\demo_data.py tests\test_evidence_access.py`
  - Result after the deterministic helper fix: passed.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and E2E smoke tests.
  - Pytest result: 244 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - First result: `pass-with-concerns`, 75/100, because README/evidence placeholder wording looked like possible secrets.
  - Remediation: removed token-like placeholder examples and the literal bearer-token wording from docs/evidence.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result after remediation: `safe-to-deploy`, 90/100.
  - Blocking errors: 0.
  - Non-blocking warnings: this task spans `.agent-guardrails`, `README.md`, `docs`, `retrocause`, and `tests`, and `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.
- Committed Task 5 as `feat: add optional Tavily retrieval adapter`.

### Behavior Notes

- Added `TavilySourceAdapter`, using `TAVILY_API_KEY` by default or an explicit constructor key in tests.
- The adapter calls Tavily Search with the configured auth header, query, max results, and raw-content inclusion.
- Tavily results now map title, URL, content, raw content, score, and published date into `SearchResult` plus metadata.
- App source registration now includes Tavily only when `TAVILY_API_KEY` is present.
- Broker optional-source routing remains controlled by the existing `broker_source_names(..., optional_sources=...)` path.

### Residual Risks

- Focused tests use mocked HTTP only; no live Tavily account was used.
- Tavily is now available to the live app when a key is present, but frontend-specific source status labels remain later Task 7 work.
- `_select_source_names()` remains deterministic for legacy routing tests; optional hosted sources are added in the live analysis path only.

## 2026-04-15 SourceBroker Task 6: Optional Brave Search Adapter

### Task

Execute Task 6 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: add an optional Brave Search adapter that is enabled only when the user provides `BRAVE_SEARCH_API_KEY`, maps Brave web search results into `SearchResult`, and marks provider metadata with a transient result-storage policy.

### Files Touched

- `retrocause/sources/brave.py`
- `retrocause/app/demo_data.py`
- `tests/test_evidence_access.py`
- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `retrocause/app/demo_data.py`, `retrocause/evidence_access.py`, `retrocause/sources/tavily.py`, `retrocause/sources/base.py`, `tests/test_evidence_access.py`, `.agent-guardrails/task-contract.json`, and this evidence note before implementation.
- Checked official Brave Search API docs for the Web Search endpoint, API-key header, and request parameters.
- `pytest tests\test_evidence_access.py::test_optional_brave_adapter_requires_api_key tests\test_evidence_access.py::test_brave_adapter_marks_transient_cache_policy -q`
  - TDD red result: failed because `_optional_hosted_source_names_from_env()` did not include Brave and `retrocause.sources.brave` did not exist.
- `pytest tests\test_evidence_access.py::test_optional_brave_adapter_requires_api_key tests\test_evidence_access.py::test_brave_adapter_marks_transient_cache_policy -q`
  - Result after implementation: 2 passed.
- `pytest tests\test_evidence_access.py -q`
  - Result: 24 passed.
- `ruff check retrocause\sources\brave.py retrocause\app\demo_data.py tests\test_evidence_access.py`
  - Result: passed.
- `pytest tests\test_evidence_access.py tests\test_auto_collect.py -q`
  - Result: 38 passed.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and E2E smoke tests.
  - Pytest result: 246 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 90/100.
  - Blocking errors: 0.
  - Non-blocking warnings: this task spans `.agent-guardrails`, `README.md`, `docs`, `retrocause`, and `tests`, and `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.
- Committed Task 6 as `feat: add optional Brave retrieval adapter`.

### Behavior Notes

- Added `BraveSearchSourceAdapter`, using `BRAVE_SEARCH_API_KEY` by default or an explicit constructor key in tests.
- The adapter calls Brave Web Search with query and result-count parameters plus the required API-key header.
- Brave web results now map title, URL, description, source domain, and published date when present into `SearchResult`.
- Brave metadata includes `provider=brave`, `content_quality=snippet`, and `cache_policy=transient_results_only`.
- App source registration now includes Brave only when `BRAVE_SEARCH_API_KEY` is present.

### Residual Risks

- Focused tests use mocked HTTP only; no live Brave account was used.
- Brave result metadata is snippet-only in this pass. Full page fetch/extract remains governed by downstream source policy and provider terms.
- Frontend-specific bilingual source status labels remain later Task 7 work.

## 2026-04-15 SourceBroker Task 7: UI Source Degradation Language

### Task

Execute Task 7 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: make degraded source states readable in the browser UI and source-health summary so users can distinguish ready, cached, source-limited, rate-limited, forbidden, timed-out, and source-error rows.

### Files Touched

- `frontend/src/app/page.tsx`
- `tests/test_comprehensive.py`
- `docs/PROJECT_STATE.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `frontend/src/app/page.tsx`, `tests/test_comprehensive.py`, `docs/retrieval-and-output-strategy.md`, `.agent-guardrails/task-contract.json`, and this evidence note before implementation.
- `pytest tests\test_comprehensive.py::test_frontend_surfaces_rate_limited_source_trace_language tests\test_comprehensive.py::test_frontend_localizes_source_trace_status -q`
  - TDD red result: failed because the frontend had no status label helper or localized source status strings.
- `pytest tests\test_comprehensive.py::test_frontend_surfaces_rate_limited_source_trace_language tests\test_comprehensive.py::test_frontend_localizes_source_trace_status -q`
  - Result after implementation: 2 passed.
- `pytest tests\test_comprehensive.py::test_frontend_surfaces_rate_limited_source_trace_language tests\test_comprehensive.py::test_frontend_localizes_source_trace_status tests\test_comprehensive.py::test_frontend_summarizes_source_transparency_in_readable_brief -q`
  - Result: 3 passed.
- `npm --prefix frontend run lint`
  - Result: passed.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and E2E smoke tests.
  - Pytest result: 248 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 95/100.
  - Blocking errors: 0.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 90/100.
  - Blocking errors: 0.
  - Non-blocking warnings: this uncommitted task view spans implementation, tests, docs, and evidence; `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.
- Committed Task 7 as `feat: show degraded source trace status`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after committing Task 7
  - Result: `safe-to-deploy`, 90/100.
  - Blocking errors: 0.
  - Non-blocking warnings: the committed task spans `.agent-guardrails`, `docs`, `frontend`, and `tests`; `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.

### Behavior Notes

- `ApiRetrievalTrace` now includes frontend fields for `status`, `retry_after_seconds`, and `cache_policy`.
- Added a frontend source-status label helper for English and Chinese statuses.
- Right-side source trace rows now render a `source-trace-status` status label and retry-after hint when present.
- The readable brief source-health summary now includes successful, cached, degraded, and reviewability state in addition to checked/stable/hit counts.

### Residual Risks

- This is still source-health metadata, not a causal claim. Users still need to inspect evidence before trusting the explanation.
- Visual QA for the exact badge spacing remains useful after Task 8 full verification, especially on narrow screens.

## 2026-04-15 SourceBroker Task 8: Documentation And Full Verification

### Task

Execute Task 8 from `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`: update bilingual README usage guidance, retrieval strategy docs, project state, and this evidence note for the completed SourceBroker reliability pass, then run full verification.

### Files Touched

- `README.md`
- `docs/PROJECT_STATE.md`
- `docs/retrieval-and-output-strategy.md`
- `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `docs/superpowers/plans/2026-04-15-sourcebroker-plan.md`, `docs/retrieval-and-output-strategy.md`, `.agent-guardrails/task-contract.json`, and this evidence note before editing.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and E2E smoke tests.
  - Pytest result: 248 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: `safe-to-deploy`, 90/100.
  - Blocking errors: 0.
  - Non-blocking warnings: the uncommitted check still included the previous Task 7 implementation commit in the `HEAD~1...HEAD` comparison, plus intentional `docs/PROJECT_STATE.md` continuity updates.
- Committed Task 8 as `docs: document sourcebroker reliability pass`.

### Behavior Notes

- Rewrote README as clean bilingual English/Chinese usage documentation.
- README now explains source-limited, rate-limited, timeout, source-error, and cached states as retrieval-health signals rather than causal evidence.
- README now documents optional user-key Tavily and Brave Search adapters and states that OSS continues to run without those hosted keys.
- README and project docs keep the OSS/Pro boundary focused on local inspectable OSS runs and lightweight Solo Pro / Team Lite hosted reliability.
- Retrieval strategy docs now summarize the implemented SourceBroker reliability pass across source profiles, cache scoping, degraded-source status, API/brief/UI exposure, and optional hosted adapters.

### Residual Risks

- This pass is documentation and verification only; it does not add hosted run orchestration, persistent cache policy enforcement, uploaded evidence, or saved-run history.
- Source trace states help users understand retrieval health, but users still need to inspect evidence before acting on a causal explanation.

## 2026-04-15 SourceBroker Dogfood: Three Production Scenarios

### Task

Dogfood the completed SourceBroker reliability pass across one market, one policy/geopolitics, and one postmortem question using the OpenRouter DeepSeek V3 live path. The goal was to check whether the product output exposes reviewability, evidence count, source trace status, and next actions clearly enough for a user.

### Files Touched

- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `start.py`, `scripts/e2e_test.py`, `retrocause/api/main.py`, `.agent-guardrails/task-contract.json`, and this evidence note before updating docs.
- Ran provider preflight through the FastAPI TestClient with OpenRouter `deepseek/deepseek-chat-v3-0324`.
  - Result: `ok`, `can_run_analysis=True`.
- Ran `/api/analyze/v2` live dogfood for `Why did Bitcoin move today?` with `scenario_override=market`.
  - Result: HTTP 200, `analysis_mode=live`, `freshness_status=recent`, scenario `market`.
  - Output: 3 chains, 4 evidence items, 18 retrieval trace rows, all trace statuses `ok`.
  - Harness: `product_harness.status=ready_for_review`, score 1.0; `production_harness.status=ready_for_brief`, score 1.0.
  - Markdown brief length: 5749 characters.
- Ran `/api/analyze/v2` live dogfood for `Why did the United States and Iran fail to reach an agreement after the Islamabad talks?` with `scenario_override=policy`.
  - Result: HTTP 200, `analysis_mode=live`, `freshness_status=fresh`, scenario `policy_geopolitics`.
  - Output: 8 chains, 13 evidence items, 5 retrieval trace rows, all trace statuses `ok`.
  - Harness: `product_harness.status=ready_for_review`, score 1.0; `production_harness.status=ready_for_brief`, score 1.0.
  - Markdown brief length: 6579 characters.
- Ran `/api/analyze/v2` live dogfood for `Why did a SaaS product launch fail to convert trial users into paid customers?` with `scenario_override=postmortem`.
  - Result: HTTP 200, `analysis_mode=live`, `freshness_status=fresh`, scenario `postmortem`.
  - Output: 6 chains, 13 evidence items, 5 retrieval trace rows, all trace statuses `ok`.
  - Harness: `product_harness.status=ready_for_review`, score 1.0; `production_harness.status=ready_for_brief`, score 1.0.
  - Markdown brief length: 6130 characters.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and E2E smoke tests.
  - Pytest result: 248 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.

### Behavior Notes

- The happy-path SourceBroker output is usable across all three production scenarios: the user gets live mode, evidence counts, source trace rows, top reasons, Markdown brief, and reviewable harness status.
- The dogfood did not naturally trigger rate-limited, source-limited, timeout, forbidden, or source-error states. All observed trace rows were `ok`.
- The policy and postmortem runs emitted query-planning fallback logs when search-query decomposition returned invalid structured output, but the fallback still produced successful live results.

### Residual Risks

- This dogfood validates the normal live path, not the degraded-source UX under real provider failure.
- A follow-up degraded-source drill should intentionally simulate 429, forbidden, timeout, and cooldown states through existing mocked adapters or a small test harness so the user-facing bad-path output can be inspected without waiting for real providers to fail.
- The market run returned `freshness_status=recent` rather than `fresh`, which is acceptable for review but should be highlighted to users before any trade or investment use.

## 2026-04-15 SourceBroker Degraded-Source Drill

### Task

Add a deterministic degraded-source drill regression so the bad path is checked without waiting for real providers to fail. The drill verifies that a single reviewable output can expose rate-limited, forbidden, timed-out, source-error, source-limited, and cached trace rows.

### Files Touched

- `tests/test_comprehensive.py`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`

### Commands Run

- Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `README.md`, `pyproject.toml`, `tests/test_comprehensive.py`, `retrocause/api/main.py`, `.agent-guardrails/task-contract.json`, and this evidence note before editing.
- `pytest tests\test_comprehensive.py::test_degraded_source_drill_surfaces_all_limited_states_for_review -q`
  - Result: passed.
  - The existing SourceBroker output already surfaced all tested degraded statuses in analysis source coverage and Markdown source trace.
- `npm test` with `.venv\Scripts` prepended to `PATH`
  - Result: passed.
  - Included frontend lint/build, `ruff check retrocause/`, full pytest, and E2E smoke tests.
  - Pytest result: 249 passed.
  - E2E result: 572 passed, 0 failed, 1 skipped.
  - The skipped item was the optional Playwright full workflow because Playwright was not installed in `.venv`.
- Committed the drill as `test: add degraded source drill`.
- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"` after committing the drill
  - Result: `safe-to-deploy`, 95/100.
  - Blocking errors: 0.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed by the project documentation-sync rule.

### Behavior Notes

- Added `test_degraded_source_drill_surfaces_all_limited_states_for_review`.
- The drill builds a representative V2 result with `rate_limited`, `forbidden`, `timeout`, `source_error`, `source_limited`, and `cached` retrieval trace rows.
- The test asserts the analysis brief says `6 source attempt(s), 5 degraded or limited`.
- The test asserts Markdown source trace includes `status: rate-limited`, `status: forbidden`, `status: timeout`, `status: source-error`, `status: source-limited`, `status: cached`, `retry after 30s`, and `cache policy: transient_results_only`.

### Residual Risks

- This is deterministic API/brief regression coverage, not browser visual dogfood.
- The next useful UX check is to render a degraded trace in the browser and inspect whether the right-side status labels, colors, and retry-after copy are obvious enough for a first-time user.
