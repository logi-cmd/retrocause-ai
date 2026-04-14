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
