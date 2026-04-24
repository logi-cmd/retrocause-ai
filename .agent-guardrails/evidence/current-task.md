# Current Task Evidence

## Task

Bring the OSS RetroCause build to an honestly documented stable-deliverable local alpha state by re-validating first-run setup from a fresh copy, confirming the current workspace still passes the full release-quality test gate, and syncing public docs to match that verified state.

## Scope

- `README.md`
- `docs/PROJECT_STATE.md`
- `.agent-guardrails/evidence/current-task.md`
- verification only in the current workspace and a fresh local copy under `D:\opencode\retrocause-clean-check2`

## What Changed

- Updated `README.md` to say the current build has passed a fresh-copy install plus the full root `npm test` workflow on Windows, and to label that status as a stable-deliverable local alpha rather than a stable `v0.1.0` release.
- Updated `docs/PROJECT_STATE.md` to record the clean-clone validation result, close the first-run local-delivery gap, and move the next-step focus to provider-backed Chinese finance validation, maintainability cleanup, and defining the non-alpha release gate.
- Replaced this evidence note with a clean UTF-8 version because the prior file had broken encoding that no longer reflected the current task.

## Commands Run

### Current workspace verification

- `npm test`
  - Result: passed.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `325 collected, 324 passed, 1 skipped`.
  - E2E result: `617 passed, 0 failed, 0 skipped`.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: passed, `95/100 (safe-to-deploy)`.
  - Non-blocking warning: one large resource file is present in the current diff. This warning comes from the existing working tree and was not introduced by this docs-only status-calibration pass.

### Fresh-copy first-run validation

A first attempt used a broad Windows directory copy into `D:\opencode\retrocause-clean-check`, but that copy was incomplete and did not include `frontend/package.json`, so it was not treated as a valid first-run result.

A second fresh copy was created at `D:\opencode\retrocause-clean-check2` by copying all tracked files from `git ls-files` plus the current needed untracked files under `retrocause/`, `scripts/`, `tests/`, `frontend/`, `docs/`, and `.agent-guardrails/`.

- `python -m pip install -e ".[dev]"`
  - Result: passed in `D:\opencode\retrocause-clean-check2`.

- `npm install`
  - Result: passed in `D:\opencode\retrocause-clean-check2`.

- `npm --prefix frontend install`
  - Result: passed in `D:\opencode\retrocause-clean-check2`.

- `npm test`
  - Result: passed in `D:\opencode\retrocause-clean-check2`.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `325 collected, 324 passed, 1 skipped`.
  - E2E result: `617 passed, 0 failed, 0 skipped`.

## Delivery Conclusion

The current OSS build now meets the bar for a **stable-deliverable local alpha**:

- the working tree passes the full release-quality local verification gate,
- a fresh local copy can be installed with the documented README steps,
- that fresh local copy also passes the full root `npm test` workflow, and
- docs now match the verified state.

This does **not** mean the project is already a stable non-alpha `v0.1.0` release.

## Remaining Risks And Follow-up

- A provider-backed live Chinese finance run with real `OFOXAI_API_KEY` plus search keys still needs to be recorded after the latest fast-path and provider-stability changes.
- The exact quality bar for promoting the OSS build from stable local alpha delivery to a non-alpha `v0.1.0` release is now defined in `docs/oss-release-gate.md`, but several gates in that document are still open.
- Frontend and backend maintainability cleanup remains open, especially the remaining homepage orchestration in `frontend/src/app/page.tsx`, legacy canvas retirement, and the residual route orchestration in `retrocause/api/main.py`.

## 2026-04-24 Follow-up

Release-state audit on 2026-04-24 found that the repository only has alpha tags/releases (`v0.1.0-alpha.1` through `v0.1.0-alpha.5`) and does not yet have a public `v0.1.0` tag or GitHub release. Some in-progress local doc edits had drifted into claiming `v0.1.0` was already shipped, so the docs were corrected and an explicit release-gate doc was added instead.

### Commands Run

- `git tag --list "v0.1.0*"`
  - Result: only `v0.1.0-alpha.1` through `v0.1.0-alpha.5` exist locally.

- `gh release list --repo logi-cmd/retrocause-ai`
  - Result: only alpha prereleases exist publicly; latest is `RetroCause v0.1.0-alpha.5`.

- `gh repo view logi-cmd/retrocause-ai --json defaultBranchRef,url`
  - Result: repository default branch is `main`.

- `git log --oneline --decorate --tags -10`
  - Result: latest release tag in history is `v0.1.0-alpha.5`; no `v0.1.0` tag is present.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test"`
  - Result: passed again on 2026-04-24, `95/100 (safe-to-deploy)`.
  - Non-blocking warning: the existing large README screenshot remains the only warning in this diff.

### Doc Sync From This Follow-up

- `README.md`
  - Corrected the public wording back to "stable-deliverable local alpha" and linked to the new release-gate doc.

- `docs/PROJECT_STATE.md`
  - Corrected the contradictory local-`v0.1.0` wording, kept the verified local-alpha status, and pointed next-step release work toward the explicit gate.

- `docs/INDEX.md`
  - Added the new release-gate doc to the "Start Here" section.

- `docs/oss-release-gate.md`
  - New source-of-truth doc defining the difference between stable local alpha and non-alpha `v0.1.0`, plus the exact mandatory gates that must pass before a non-alpha release.

### Updated Remaining Risks

- The exact quality bar for promoting the OSS build from stable local alpha delivery to a non-alpha `v0.1.0` release is now defined in `docs/oss-release-gate.md`, but the provider-backed live validation gate and dedicated non-alpha manual smoke gate are still open.

## 2026-04-24 UI Localization And Brief-Usability Follow-up

The current user-reported regression had two parts:

1. some Chinese text in the current UI/report path was still mojibake because the frontend brief-localization helper contained broken replacement strings
2. the visible "production brief" surface was too summary-only, which made the result harder to use in an actual review or operational follow-up

### Files Updated

- `frontend/src/app/page.tsx`
- `frontend/src/lib/production-brief-panel.tsx`
- `retrocause/api/production_brief.py`
- `tests/test_comprehensive.py`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Replaced the broken Chinese brief-localization replacement strings in `frontend/src/app/page.tsx` with clean Chinese text and expanded the replacement coverage for common analysis-brief / markdown-brief / production-brief phrases.
- Localized uncertainty-report summary and dominant uncertainty type rendering in the current homepage flow so Chinese mode no longer leaves those sections mostly English.
- Expanded the production-brief panel from a compact summary card into a more usable structured review surface:
  - each item now shows both a title and a fuller summary
  - the panel now exposes next verification steps
  - the panel now exposes current limits
- Improved `retrocause/api/production_brief.py` so production-brief driver items include the first supporting-evidence excerpt instead of only reporting edge strength and evidence count.
- Added regression coverage for:
  - clean brief-localization strings in the frontend source
  - evidence-excerpt production-brief content
  - visible next-step / limit sections in the production-brief panel

### Commands Run

- `python -m pytest tests\test_comprehensive.py -q -k "brief_localization_strings_are_clean or market_production_brief_uses_evidence_excerpt_and_next_steps or frontend_production_brief_panel_surfaces_next_steps_and_limits or frontend_page_has_no_known_mojibake_strings or market_production_brief_has_expected_sections" --basetemp=.tmp-tests\pytest`
  - Result: passed (`5 passed, 134 deselected`).

- `npm test`
  - Result: passed.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `328 collected, 327 passed, 1 skipped`.
  - E2E result: `617 passed, 0 failed, 0 skipped`.

### Risk / Tradeoff Notes

- Security: no auth flow, secrets, or permission handling changed. No keys were added or echoed. This was a frontend/reporting and brief-generation pass only.
- Dependencies: no new packages, lockfile changes, or version upgrades were introduced.
- Performance: the UI now renders more production-brief content and the backend includes one short supporting-evidence excerpt per production driver. This is a small payload/rendering increase, but it stays bounded to a few items and does not add new network calls.
- Understanding: the main tradeoff is that we kept the existing brief/production-brief pipeline and made it more useful instead of inventing a parallel "full report" abstraction. That keeps the user-visible flow coherent and easier to maintain.
- Continuity: reused the existing `localizeBriefText` path, the existing production-brief payload, and the existing `ProductionBriefPanel` instead of introducing a new report subsystem.

### Remaining Risks

- Source evidence excerpts may still remain in their original source language. This is intentional for evidence fidelity; the surrounding report structure should now be clean Chinese in Chinese mode, but quoted evidence text itself is not machine-translated in this pass.
- The provider-backed Chinese finance live-validation gate in `docs/oss-release-gate.md` is still open and remains the next highest-value OSS stability check.

## 2026-04-24 OSS Remote-Push Security Cleanup

Before pushing the current OSS branch, a tracked-scripts audit found that several local diagnostic scripts still hardcoded an OpenRouter API key. Those scripts are not part of the main app path, but because they are tracked files they still count as a real repository secret leak and had to be cleaned before any remote push.

### Files Updated

- `scripts/_sse_e2e.py`
- `scripts/_test_api_path.py`
- `scripts/_test_llm.py`
- `scripts/_test_mh370.py`
- `scripts/_test_sse_mh370.py`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Replaced the hardcoded OpenRouter API key in each tracked helper script with environment-variable lookup.
- Standardized those scripts to accept either `OPENROUTER_API_KEY` or `RETROCAUSE_OPENROUTER_KEY`, then fail fast with a clear message if neither is set.
- Kept the scripts otherwise intact so local debugging behavior stays familiar for future maintenance.

### Commands Run

- `git grep -n "sk-or-v1-" -- .`
  - Result: no tracked files contain a hardcoded `sk-or-v1-...` secret after the cleanup.

- `python - <<'PY' ... compile(...) ... PY`
  - Result: all five updated helper scripts compile successfully after the key-loading change.

- `npm test`
  - Result: passed after the cleanup.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `328 collected, 327 passed, 1 skipped`.
  - E2E result: `617 passed, 0 failed, 0 skipped`.

### Risk / Tradeoff Notes

- Security: the current branch head no longer ships a tracked hardcoded OpenRouter key. If that key was ever pushed in earlier history outside the current branch head, it should still be treated as exposed and rotated outside this repository task.
- Behavior: these scripts now require an environment variable instead of silently carrying a baked-in credential. That is intentional and is the safer default for any future local operator.
- Scope: no application runtime path, public API behavior, or frontend rendering changed in this cleanup.

## 2026-04-24 Pro Rust Kickoff

After pushing the current OSS stabilization branch, Pro work was started on a separate branch: `codex/pro-rust-kg-foundation`. The goal of this kickoff was not to ship hosted Pro inside the OSS stack; it was to establish the product/design context, create a bounded Rust workspace, and prove the first graph-first UI direction.

### Files Updated

- `.impeccable.md`
- `docs/INDEX.md`
- `docs/pro-prd.md`
- `docs/pro-rust-architecture.md`
- `pro/Cargo.toml`
- `pro/apps/api/Cargo.toml`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/Cargo.toml`
- `pro/apps/web/src/main.rs`
- `pro/crates/domain/Cargo.toml`
- `pro/crates/domain/src/lib.rs`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added an explicit Pro design-context file in `.impeccable.md` so future design work starts from a real audience, workflow, and tone instead of generic dashboard defaults.
- Added `docs/pro-prd.md` to define the first Solo Pro workflow, graph-first product shape, and success metrics.
- Added `docs/pro-rust-architecture.md` to lock the kickoff stack choice and the separation boundary between OSS and the Rust rewrite.
- Added a new Rust workspace under `pro/` with:
  - `apps/api`: an Axum API shell with `/`, `/healthz`, and `/api/graph/seed`
  - `apps/web`: an Axum + Maud server-rendered knowledge-graph workspace shell
  - `crates/domain`: shared Pro graph/run types and canonical seed data used by both API and web
- Updated `docs/INDEX.md` so the new Pro PRD and Rust architecture note are discoverable from the main documentation map.

### Commands Run

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - Coverage from this kickoff:
    - API health payload test
    - shared domain seed-integrity test
    - web graph-wire/path rendering test
    - web shell section-rendering test

- Pro API smoke:
  - Started with `cargo run --manifest-path pro/apps/api/Cargo.toml`
  - Result: `GET http://127.0.0.1:8787/healthz` returned HTTP `200`

- Pro web smoke:
  - Started with `cargo run --manifest-path pro/apps/web/Cargo.toml`
  - Result: `GET http://127.0.0.1:3007/` returned HTTP `200`
  - The returned HTML contained `Knowledge graph review desk`

- `agent-guardrails check --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with concerns, `80/100`
  - Non-blocking warnings:
    - this kickoff still spans 5 top-level areas (`.agent-guardrails`, `.gitignore`, `.impeccable.md`, `docs`, `pro`)
    - the kickoff introduces new Rust Cargo manifests under `pro/`
    - the kickoff includes the first Pro API interface shell in `pro/apps/api/src/main.rs`

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: same pass-with-concerns outcome, `80/100`
  - No blocking errors remained after narrowing the task contract to the actual Pro kickoff files.

### Risk / Tradeoff Notes

- Security: no auth, secrets, or credential storage were added in this kickoff. The Pro workspace uses only static seed data and local ports for now.
- Dependencies: this adds a new Rust dependency surface under `pro/` only (`axum`, `tokio`, `serde`, `serde_json`, `maud`). No Python or Node dependency graph changed for OSS.
- Performance: the kickoff web shell is server-rendered HTML instead of a WASM-heavy client graph. That keeps compile and startup cost low while the product shape is still fluid.
- Understanding: the main deliberate tradeoff is choosing a shared `domain` crate immediately, because both the API and the web shell need the same run/graph model even at kickoff scale. Queueing, persistence, BYOK handling, and exports are intentionally deferred.
- Continuity: OSS runtime paths remain untouched. The intentional continuity break is architectural: Pro now starts under `pro/` as a separate Rust workspace instead of extending the Python/FastAPI + Next.js app toward hosted responsibilities.

## Security / Dependency / Performance / Understanding / Continuity Notes

- Security: no secrets were added, copied into docs, or echoed in verification output. The fresh-copy validation used the documented no-secret local setup path.
- Dependencies: no new packages or version changes were introduced by this task. The fresh-copy install only reinstalled the existing declared dependencies.
- Performance: no runtime logic changed. The only performance-relevant result is that the full local verification gate remains executable from a fresh copy on Windows.
- Understanding: the docs now distinguish three states clearly: stable-deliverable local alpha, not-yet-stable `v0.1.0`, and not-a-hosted-service.
- Continuity: reused the existing README, project-state, and guardrails evidence pattern instead of adding a new release-status document.

## 2026-04-24 Keyless OSS Boundary And Pro Graph Redesign

This task responds to the product boundary correction that OSS should not expose user/provider keys and that OpenRouter is deprecated for RetroCause. It also refreshes the Pro Rust web shell so the only carried-forward frontend requirement is a knowledge-graph-first workspace, not the earlier OSS evidence-board/rail layout.

### Files Updated

- `README.md`
- `.env.example`
- `.impeccable.md`
- `STATE.md`
- `docs/INDEX.md`
- `docs/PROJECT_STATE.md`
- `docs/codebase-audit.md`
- `docs/manual-smoke-test.md`
- `docs/oss-release-gate.md`
- `docs/pro-prd.md`
- `docs/pro-rust-architecture.md`
- `docs/pro-workflow-spec.md`
- `docs/retrieval-and-output-strategy.md`
- `frontend/src/app/page.tsx`
- `frontend/src/lib/i18n/en.ts`
- `frontend/src/lib/i18n/zh.ts`
- `pro/apps/web/src/main.rs`
- `retrocause/api/*` keyless response/finalization/preflight helpers
- `retrocause/app/demo_data.py`
- `retrocause/evidence_access.py`
- `retrocause/config.py`
- `retrocause/llm.py`
- `retrocause/sources/tavily.py` removed
- `retrocause/sources/brave.py` removed
- `scripts/live_stability_probe.py`
- `scripts/e2e_test.py`
- `tests/test_comprehensive.py`
- `tests/test_evidence_access.py`
- `tests/test_live_stability_probe.py`

### What Changed

- Removed active OpenRouter support from the OSS provider catalog and docs.
- Removed OSS browser/API request fields for model keys and hosted-search keys.
- Changed `/api/analyze`, `/api/analyze/v2`, and `/api/analyze/v2/stream` to return the keyless local/demo analysis path instead of trying hosted model execution.
- Kept provider/source preflight endpoints only as compatibility surfaces: provider preflight now reports `oss_keyless`, and source preflight reports the built-in keyless source path.
- Removed tracked Tavily and Brave source-adapter files from the active OSS source tree and removed environment-key registration from the OSS source factory.
- Updated README, project state, release gate, manual smoke notes, and retrieval strategy so they describe the keyless OSS boundary and point hosted model/search execution to the future Rust Pro line.
- Reworked the Pro Rust web shell into a full-screen graph-field command room with overlay/dock surfaces around the graph rather than left/right rails inherited from the OSS page.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed to include OSS docs/runtime/tests/scripts plus the Pro Rust web shell.

- `python -m pytest tests\test_evidence_access.py -q --basetemp=.tmp-tests\pytest-evidence`
  - Result: `27 passed`.

- `python -m pytest tests\test_comprehensive.py tests\test_live_stability_probe.py -q --basetemp=.tmp-tests\pytest-keyless`
  - Result: `138 passed`.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - Coverage includes Pro API health, domain seed integrity, graph-wire path rendering, and Pro web graph-first section rendering.

- `npm test`
  - Result: passed.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `321 collected`, all passed.
  - E2E result: `609 passed`, `1 skipped`, `0 failed`.

- Pro web smoke
  - Started with `cargo run --manifest-path pro/apps/web/Cargo.toml`.
  - Result: `GET http://127.0.0.1:3007/` returned HTTP `200`.
  - The returned HTML contained `Causal graph command room` and `Knowledge graph operating field`.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test" --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with concerns, `50/100`, no blocking errors.
  - Non-blocking warnings were expected for this correction because it intentionally updates the OSS public boundary, API schemas/routes, docs, tests, `.env.example`, scripts, and the Pro graph shell in one branch-level handoff.
  - The sensitive-file warning is for `.env.example`, which now removes provider secret placeholders rather than adding them.

### Risk / Tradeoff Notes

- Security: the active OSS browser/API no longer accepts user model/search keys, `.env.example` no longer advertises provider secrets, OpenRouter is not in the active catalog, and Tavily/Brave key-reading adapters were removed from the active source tree. The low-level `LLMClient` still has a non-OSS integration constructor parameter because the project uses the OpenAI SDK internally, but it is no longer wired to the OSS browser/API surface or environment-key fallback.
- Dependencies: no new Python, Node, or Rust dependencies were added. Removing hosted-search adapter files reduces the active OSS source surface.
- Performance: keyless OSS requests now avoid hosted model/search calls from the browser/API path, making local analysis deterministic and less latency-sensitive. The Pro web redesign remains server-rendered HTML from the existing Rust stack.
- Understanding: the main deliberate tradeoff is product clarity over live-provider flexibility. OSS is now the local inspectable alpha; hosted credentials, quotas, live search, and provider recovery belong in Pro.
- Continuity: saved runs, uploaded evidence, source traces, challenge coverage, and the evidence board stay in OSS. The intentional continuity break is the Pro frontend: it keeps the knowledge graph as the core, but does not inherit the OSS evidence-board layout.
- Remaining risk: old historical decision logs and archived implementation plans may still mention prior provider experiments. Current README/project-state/manual-smoke/runtime paths have been synchronized to the keyless boundary.

## 2026-04-24 Main Landing And Pro Entry

This task lands the already-tested keyless OSS and Pro Rust graph foundation branch onto `main`. The remote `main` branch and the active work branch had unrelated Git histories, so this landing intentionally uses an explicit merge commit rather than rewriting remote history.

### Files / Scope

- `main` was merged with `codex/pro-rust-kg-foundation`.
- The merge preserves the current project tree from the tested Pro foundation branch.
- The guardrails task contract was refreshed for this landing because `HEAD~1...HEAD` on `main` now represents the whole unrelated-history import rather than the smaller feature-branch diff.

### Commands Run

- `git fetch origin`
  - Result: remote refs refreshed.

- `git switch main`
  - Result: switched to local `main`, tracking `origin/main`.

- `git pull --ff-only origin main`
  - Result: `main` was already up to date with `origin/main`.

- `git merge --allow-unrelated-histories --no-ff codex/pro-rust-kg-foundation -m "Merge Pro Rust foundation into main"`
  - Result: unrelated-history merge started.
  - Add/add conflicts were resolved by choosing the already-tested `codex/pro-rust-kg-foundation` versions for conflicted files.
  - Only mechanical whitespace cleanup was applied before committing.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - Pro API health, Pro domain seed integrity, and Pro graph web rendering tests passed.

- `npm test`
  - Result: passed.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `321 collected`, all passed.
  - E2E result: `609 passed`, `1 skipped`, `0 failed`.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml" --commands-run "npm test"`
  - Result: passed with warnings, `90/100 (safe-to-deploy)`.
  - Tool quirk: this multi-command invocation only counted the final `npm test` command and incorrectly reported the required `cargo test --manifest-path pro/Cargo.toml` as missing even though it had already been run and passed.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with warnings, `90/100 (safe-to-deploy)`.
  - No blocking errors and no missing required command remained.
  - Non-blocking warnings:
    - `docs/PROJECT_STATE.md` changed; this is intentional because the Pro implementation state and next step changed.
    - `pro/apps/api/src/main.rs` changed the public Pro API by adding `POST /api/runs`; this is intentional and is the central behavior change of this slice.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test" --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - First result: blocked by stale feature-branch contract scope, not by tests.
  - The stale contract did not include the full unrelated-history import surface now visible from `main`.

- `agent-guardrails plan ...`
  - Result: task contract refreshed for the `main` landing scope.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "npm test" --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Final result after refreshing the landing contract: passed with high-risk warnings, `0/100`, no blocking errors.
  - The remaining 27 warnings are expected for this one-time unrelated-history landing: the diff imports 132 files onto `main`, spans many top-level areas, includes large screenshot/log fixtures, and changes public/API/config surfaces already validated on the feature branch.

### Risk / Tradeoff Notes

- Security: no provider secret is added. The active OSS browser/API remains keyless, and `.env.example` removes provider secret placeholders rather than introducing credentials.
- Dependencies: the merge brings the already-tested Pro Rust workspace and existing Node/Python dependency metadata onto `main`; no extra dependency change was added during the landing itself.
- Performance: the landing itself changes no runtime path beyond bringing the previously tested branch onto `main`. Pro remains a small server-rendered Rust graph shell at this stage.
- Understanding: the main tradeoff is Git-history cleanliness versus remote safety. Because the histories were unrelated, this keeps a visible merge commit and avoids force-pushing `main`.
- Continuity: the landing intentionally keeps the tested branch content as the source of truth. The next work should branch from `main` into a fresh Pro implementation branch.

## 2026-04-24 Pro Product Core Slice 1

This task starts active Pro implementation on `codex/pro-rust-product-core`. It keeps OSS runtime paths untouched and expands only the Rust Pro workspace plus synchronized docs.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `README.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Replaced the simple Pro seed type with a richer shared `ProRun` payload that includes:
  - run summary fields
  - graph nodes and edges
  - evidence anchors
  - challenge checks
  - source health
  - usage ledger entries
  - verification steps
- Added shared validation for graph references to ensure nodes and edges only point at known evidence and challenge ids.
- Added Pro API endpoints:
  - `GET /api/runs`
  - `GET /api/runs/{run_id}`
  - `GET /api/runs/{run_id}/graph`
  - retained `GET /api/graph/seed` as a compatibility seed endpoint
- Updated the Pro web shell to render the richer run payload, including evidence anchors, challenge counts, source health, and operator summary while keeping the graph as the primary surface.
- Updated current project state and Pro architecture docs to say Pro implementation has started under `pro/`, while OSS remains keyless and stable.

### Commands Run

- `agent-guardrails plan ...`
  - Result: contract refreshed for a Pro-only product-core slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed after formatting.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `4 passed`.
  - Domain tests: `5 passed`.
  - Web tests: `2 passed`.

- `npm test`
  - Result: passed.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `321 collected`, all passed.
  - E2E result: `609 passed`, `1 skipped`, `0 failed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed after moving the `IntoResponse` trait import into the API test module.

- Pro HTTP smoke:
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8791`.
  - Started `retrocause-pro-web.exe` on `127.0.0.1:3017`.
  - `GET /api/runs` returned `1` run.
  - `GET /api/runs/run_semiconductor_controls_001/graph` returned `6` graph nodes and `5` graph edges.
  - `GET /` on the Pro web shell returned HTTP `200` and included `Evidence anchors`.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with concerns, `85/100`, no blocking errors.
  - Non-blocking warnings:
    - this slice spans 4 top-level areas because code and docs/evidence were intentionally synchronized
    - `docs/PROJECT_STATE.md` changed because the project moved from Pro planning to Pro implementation
    - `pro/apps/api/src/main.rs` changed public API shape by adding run list/detail/graph endpoints

### Risk / Tradeoff Notes

- Security: no auth, secrets, provider credentials, BYOK fields, or hosted calls were added. This is still a static local Pro seed and API/web shell.
- Dependencies: no dependency or lockfile changes were added in this slice.
- Performance: payloads remain static and server-rendered, so runtime cost is minimal. The richer JSON payload is deliberately small and bounded while the domain shape is still forming.
- Understanding: the main tradeoff is keeping static sample data while defining the real Pro payload boundary. This avoids premature persistence or provider routing before the graph/review contract is stable.
- Continuity: this reuses the existing Rust workspace, Axum API, Maud web shell, and shared domain crate. The intentional continuity break remains the Pro frontend direction: it stays graph-first and does not inherit the OSS evidence-board layout.

## 2026-04-24 Pro Product Core Slice 2

This task continues active Pro implementation on `codex/pro-rust-product-core`. It keeps OSS runtime paths untouched and adds the first real run-creation path inside the Rust Pro API.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Converted Pro run/domain payload string fields from static string references to owned `String` values so user-created runs can be represented safely without leaking memory or pretending dynamic text is static data.
- Added `CreateRunRequest` and `create_run_from_request`, producing a bounded queued run shell with user-question evidence, challenge checks, source status, usage ledger entries, and verification steps.
- Added process-local in-memory API state for Pro runs.
- Added `POST /api/runs`; `GET /api/runs`, `GET /api/runs/{run_id}`, and `GET /api/runs/{run_id}/graph` now read from the same in-memory store.
- Updated the Pro web shell for the owned payload type while keeping it graph-first and still rendering the canonical sample run.
- Updated project-state and Pro architecture docs to mark in-memory run creation as implemented and move the next Pro step to web/API create-run interaction plus provider/search quota ownership types.

### Commands Run

- `agent-guardrails plan ...`
  - Result: contract refreshed for the Pro in-memory run-creation slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because newly edited Rust files needed standard `rustfmt` line wrapping.

- `cargo test --manifest-path pro/Cargo.toml`
  - First result: passed.
  - API tests: `6 passed`.
  - Domain tests: `7 passed`.
  - Web tests: `2 passed`.

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: applied standard Rust formatting.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed after formatting.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed after formatting.
  - API tests: `6 passed`.
  - Domain tests: `7 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- `git diff --check`
  - Result: passed. Git only reported normal Windows CRLF normalization warnings for touched text files.

- Pro API HTTP smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8792`.
  - `GET /healthz` returned `ok`.
  - `POST /api/runs` created `run_local_000001`.
  - `GET /api/runs/{run_id}` returned the submitted smoke-test question.
  - `GET /api/runs/{run_id}/graph` returned `3` graph nodes.
  - `GET /api/runs` returned `2` runs, proving the sample and created run share the same in-memory store.

- `npm test`
  - Result: passed.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `321 collected`, all passed.
  - E2E result: `609 passed`, `1 skipped`, `0 failed`.

### Risk / Tradeoff Notes

- Security: no auth, secrets, provider credentials, BYOK fields, or hosted calls were added. Created runs live only in the local Pro API process memory.
- Dependencies: no new packages, lockfile changes, or version upgrades were introduced.
- Performance: reads and writes use a small `Arc<RwLock<HashMap<...>>>` in-process store. This is suitable for an alpha product-core slice, but it is not a multi-user hosted storage model.
- Understanding: the main tradeoff is taking the small owned-string migration now so later provider/search/web-created runs do not need unsafe static lifetimes or memory leaks.
- Continuity: the slice reuses the existing Rust workspace, Axum routes, Maud web shell, and shared domain crate. It intentionally avoids touching OSS runtime paths.

### Remaining Risks

- Runs are not durable and disappear when the Pro API process exits.
- The Pro web shell still renders the canonical sample directly instead of creating runs through the API.
- Provider/search routing, cooldown buckets, workspace quotas, auth, and persistence remain future Pro work.

## 2026-04-24 Pro Product Core Slice 3

This task wires the graph-first Pro web shell to the Rust API create/list/detail/graph flow. It keeps OSS runtime paths untouched and does not add live provider/search credentials.

### Files Updated

- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added minimal local CORS handling to the Pro API so the separate Pro web port can call `GET /api/runs`, `POST /api/runs`, `GET /api/runs/{run_id}`, and `GET /api/runs/{run_id}/graph` during local alpha development.
- Added a Pro web create-run console with a question textarea, optional title, saved-run picker, and status text.
- Added browser-side run loading that calls the Pro API detail and graph endpoints, then refreshes the graph cards, wires, evidence anchors, source pulse, challenge checks, focus queue, and payload drawer from the API payload.
- Kept the web shell graph-first and avoided inheriting the OSS evidence-board layout.
- Updated Pro project-state and architecture docs to mark web/API create-run interaction as implemented and move the next step to provider/search quota ownership and durable run storage.

### Commands Run

- `agent-guardrails plan ...`
  - Result: contract refreshed for the Pro web/API wiring slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because the edited Rust files needed standard `rustfmt` line wrapping.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed after adding the web/API wiring.
  - API tests: `7 passed`.
  - Domain tests: `7 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Final result: passed after applying `rustfmt`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Pro browser smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8793`.
  - Started `retrocause-pro-web.exe` on `127.0.0.1:3018` with `PRO_API_BASE=http://127.0.0.1:8793`.
  - Opened the Pro web shell with Playwright/Chromium.
  - Submitted the create-run form.
  - Result: page displayed title `Browser-created smoke run`, graph updated to `3` created-run nodes, and status showed `Loaded run_local_000001`.

- `npm test`
  - Result: passed.
  - Included frontend lint/build, `python -m ruff check retrocause/`, full pytest, and browser E2E.
  - Pytest result: `321 collected`, all passed.
  - E2E result: `609 passed`, `1 skipped`, `0 failed`.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The state doc was intentionally synchronized with the implemented Pro web/API create-run flow and next-step queue.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally changes the local Pro API surface by adding local CORS and enabling `POST /api/runs` consumption from the browser shell; it is not an OSS API change and remains keyless/no-auth local alpha plumbing.

### Risk / Tradeoff Notes

- Security: no auth, secrets, provider credentials, BYOK fields, or hosted calls were added. The CORS headers are permissive local-alpha plumbing for a keyless/no-auth local API and should be replaced before any hosted deployment.
- Dependencies: no new packages, lockfile changes, or version upgrades were introduced.
- Performance: browser-side DOM refresh is bounded by the small Pro run payload and makes only list/detail/graph API calls. This is appropriate for the current alpha shell but not the final high-interaction graph client.
- Understanding: the main tradeoff is using a small server-rendered page plus vanilla browser script to prove the run loop now, rather than introducing a full Rust client/hydration stack before persistence and provider routing are defined.
- Continuity: this reuses the existing Axum API, Maud web shell, shared domain payload, and in-memory store. OSS runtime paths remain untouched.

### Remaining Risks

- Runs are still process-local and disappear when the Pro API exits.
- The API has no auth/tenant boundary yet.
- The CORS behavior is not production-ready.
- Provider/search routing, quota ownership enforcement, cooldown buckets, persistence, and richer graph interaction remain future Pro work.

## 2026-04-24 Pro Product Core Slice 4

This task adds the first provider/search quota ownership and cooldown status model for Pro. It keeps the implementation keyless and static: no credentials, no live provider calls, no billing path, and no hosted execution are introduced.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added shared Rust domain payloads for provider/search quota status, including quota owner, credential policy, readiness, and cooldown state.
- Added `provider_status_snapshot()` with static local-alpha lanes for managed Pro model quota, workspace search quota, BYOK-later search, uploaded-evidence-only input, and a market-search cooldown bucket.
- Added keyless `GET /api/provider-status` in the Pro API.
- Added a quota-routing panel in the graph-first Pro web shell and browser-side refresh from `/api/provider-status`.
- Updated Pro docs so the next implementation step moves from modeling quota ownership to graph interaction state, durable run storage, and real routing behind the new payloads.

### Commands Run

- `agent-guardrails plan ...`
  - Result: contract refreshed for the provider/search quota ownership slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because new Rust code needed standard `rustfmt` wrapping.

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: applied standard formatting.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `8 passed`.
  - Domain tests: `8 passed`.
  - Web tests: `2 passed`.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Final result: passed.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API provider-status smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8794`.
  - Called `GET /api/provider-status`.
  - Result: `mode=local_alpha_no_credentials`, `entries=5`, `market_search_cooldown.retry_after_seconds=900`.

- Pro browser quota-panel smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8795`.
  - Started `retrocause-pro-web.exe` on `127.0.0.1:3019` with `PRO_API_BASE=http://127.0.0.1:8795`.
  - Opened the Pro web shell with Playwright/Chromium.
  - Result: quota panel rendered `5` provider/search rows and displayed `local alpha no credentials`.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The project state was intentionally synchronized to mark provider/search quota ownership modeling as done and move the next-step queue forward.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds the keyless local `GET /api/provider-status` endpoint for Pro; it does not change the OSS API surface or introduce provider credentials.

### Risk / Tradeoff Notes

- Security: no auth, secrets, API keys, credential input fields, provider credentials, BYOK storage, or hosted calls were added. BYOK is represented only as a future ownership policy label.
- Dependencies: no new packages, lockfile changes, or version upgrades were introduced.
- Performance: the provider-status snapshot is static and tiny. The browser makes one extra GET request and falls back to the embedded static payload if the API is offline.
- Understanding: this deliberately models ownership/cooldown semantics before building any executor, so future provider routing can inherit explicit quota labels instead of burying rate-limit behavior in adapters.
- Continuity: this reuses the existing shared domain crate, Axum API pattern, Maud web shell, and local-alpha API/web split. OSS runtime paths remain untouched.

### Remaining Risks

- The provider-status payload is static; it does not enforce real quota, cooldown, tenant, or billing rules yet.
- There is still no auth/tenant boundary, persistent run store, credential vault, provider executor, or queue.
- The browser panel is an inspectable status surface, not the final provider-management UX.

## 2026-04-24 Pro Product Core Slice 5

This task adds the first browser-local graph interaction state for the Pro web shell. It keeps state in the page only and does not add persistence, provider calls, credentials, or OSS runtime changes.

### Files Updated

- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Made graph nodes selectable with `data-node-id`, button semantics, keyboard activation, and a stable selected-node class.
- Added a graph inspector that shows the selected node's kind, confidence, summary, evidence links, and challenge links.
- Added browser-local `activeNodeId` handling so the inspector follows node clicks and resets safely when a newly loaded run does not contain the old selected node.
- Adjusted desktop graph spacing after browser smoke found the create-run panel intercepting clicks on a graph node.
- Updated Pro docs so graph interaction state is marked as implemented and the next step moves to durable run storage, provider/search routing, and deeper graph review.

### Commands Run

- `agent-guardrails plan ...`
  - Result: contract refreshed for the graph interaction slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `8 passed`.
  - Domain tests: `8 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro browser interaction smoke
  - First result: failed because the create-run textarea intercepted pointer events on the second graph node.
  - Fix: narrowed the question panel and moved the graph viewport lower to preserve node clickability.
  - Final result: passed after layout adjustment.
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8796`.
  - Started `retrocause-pro-web.exe` on `127.0.0.1:3020` with `PRO_API_BASE=http://127.0.0.1:8796`.
  - Opened the Pro web shell with Playwright/Chromium, clicked the second graph node, and verified inspector title changed from `Control scope tightened` to `Customer pause` with exactly one selected node.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `95/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The state doc was intentionally synchronized to mark graph node selection/inspector state as implemented and to move the next-step queue forward.

### Risk / Tradeoff Notes

- Security: no auth, secrets, API keys, credential fields, provider calls, or stored user data were added. The selected node state is browser-local only.
- Dependencies: no new packages, lockfile changes, or version upgrades were introduced.
- Performance: node selection re-renders the small graph node layer and inspector only; this is fine for the current static alpha graph, but a larger future graph should use incremental updates or a dedicated client graph runtime.
- Understanding: the tradeoff is intentionally lightweight browser-local interaction instead of introducing a full graph-client framework before persistence and run-store boundaries exist.
- Continuity: this reuses the existing Maud web shell, embedded payload, and vanilla browser script. OSS runtime paths remain untouched.

### Remaining Risks

- Selection state is not persisted and does not synchronize across tabs or runs.
- The inspector is read-only and only shows node-level evidence/challenge links; edge-level inspection and richer review workflows remain future work.
- The current layout is still an alpha shell and will need more visual QA as the graph grows.

## 2026-04-24 Pro Product Core Slice 6

This task replaces the Pro API's direct process-local `HashMap` storage with the first local durable run-store boundary. It adds a small file-backed Rust crate and keeps all storage local, keyless, and alpha-scoped.

### Files Updated

- `pro/Cargo.toml`
- `pro/Cargo.lock`
- `pro/apps/api/Cargo.toml`
- `pro/apps/api/src/main.rs`
- `pro/crates/domain/src/lib.rs`
- `pro/crates/run-store/Cargo.toml`
- `pro/crates/run-store/src/lib.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `retrocause-pro-run-store`, a local JSON file-backed run-store crate.
- Added `FileRunStore` with `list_summaries`, `get_run`, and `create_run` methods.
- Added default local storage at `.retrocause/pro_runs.json`, with `RETROCAUSE_PRO_RUN_STORE_PATH` override.
- Changed Pro API routes to call the run-store boundary instead of owning direct `HashMap`, `RwLock`, and sequence state.
- Derived `Deserialize` for Pro domain payloads so run records can be serialized and restored from disk.
- Updated Pro docs so the current storage story is local-file-backed alpha persistence, not hosted storage.

### Commands Run

- `agent-guardrails plan ...`
  - Result: contract refreshed for the durable run-store boundary slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because new Rust code needed standard `rustfmt` wrapping.

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: applied standard formatting.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `8 passed`.
  - Domain tests: `8 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API restart persistence smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8797` with a temporary `RETROCAUSE_PRO_RUN_STORE_PATH`.
  - Created a run titled `Durable smoke`.
  - Stopped and restarted the API process with the same store path.
  - Loaded the created run by id.
  - Result: `created=run_local_000001; loaded=Durable smoke; storeExists=True`.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Final result: passed.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `75/100 (pass-with-concerns)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The project state was intentionally synchronized to mark local JSON run-store persistence as implemented and to move the next-step queue forward.
  - Non-blocking warning: `pro/crates/run-store/Cargo.toml` and `pro/crates/run-store/src/lib.rs` are state/storage-related files. This is intentional: the task creates the first run-store boundary and moves run state out of API-owned `HashMap` storage.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface/behavior-changing file. This slice preserves the same run endpoints but changes their storage behavior so created runs survive API restarts through the local run-store file.
  - Non-blocking warning: `pro/Cargo.toml`, `pro/apps/api/Cargo.toml`, and `pro/crates/run-store/Cargo.toml` are config changes. This is intentional and scoped to adding the new workspace crate plus API dependency; there is no package publishing or deployment change.
  - Non-blocking warning: change size is larger than earlier slices. The size comes from adding one crate, deriving deserialization for existing domain payloads, and updating docs/evidence in the same storage-boundary slice.

### Risk / Tradeoff Notes

- Security: no auth, secrets, API keys, credential fields, provider calls, or hosted execution were added. The JSON run store is local alpha storage and is not a secure document vault.
- Dependencies: no external dependency versions were added; `serde_json` was already a workspace dependency and is now used by the new run-store crate. `pro/Cargo.lock` changed because the new crate joined the workspace.
- Performance: the store writes the small JSON file on create. This is acceptable for the alpha run-store boundary, but it is not suitable for high-concurrency hosted use.
- Understanding: the tradeoff is taking a simple durable boundary now instead of jumping straight to Postgres. API routes stop owning storage details, so a future database implementation can replace the crate without reshaping the route layer.
- Continuity: this reuses the existing Pro domain payload and Axum route patterns. OSS runtime paths remain untouched.

### Remaining Risks

- The JSON file store is local-only, single-process oriented, and not crash-atomic.
- There is still no tenant boundary, auth, ACL, encryption, migration layer, or hosted database.
- Future hosted Pro should move this boundary to Postgres and keep JSON only as a local/dev fallback.

## 2026-04-24 Pro Product Core Slice 7

This task adds the first provider/search routing skeleton for Pro. It produces inspectable routing preview plans from the existing keyless provider-status/quota payload, without executing provider calls.

### Files Updated

- `pro/Cargo.toml`
- `pro/Cargo.lock`
- `pro/apps/api/Cargo.toml`
- `pro/apps/api/src/main.rs`
- `pro/crates/provider-routing/Cargo.toml`
- `pro/crates/provider-routing/src/lib.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `retrocause-pro-provider-routing`, a small routing-boundary crate.
- Added `RoutingPreviewRequest` and `RoutingPreviewPlan` with scenario, source policy, lane decisions, cooldown hints, selected lane, and warnings.
- Added preview-only routing behavior that never allows execution and never calls live providers.
- Added `GET /api/provider-route/preview` as a hint endpoint and `POST /api/provider-route/preview` for local routing preview requests.
- Updated Pro docs so provider/search routing preview is marked as implemented, while real execution remains future work.

### Commands Run

- `agent-guardrails plan ...`
  - Result: contract refreshed for the provider/search routing skeleton slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because new Rust code needed standard `rustfmt` wrapping.

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: applied standard formatting.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `10 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API routing-preview smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8798` with a temporary local run-store path.
  - Called `POST /api/provider-route/preview` with a market-style query.
  - Result: `mode=preview_only; execution=False; selected=uploaded_evidence_lane; steps=5; warnings=2`.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Final result: passed.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked the API/provider-routing diff for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added code in the routing/API diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `85/100 (pass-with-concerns)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The project state was intentionally synchronized to mark routing preview as implemented and to move the next-step queue forward.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET/POST /api/provider-route/preview`; it does not change the OSS API or execute provider calls.
  - Non-blocking warning: `pro/Cargo.toml`, `pro/apps/api/Cargo.toml`, and `pro/crates/provider-routing/Cargo.toml` are config changes. This is intentional and scoped to adding the new workspace crate plus API dependency; there is no package publishing or deployment change.

### Risk / Tradeoff Notes

- Security: no auth, secrets, API keys, credential fields, provider calls, queue workers, billing, or hosted execution were added. The endpoint returns routing preview metadata only.
- Dependencies: no external dependency versions were added; the new provider-routing crate uses existing workspace dependencies. `pro/Cargo.lock` changed because the new crate joined the workspace.
- Performance: routing preview is in-memory and bounded by the five static provider-status lanes. It adds no network calls.
- Understanding: the tradeoff is modeling routing decisions and warnings before implementation of any executor, so future provider adapters can share transparent lane semantics instead of hiding routing logic.
- Continuity: this reuses the existing provider-status payload, Axum route style, and Pro workspace crate pattern. OSS runtime paths remain untouched.

### Remaining Risks

- The route preview does not execute, enqueue, bill, or enforce real provider quotas.
- There is still no tenant/auth boundary, provider credential vault, queue, cooldown persistence, or live search/model adapter.
- The web shell does not yet render route-preview plans; this slice exposes the API and shared routing vocabulary first.

## 2026-04-24 Pro Product Core Slice 8

This task adds the first queued execution boundary behind the Pro provider-routing preview. It stays local and preview-only: no provider calls, credentials, billing, auth, tenant enforcement, worker execution, or OSS runtime changes were added.

### Files Updated

- `pro/Cargo.toml`
- `pro/Cargo.lock`
- `pro/apps/api/Cargo.toml`
- `pro/apps/api/src/main.rs`
- `pro/crates/queue/Cargo.toml`
- `pro/crates/queue/src/lib.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `retrocause-pro-queue`, a small in-memory queue-boundary crate.
- Added `ExecutionQueue`, `ExecutionJob`, `ExecutionJobSummary`, and `ExecutionJobStatus::PreviewOnly`.
- Queue jobs are created from `RoutingPreviewRequest`, reuse the provider-routing preview plan, and explicitly keep `execution_allowed=false`.
- Added Pro API endpoints:
  - `POST /api/execution-jobs`
  - `GET /api/execution-jobs`
  - `GET /api/execution-jobs/{job_id}`
- Updated Pro docs so the queue boundary is documented as process-local preview state, not durable hosted execution.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for the queued execution boundary slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because `pro/crates/queue/src/lib.rs` needed standard `rustfmt` wrapping.

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: applied standard formatting.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Final result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `13 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Queue tests: `4 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API execution-job smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8799` with a temporary local run-store path.
  - Called `POST /api/execution-jobs`, `GET /api/execution-jobs`, and `GET /api/execution-jobs/{job_id}`.
  - Result: `job=job_local_000000; status=preview_only; execution=False; selected=uploaded_evidence_lane; listed=1`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added Pro code lines.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `85/100 (pass-with-concerns)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The project state was intentionally synchronized to mark the preview-only queue boundary as implemented and move the next-step focus to showing queue status in the Pro web shell.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET/POST /api/execution-jobs` and `GET /api/execution-jobs/{job_id}` endpoints; it does not change OSS APIs or execute provider calls.
  - Non-blocking warning: `pro/Cargo.toml`, `pro/apps/api/Cargo.toml`, and `pro/crates/queue/Cargo.toml` are config changes. This is intentional and scoped to adding the new local workspace crate plus API dependency; there is no package publishing, deployment, credential, or billing change.

### Risk / Tradeoff Notes

- Security: no auth, secrets, API keys, credential fields, provider calls, billing hooks, tenant permissions, or sensitive-data storage were added. The queue is a local preview boundary only.
- Dependencies: no new external crate versions were added. `pro/Cargo.lock` changed only because the local `retrocause-pro-queue` workspace crate joined the Pro workspace and the API depends on it.
- Performance: queue operations are in-memory `RwLock` reads/writes over small local job vectors. This is fine for local alpha preview state, but it is not a hosted queue implementation.
- Understanding: the main tradeoff is creating the queue state boundary now while deliberately avoiding workers. API routes no longer need to couple route-plan creation directly to eventual execution state, but the implementation remains small and inspectable.
- Continuity: reused `RoutingPreviewRequest`, `RoutingPreviewPlan`, existing Axum route style, and the Pro workspace crate pattern. OSS runtime paths remain untouched.

### Remaining Risks

- Queue jobs are process-local and disappear when the Pro API exits.
- There is still no Redis/Postgres-backed queue, worker process, tenant/auth boundary, credential vault, live provider executor, or quota enforcement.
- The graph-first Pro web shell does not yet render execution-job status; this is the next intended UI slice.

## 2026-04-24 Pro Product Core Slice 9

This task renders preview-only execution job status in the graph-first Pro web shell. It consumes the existing local execution-job API and keeps the behavior keyless: no provider calls, credentials, billing, auth, workers, persistence, or OSS runtime changes were added.

### Files Updated

- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added an `Execution queue` panel to the Rust Pro web shell.
- Added a `Queue preview job` button that posts the current run question to `POST /api/execution-jobs`.
- Added browser-side refresh from `GET /api/execution-jobs`.
- Rendered queue job id, query, preview-only status, selected lane, and explicit `execution off` state.
- Updated Pro docs so the queue status is now a visible web-shell capability, not just an API boundary.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for the queue-status web slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `13 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Queue tests: `4 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro browser queue-status smoke
  - First readiness attempt failed because PowerShell `Invoke-WebRequest` reported `Object reference not set to an instance of an object` while the web process was actually alive. This was treated as an invalid readiness probe, not as a passing result.
  - Retried with API health readiness plus Playwright page navigation.
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8802` and `retrocause-pro-web.exe` on `127.0.0.1:3023`.
  - Clicked `#queue-preview-button`.
  - Result: browser showed `job_local_000000`, `preview only / uploaded_evidence_lane`, and `execution off`; status text showed `Queued job_local_000000; provider execution remains disabled.`

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro web/doc diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added lines.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `95/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The project state was intentionally synchronized to mark graph-review focus as implemented and move the next-step focus to worker/executor contract planning.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `95/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The project state was intentionally synchronized to mark queue status as visible in the Pro web shell and move the next-step focus to graph review interaction plus the first worker/executor contract.

### Risk / Tradeoff Notes

- Security: no auth, secrets, provider credentials, key input fields, billing hooks, worker execution, or sensitive-data storage were added. The web action sends only the visible run question to the local Pro API.
- Dependencies: no new crates, packages, lockfile changes, or version upgrades were introduced in this slice.
- Performance: the browser now makes one small `GET /api/execution-jobs` on load and one small `POST /api/execution-jobs` when the operator clicks the button. Rendering is bounded to the four newest jobs in the panel.
- Understanding: the tradeoff is keeping the queue UI deliberately small and explicit instead of designing a full job dashboard before workers exist. It makes the current local boundary visible without implying real provider execution.
- Continuity: reused the existing Maud panel pattern, vanilla `fetchJson` browser helper, local API base, and queue endpoint from the prior slice. OSS runtime paths remain untouched.

### Remaining Risks

- Queue jobs are still process-local and disappear when the Pro API exits.
- The web shell lists queue state but does not yet stream job progress, render route-step detail, or link a job back into a completed run.
- There is still no durable worker/executor contract, tenant/auth boundary, credential vault, quota enforcement, or live provider adapter.

## 2026-04-24 Pro Product Core Slice 10

This task deepens browser-local graph review interactions in the Rust Pro web shell. Inspector evidence/challenge links now focus corresponding review items in the workspace. No backend APIs, credentials, provider calls, auth, billing, workers, persistence, or OSS runtime changes were added.

### Files Updated

- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Converted inspector evidence and challenge entries into focus buttons.
- Added `data-evidence-id`, `data-challenge-id`, and `data-review-*` hooks for browser-local review focus.
- Added `focusReviewItem()` in the web shell script to highlight the matching evidence chip or challenge row and update a visible focus status line.
- Added focused styling for evidence/challenge items.
- Updated Pro docs so graph review focus is recorded as part of the current web-shell capability.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for the graph-review focus slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `13 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Queue tests: `4 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro browser graph-review focus smoke
  - Started `retrocause-pro-web.exe` on `127.0.0.1:3024`.
  - Clicked the first inspector evidence link and verified `.evidence-chip.is-focused`.
  - Clicked the first inspector challenge link and verified `#challenge-strip span.is-focused`.
  - Result: focused evidence was `Official export-control language`; focused challenge was `needs primary source: Does the rule actually cover the affected SKUs?`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro web/doc diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added lines.

### Risk / Tradeoff Notes

- Security: no auth, secrets, credential fields, provider calls, billing hooks, sensitive-data storage, or backend surfaces changed. This is browser-local UI state only.
- Dependencies: no new crates, packages, lockfile changes, or version upgrades were introduced.
- Performance: focus uses a small DOM query over currently rendered evidence/challenge items. It is acceptable for the current alpha graph shell; larger future graphs should introduce scoped indexes or a richer graph client runtime.
- Understanding: the tradeoff is using simple DOM focus state rather than introducing a review workflow model before the run/executor contract exists.
- Continuity: reused the existing inspector, evidence dock, challenge strip, and vanilla browser script. OSS runtime paths remain untouched.

### Remaining Risks

- Focus state is browser-local and not persisted across runs, reloads, or tabs.
- Only currently rendered evidence items can be focused; if future docks virtualize or paginate evidence, focus should scroll/load the target explicitly.
- Edge-level review, multi-select, and persisted review decisions remain future work.

## 2026-04-24 Pro Product Core Slice 11

This task defines the first worker/executor contract behind preview-only queue jobs. It adds a non-executing work-order payload derived from queued routing-preview jobs and exposes it through the local Pro API. No provider credentials, provider calls, auth, billing, worker process, persistence, or OSS runtime changes were added.

### Files Updated

- `pro/crates/queue/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `ExecutionWorkOrder` and `ExecutionWorkOrderMode::PreviewOnly`.
- Added `ExecutionJob::work_order()` and `ExecutionQueue::get_work_order()`.
- Work orders include job id, workspace id, query, selected lane, route steps, routing warnings, and safeguards.
- Safeguards explicitly include:
  - `provider_execution_disabled`
  - `credential_access_forbidden`
  - `billing_disabled`
  - `worker_not_started`
- Added `GET /api/execution-jobs/{job_id}/work-order`.
- Updated Pro docs so the work-order contract is documented as non-executing preview infrastructure.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for the executor-contract slice.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because `pro/crates/queue/src/lib.rs` needed standard `rustfmt` import wrapping.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `14 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Queue tests: `5 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: applied standard formatting.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Final result: passed.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API work-order smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8803` with a temporary local run-store path.
  - Created a preview execution job, then called `GET /api/execution-jobs/{job_id}/work-order`.
  - Result: `job=job_local_000000; mode=preview_only; execution=False; steps=5; safeguard=True; selected=uploaded_evidence_lane`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro/doc diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added lines.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `95/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark route-step visibility as implemented and move the next Pro focus to hosted worker lifecycle/store/adapter planning.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. The state doc was intentionally synchronized to mark the non-executing work-order contract as implemented and move the next-step focus to route-step visibility and hosted worker lifecycle planning.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/execution-jobs/{job_id}/work-order`; it does not change OSS APIs or execute provider calls.

### Risk / Tradeoff Notes

- Security: no auth, secrets, credential fields, provider calls, billing hooks, worker execution, or sensitive-data storage were added. Work-order safeguards explicitly preserve the no-execution boundary.
- Dependencies: no new crates, packages, lockfile changes, or version upgrades were introduced.
- Performance: work-order generation clones the small route plan already stored on the in-memory job. This is fine for preview-alpha state; durable hosted execution should generate work orders from persisted job records.
- Understanding: the tradeoff is defining the worker-facing contract before creating a worker. This keeps future executor work honest about safeguards and route-step inputs without pretending live execution exists.
- Continuity: reused `ExecutionJob`, `RoutingPreviewPlan`, existing queue crate, and Axum route style. OSS runtime paths remain untouched.

### Remaining Risks

- Work orders are read-only preview payloads; there is still no worker process or execution lifecycle.
- Work orders disappear with the process-local queue.
- Future hosted Pro still needs tenant/auth checks, durable job storage, quota enforcement, credential vault integration, cooldown persistence, worker retries, and live provider adapters.

## Pro Product Core Slice 12 - Route-Step Visibility In Web Queue

### Scope

This task makes queued preview jobs inspectable in the graph-first Pro web shell. The web app now fetches the existing non-executing work-order endpoint and renders the selected lane, route steps, routing warnings, and safeguards. No provider credentials, provider calls, auth, billing, worker process, queue persistence, backend API changes, or OSS runtime changes were added.

### Files Updated

- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added an execution work-order detail area to the Pro web shell's execution queue panel.
- Added an `Inspect route` action for queued preview jobs.
- `Queue preview job` now refreshes the job list and auto-loads the created job's work order.
- The work-order detail view renders:
  - job id, mode, query, and selected lane
  - route step decision/readiness/quota owner/action/reason
  - routing warnings
  - safeguards such as `provider_execution_disabled` and `credential_access_forbidden`
- Kept the desktop execution panel internally scrollable so route details do not cover the evidence dock.
- Updated Pro docs and project state so the next focus moves to hosted worker lifecycle, durable store migration, and provider adapter contract planning.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for route-step web visibility.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `14 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Queue tests: `5 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro browser route-detail smoke
  - First attempt used the wrong API health URL (`/api/health`); corrected to the actual Pro API health endpoint `/healthz`.
  - Second attempt proved the page rendered the work order, then failed because the smoke expected `Route steps` while CSS uppercased the visible label to `ROUTE STEPS`.
  - Final result: passed.
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8804` and `retrocause-pro-web.exe` on `127.0.0.1:3025` with a temporary local run-store path.
  - Clicked `#queue-preview-button`.
  - Verified the detail panel loaded `job_local_000000`, `uploaded_evidence_lane`, route steps, `provider_execution_disabled`, and `credential_access_forbidden`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro/doc diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added lines.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `85/100 (pass-with-concerns)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the storage-boundary contract as implemented and move the next Pro focus to adapter contract/dry-run work.
  - Non-blocking warning: `pro/crates/run-store/src/lib.rs` changed as a state-related module. This was intentional because the run-store crate owns the current local store boundary and now owns the no-connection hosted storage migration contract.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/storage-plan`; it does not change OSS APIs, open database/Redis connections, accept credentials, or execute provider calls.

### Risk / Tradeoff Notes

- Security: no auth, secrets, credential fields, provider calls, billing hooks, worker execution, or sensitive-data storage were added. The UI exposes safeguards from the existing work-order payload so the no-execution boundary is visible.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: each manual/auto inspection fetches one small work-order JSON payload and renders a short route list. This is fine for preview-alpha state; hosted Pro should paginate or virtualize only if route plans become large.
- Understanding: the tradeoff is making the worker contract visible before any worker exists. This improves reviewability while preserving the hard disabled-execution boundary.
- Continuity: reused the existing queue panel, `fetchJson` helper, work-order endpoint, and source/queue card styling. OSS runtime paths remain untouched.

### Remaining Risks

- Work-order inspection is browser-local UI over an in-memory preview queue; jobs disappear when the API process restarts.
- There is still no worker lifecycle, retry/failure state machine, auth/tenant enforcement, billing, credential vault, or live provider adapter.
- Future hosted Pro needs durable queue/storage design before this preview UI can become an operational console.

## Pro Product Core Slice 13 - Hosted Worker Lifecycle Contract

### Scope

This task adds the first non-executing hosted worker lifecycle/failure-state contract for the Pro Rust product core. The queue crate now owns the lifecycle vocabulary, the API exposes it through a keyless read endpoint, and the graph-first web shell renders a compact lifecycle/failure panel. No provider credentials, live provider calls, auth, billing, real worker process, queue persistence, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/queue/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `ExecutionLifecycleSpec`, `ExecutionLifecycleStage`, `ExecutionFailureState`, and `ExecutionLifecycleMode`.
- Added `execution_lifecycle_spec()` with planned hosted-worker stages: accepted, routed, waiting for quota, waiting for worker, executing provider calls, normalizing evidence, synthesizing graph, awaiting review, and completed.
- Added planned failure states such as `credential_unavailable`, `provider_rate_limited`, `provider_timeout`, `partial_results_only`, `worker_interrupted`, and `cancelled`.
- Added transition guards that keep future credentials behind vault-owned workers and keep route handlers away from raw provider secrets.
- Added `GET /api/execution-lifecycle`.
- Added a Pro web lifecycle panel that renders visible worker stages and failure states while showing execution off.
- Updated Pro docs and project state so the next focus moves to hosted storage migration and adapter dry-run design.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for hosted worker lifecycle/failure-state contract.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `15 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `3 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API lifecycle smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8806` with a temporary local run-store path.
  - Called `GET /api/execution-lifecycle`.
  - Result: passed; `execution_allowed=false`, stage `waiting_for_worker` exists, failure `credential_unavailable` exists, and guard `worker_reads_credentials_from_vault_only` exists.

- Pro browser lifecycle smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8806` and `retrocause-pro-web.exe` on `127.0.0.1:3026`.
  - Initial browser attempt showed Playwright navigation blocked by external Google Fonts loading before inline script execution; this was a smoke-harness issue, not a product endpoint failure.
  - Final browser smoke aborted external font requests, loaded the web shell, and verified the lifecycle panel renders `Hosted worker lifecycle`, `execution off`, `Executing provider calls`, and `Credential unavailable`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro/doc diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: matched only intentional lifecycle guard/test strings about not exposing provider secrets; no actual secret values or API keys were added.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the worker-lifecycle contract as implemented and move the next Pro focus to store migration and adapter dry-run design.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/execution-lifecycle`; it does not change OSS APIs, accept credentials, or execute provider calls.

### Risk / Tradeoff Notes

- Security: no auth, secrets, provider credential fields, provider calls, billing hooks, real workers, or sensitive-data storage were added. The new strings explicitly document the future rule that routes must not receive raw provider secrets and workers must read credentials from a vault boundary.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the lifecycle endpoint returns a static, small JSON contract and the browser renders only a small subset of visible stages/failures. It has no queue or provider load impact.
- Understanding: the tradeoff is naming the hosted worker lifecycle before implementing workers. This reduces future ambiguity around retries, partial results, credentials, and terminal states without pretending live execution exists.
- Continuity: reused the existing queue crate as the execution-boundary owner, Axum JSON route style, `fetchJson`, and the execution-console card styling. OSS runtime paths remain untouched.

### Remaining Risks

- The lifecycle contract is a planned taxonomy, not an executable worker state machine.
- There is still no durable queue, tenant/auth enforcement, billing/quota ledger, credential vault integration, live provider adapter, retry scheduler, or persisted worker lease.
- Future hosted Pro still needs the local JSON/in-memory queue boundary migrated to Postgres plus Redis before live provider execution is safe.

## Pro Product Core Slice 14 - Hosted Storage Boundary Contract

### Scope

This task adds a no-connection hosted storage migration contract for the Pro Rust product core. The run-store crate now owns the storage migration vocabulary, the API exposes it through a keyless read endpoint, and the graph-first web shell renders a compact storage-boundary panel. No database connections, Redis connections, migrations, provider credentials, live provider calls, auth, billing, real worker process, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/run-store/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `HostedStorageMigrationPlan`, `HostedStorageMode`, `HostedStorageComponent`, `HostedStorageBoundary`, and `HostedMigrationStep`.
- Added `hosted_storage_migration_plan()` with planned Postgres components for runs, evidence, and usage ledger.
- Added planned Redis components for execution queue and cooldown buckets.
- Added tenant boundaries for workspace id, actor identity, row-level policy, and audit metadata.
- Added worker-ownership boundaries for Redis leases, status events, no route-handler execution, vault credential reads, and partial-result persistence.
- Added `GET /api/storage-plan`.
- Added a Pro web storage-boundary panel that renders target stores and connection-disabled state.
- Updated Pro docs and project state so the next focus moves to hosted provider adapter contract and dry-run shape.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for hosted storage migration contract.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `16 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `4 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API storage-plan smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8809` with a temporary local run-store path.
  - Called `GET /api/storage-plan`.
  - Result: passed; `connections_enabled=false`, `postgres_runs` exists, `redis_execution_queue` exists, and worker vault ownership exists.

- Pro browser storage-boundary smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8809` and `retrocause-pro-web.exe` on `127.0.0.1:3029`.
  - Aborted external font requests in Playwright so the inline script could run without network font blocking.
  - Verified the storage panel renders `Hosted storage boundary`, `connections off`, `postgres_runs`, and `redis_execution_queue`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro/doc diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added lines.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the provider-adapter contract as implemented and move the next Pro focus to adapter dry-run/workspace-auth/status-event work.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/provider-adapter-contract`; it does not change OSS APIs, accept credentials, or execute provider calls.

### Risk / Tradeoff Notes

- Security: no auth, secrets, provider credential fields, database connections, Redis connections, billing hooks, real workers, or sensitive-data storage were added. The new contract explicitly keeps future route handlers away from provider execution and credential reads.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the storage-plan endpoint returns a static, small JSON contract and the browser renders a small subset of components/boundaries. It has no database, Redis, or provider load impact.
- Understanding: the tradeoff is naming hosted persistence boundaries before implementing storage. This keeps future Postgres/Redis work honest about tenant scoping, worker leases, credentials, and partial-result persistence.
- Continuity: reused the existing run-store crate as the storage-boundary owner, Axum JSON route style, `fetchJson`, and the execution-console card styling. OSS runtime paths remain untouched.

### Remaining Risks

- The storage plan is a contract, not a live hosted data layer.
- There is still no Postgres schema, Redis queue, tenant/auth enforcement, billing/quota ledger, credential vault integration, live provider adapter, retry scheduler, or persisted worker lease.
- Future hosted Pro needs a dry-run adapter shape before any live provider execution is safe.

## Pro Product Core Slice 15 - Provider Adapter Contract

### Scope

This task adds the first non-executing hosted provider adapter contract for the Pro Rust product core. The provider-routing crate now owns request/result/degradation/quota/partial-result semantics, the API exposes them through a keyless read endpoint, and the graph-first web shell renders a compact adapter contract panel. No provider credentials, live provider calls, auth, billing, real workers, database/Redis connections, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/provider-routing/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `ProviderAdapterContract`, `ProviderAdapterContractMode`, `ProviderAdapterField`, and `ProviderAdapterDegradation`.
- Added `provider_adapter_contract()` with dry request fields for workspace id, job id, provider lane id, source policy, and optional evidence context.
- Added result fields for evidence items, usage ledger rows, degraded source states, and partial results.
- Added degradation states for provider rate limits, timeouts, forbidden responses, source-limited responses, and empty results.
- Added quota guards and partial-result rules that require explicit quota ownership, retry-after visibility, usage ledger rows, degraded-source surfacing, and evidence preservation before retry.
- Added `GET /api/provider-adapter-contract`.
- Added a Pro web adapter contract panel that renders request fields, degradation states, and calls-disabled state.
- Updated Pro docs and project state so the next focus moves to adapter dry-run shape, workspace/auth boundary, and durable event/status vocabulary.

### Commands Run

- `agent-guardrails plan ...`
  - Result: task contract refreshed for hosted provider adapter contract.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `17 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `5 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API provider-adapter smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8810` with a temporary local run-store path.
  - Called `GET /api/provider-adapter-contract`.
  - Result: passed; `execution_allowed=false`, request field `provider_lane_id` exists, degradation `provider_rate_limited` exists, and partial-result rule `preserve_successful_evidence_before_retry` exists.

- Pro browser provider-adapter smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8810` and `retrocause-pro-web.exe` on `127.0.0.1:3030`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Verified the adapter panel renders `Provider adapter contract`, `calls off`, `provider_lane_id`, and `provider_rate_limited`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Checked added Pro/doc diff lines for `api_key`, `secret`, `OPENROUTER`, `TAVILY`, `BRAVE`, and `sk-`.
  - Result: no matching added lines.

### Risk / Tradeoff Notes

- Security: no auth, secrets, provider credential fields, provider calls, billing hooks, real workers, database/Redis connections, or sensitive-data storage were added. The contract names future adapter inputs and outputs while preserving the disabled-call boundary.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the provider-adapter endpoint returns a static, small JSON contract and the browser renders a small subset of fields/states. It has no provider, database, Redis, or queue load impact.
- Understanding: the tradeoff is naming adapter semantics before implementing adapters. This keeps future provider work honest about quota ownership, cooldowns, degradation, usage ledgers, and partial results without pretending live execution exists.
- Continuity: reused the provider-routing crate as the provider/source decision owner, Axum JSON route style, `fetchJson`, and quota-console card styling. OSS runtime paths remain untouched.

### Remaining Risks

- The provider adapter contract is not a live adapter or dry-run executor yet.
- There is still no workspace/auth boundary, credential vault integration, provider SDK, billing/quota ledger, durable status events, or live source/provider call path.
- Future hosted Pro needs an adapter dry-run shape before any real provider execution is enabled.

## Pro Product Core Slice 16 - Provider Adapter Dry-Run Shape

### Scope

This task adds a non-executing provider adapter dry-run shape for the Pro Rust product core. The provider-routing crate now owns the dry-run request/result payload, the API exposes it through a keyless POST endpoint, and the graph-first web shell can run the dry-run for the current graph question. No provider credentials, live provider calls, auth, billing, workers, database/Redis connections, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/provider-routing/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `ProviderAdapterDryRunRequest`, `ProviderAdapterDryRunResult`, `ProviderAdapterDryRunMode`, `ProviderAdapterEvidencePreview`, and `ProviderAdapterUsagePreview`.
- Added `provider_adapter_dry_run()` so a workspace/query/lane/source-policy request returns preview evidence, zero-billable usage ledger rows, selected lane ownership, degradation states, and dry-run warnings.
- Added `POST /api/provider-adapter/dry-run`.
- Added a Pro web `Dry-run adapter` action and result panel that shows dry-run-only mode, calls-disabled state, zero billable units, evidence-preview count, and degradation states.
- Updated Pro docs and project state so the next focus moves to workspace/auth boundary, durable event/status vocabulary, and a future live adapter candidate behind explicit gates.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `18 passed`.
  - Domain tests: `8 passed`.
  - Provider-routing tests: `7 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API dry-run smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8811` with a temporary local run-store path.
  - Called `POST /api/provider-adapter/dry-run`.
  - Result: passed; `mode=dry_run_only`, `provider_lane_id=uploaded_evidence_lane`, `execution_allowed=false`, `billable_units=0`, warning `dry_run_only_no_provider_calls` exists, and degradation `provider_rate_limited` exists.

- Pro browser dry-run smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8812` and `retrocause-pro-web.exe` on `127.0.0.1:3031`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Clicked `#provider-adapter-dry-run-button`.
  - Result: passed; the dry-run panel rendered `dry run only`, `calls off`, `uploaded_evidence_lane`, `billable units: 0`, and `provider_rate_limited`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A broad scan for words such as `secret` intentionally matched documentation statements saying secrets are not read.
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the dry-run shape as implemented and move the next Pro focus to workspace/auth and durable status vocabulary.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `POST /api/provider-adapter/dry-run`; it does not change OSS APIs, accept credentials, bill usage, or execute provider calls.

### Risk / Tradeoff Notes

- Security: the dry-run accepts only workspace id, query, lane id, and source policy. It does not accept, read, store, log, or return provider secrets or API keys. Auth remains future work and is not simulated as real protection in this slice.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the dry-run is deterministic and in-process. It reuses the existing provider-status/routing-preview data and returns a small JSON payload, so there is no provider, database, Redis, worker, or queue load impact.
- Understanding: the tradeoff is making adapter result shape testable before live execution. That gives future provider work a concrete contract for evidence previews, usage ledger rows, degradation states, and warnings without pretending the live path exists.
- Continuity: reused the provider-routing crate, routing-preview error handling, Axum JSON route style, web `fetchJson` helper, and existing quota/adapter card styling. OSS runtime paths remain untouched.

### Remaining Risks

- The dry-run is not a live provider adapter and does not prove provider connectivity, model output quality, or search-result quality.
- There is still no workspace/auth boundary, credential vault integration, billing/quota ledger, durable status events, real worker process, retry scheduler, or live source/provider call path.
- Future hosted Pro must add explicit auth and quota gates before any live adapter can execute provider calls.

## Pro Product Core Slice 17 - Workspace/Auth Boundary Preview

### Scope

This task adds the first non-enforcing workspace/auth boundary preview for the Pro Rust product core. The shared domain crate now owns the workspace access context payload, the API exposes it through a keyless read endpoint, and the graph-first web shell renders the preview actor, preview permissions, future gated permissions, and auth safeguards. No real auth, sessions, cookies, JWT validation, credential storage, billing, database/Redis connections, provider calls, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `WorkspaceAccessContext`, `WorkspaceActor`, `WorkspacePermission`, and workspace/auth permission enums.
- Added `workspace_access_context()` with demo workspace id, local preview actor, preview-allowed permissions, future gated permissions, safeguards, and sensitive-data rules.
- Added `GET /api/workspace/access-context`.
- Added a Pro web workspace access panel that renders preview auth mode, non-enforcement mode, preview permissions, future gated permissions, and safeguards.
- Updated Pro docs and project state so the next focus moves to durable event/status vocabulary and future live-provider work behind explicit gates.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `19 passed`.
  - Domain tests: `9 passed`.
  - Provider-routing tests: `7 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API workspace-access smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8813` with a temporary local run-store path.
  - Called `GET /api/workspace/access-context`.
  - Result: passed; `workspace_id=workspace_demo`, `auth_mode=local_preview_only`, `enforcement_mode=not_enforced_preview`, six permissions were returned, provider execution is gated as `requires_auth_later`, and session/tenant safeguards are present.

- Pro browser workspace-access smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8814` and `retrocause-pro-web.exe` on `127.0.0.1:3032`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Result: passed; the workspace access panel rendered `Workspace access preview`, `not enforced preview`, `Local preview operator`, `Create preview runs`, `Execute provider calls`, and `no_sessions_or_cookies_issued`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors after committing the workspace/auth slice.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the workspace/auth preview as implemented and move the next Pro focus to durable event/status vocabulary.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/workspace/access-context`; it does not change OSS APIs, enforce auth, accept credentials, mutate billing/quota, or execute provider calls.

### Risk / Tradeoff Notes

- Security: this slice explicitly does not authenticate or authorize requests. It does not issue sessions or cookies, validate tokens, read or store secrets, accept provider credentials, mutate billing/quota, or protect hosted resources. The value is the visible boundary vocabulary and the safeguards that prevent future provider execution from being mistaken as safe before auth exists.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the endpoint returns one static in-process JSON payload and the browser renders a small card. It has no database, Redis, provider, worker, billing, or credential-vault load impact.
- Understanding: the tradeoff is putting auth vocabulary in the shared domain before real auth exists. That makes future tenant/actor/permission replacement explicit while avoiding fake protection in the current local preview.
- Continuity: reused the shared domain crate for cross-service payloads, Axum JSON route style, web `fetchJson` helper, and existing compact card styling. OSS runtime paths remain untouched.

### Remaining Risks

- The access context is not security enforcement. It is only a local preview contract.
- There is still no tenant resolver, actor identity provider, session store, JWT validation, credential vault, billing/quota ledger, durable status events, real worker process, retry scheduler, or live source/provider call path.
- Future hosted Pro must implement real auth/tenant enforcement before enabling provider execution or shared hosted data.

## Pro Product Core Slice 18 - Run Event/Status Vocabulary

### Scope

This task adds a non-durable run event/status vocabulary for the Pro Rust product core. The shared domain crate now derives a run event timeline from a `ProRun`, the API exposes it through a keyless per-run endpoint, and the graph-first web shell renders a compact event timeline. No database, Redis, event-store connection, background worker, provider call, auth enforcement, billing, OSS runtime change, dependency change, or package publishing was added.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `RunEventTimeline`, `RunEvent`, `RunStatusVocabularyEntry`, `RunEventKind`, and `RunEventSource`.
- Added `run_event_timeline()` and `run_status_vocabulary()` so a current `ProRun` can produce a non-durable timeline, recent events, reviewability status vocabulary, and safeguards.
- Added `GET /api/runs/{run_id}/events`.
- Added a Pro web run-event panel that renders current status, non-durable mode, recent events, status vocabulary, and event-store safeguards.
- Updated Pro docs and project state so the next focus moves to the first live-provider adapter candidate behind explicit auth, quota, dry-run, and status-event gates.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: passed.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `20 passed`.
  - Domain tests: `11 passed`.
  - Provider-routing tests: `7 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API run-events smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8815` with a temporary local run-store path.
  - Called `GET /api/runs/run_semiconductor_controls_001/events`.
  - Result: passed; `run_id=run_semiconductor_controls_001`, `durable=false`, four derived events, seven status-vocabulary entries, `review_ready` event present, `partial_live` vocabulary present, and event-store safeguard present.

- Pro browser run-events smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8816` and `retrocause-pro-web.exe` on `127.0.0.1:3033`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Result: passed; the event panel rendered `Run event timeline`, `non durable`, `ready for review`, `Ready for review`, `Partial live`, and `no_event_store_connection_in_this_slice`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the run event/status vocabulary as implemented and move the next Pro focus to live-provider adapter work behind gates.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/runs/{run_id}/events`; it does not change OSS APIs, connect an event store, enforce auth, mutate billing/quota, or execute provider calls.

### Risk / Tradeoff Notes

- Security: the event endpoint reads only an existing run record and derives a timeline. It does not authenticate requests, enforce authorization, issue sessions, read provider credentials, accept secrets, mutate billing/quota, or protect hosted resources.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the timeline is generated in process from one run payload and returns a small JSON response. It adds no event-store, database, Redis, worker, provider, or billing load.
- Understanding: the deliberate tradeoff is naming event/status semantics before durable storage exists. That gives the UI and API a concrete vocabulary for run history without pretending this is an audit log or worker queue.
- Continuity: reused the shared domain crate, existing `RunStatus`, Axum JSON route style, local file-backed run-store reads, web `fetchJson` helper, and compact card styling. OSS runtime paths remain untouched.

### Remaining Risks

- The event timeline is not durable and should not be treated as an audit log.
- There is still no event store, tenant resolver, real auth, credential vault, billing/quota ledger, persisted worker lease, retry scheduler, or live source/provider call path.
- Future hosted Pro should replace or supplement this derived timeline with event-store rows after auth, storage, and worker boundaries are real.

## Pro Product Core Slice 19 - Gated Live-Adapter Candidate

### Scope

This task adds the first gated live-provider adapter candidate for the Pro Rust product core. The provider-routing crate now registers an OfoxAI model adapter candidate and a gate-check payload, the API exposes keyless candidate/gate-check endpoints, and the graph-first web shell renders candidate and denied gate-check panels. No provider credentials, credential vaults, live provider/search calls, auth enforcement, billing, database/Redis connections, workers, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/provider-routing/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `ProviderAdapterCandidateCatalog`, `ProviderAdapterCandidate`, `ProviderAdapterGate`, `ProviderAdapterGateCheckRequest`, and `ProviderAdapterGateCheckResult`.
- Added `provider_adapter_candidates()` with a registration-only OfoxAI model adapter candidate.
- Added `provider_adapter_gate_check()` so preview-observed gates can be reported while live execution remains denied until real auth, vault, quota-ledger, and worker gates exist.
- Added `GET /api/provider-adapter/candidates` and `POST /api/provider-adapter/gate-check`.
- Added Pro web panels for the live adapter candidate and gate-check result, including explicit blocking reasons.
- Updated Pro docs and project state so the next focus moves to graph-review comparison workflow and the real hosted boundaries required before live execution.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: passed.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `22 passed`.
  - Domain tests: `11 passed`.
  - Provider-routing tests: `10 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API adapter-candidate smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8817` with a temporary local run-store path.
  - Called `GET /api/provider-adapter/candidates`.
  - Called `POST /api/provider-adapter/gate-check` with preview gates marked observed.
  - Result: passed; one OfoxAI candidate was returned, `execution_allowed=false`, `workspace_auth_enforced` and `credential_vault_connected` blockers were present, and warning `live_provider_execution_denied` was present.

- Pro browser adapter-candidate smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8818` and `retrocause-pro-web.exe` on `127.0.0.1:3034`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Ran the adapter dry-run, clicked `Check live gates`, and verified the candidate/gate panels.
  - Result: passed; the UI rendered `OfoxAI model adapter candidate`, `execution denied`, `Live adapter gate check`, `workspace_auth_enforced`, and `credential_vault_connected`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the gated OfoxAI adapter candidate as implemented and move the next Pro focus to graph-review workflow plus real hosted boundaries.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/provider-adapter/candidates` and `POST /api/provider-adapter/gate-check`; it does not change OSS APIs, accept credentials, connect a vault, enforce auth, mutate billing/quota, or execute provider calls.

### Risk / Tradeoff Notes

- Security: this slice explicitly does not enable provider execution. It does not accept or read provider secrets, connect a credential vault, enforce auth, mutate billing/quota, or protect hosted resources. The gate-check endpoint always returns `execution_allowed=false`.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the candidate catalog and gate-check are deterministic in-process payloads. They add no provider, database, Redis, worker, credential-vault, or billing load.
- Understanding: the deliberate tradeoff is registering a concrete OfoxAI candidate before implementing the adapter. This gives future work a named target and visible blockers without creating a fake live path.
- Continuity: reused the provider-routing crate, Axum JSON route style, the existing web `fetchJson` helper, the adapter card styling, the earlier dry-run result state, and the run event/workspace/auth preview gates. OSS runtime paths remain untouched.

### Remaining Risks

- The OfoxAI adapter candidate is not a live adapter.
- The gate check is preview-only and should not be treated as real security, quota enforcement, provider connectivity, or worker readiness.
- Future hosted Pro still needs tenant/auth enforcement, credential vault integration, a quota ledger, worker execution, durable event storage, retry scheduling, and provider SDK integration before any live calls are safe.

## Pro Product Core Slice 20 - Graph Review Comparison Preview

### Scope

This task adds a keyless graph-review comparison preview for the Pro Rust product core. The shared domain crate now defines evidence/challenge delta payloads, the API exposes a per-run comparison endpoint, and the graph-first web shell renders a compact review-comparison panel. No live provider calls, auth enforcement, billing, database/Redis/event-store connections, workers, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `RunReviewComparison`, evidence/challenge delta payloads, delta summaries, and comparison/delta enums.
- Added `run_review_comparison()` so the current run can be compared against a derived previous-checkpoint preview without querying historical storage.
- Added `GET /api/runs/{run_id}/review-comparison`.
- Added a Pro web review-comparison panel that renders derived checkpoint mode, evidence/challenge delta counts, visible delta items, and comparison safeguards.
- Updated Pro project state and architecture docs so maintainers can see that this is a derived preview, not a durable cross-run comparison system.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: passed.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed after formatting.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `23 passed`.
  - Domain tests: `13 passed`.
  - Provider-routing tests: `10 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API review-comparison smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8819` with a temporary local run-store path.
  - Called `GET /api/runs/run_semiconductor_controls_001/review-comparison`.
  - Result: passed; mode was `derived_previous_checkpoint`, baseline was `run_semiconductor_controls_001_previous_checkpoint`, evidence added count was `1`, challenge added count was `1`, and safeguard `no_provider_calls_or_credential_reads` was present.

- Pro browser review-comparison smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8822` and `retrocause-pro-web.exe` on `127.0.0.1:3037`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Result: passed; the review-comparison panel rendered `Review comparison`, `derived previous checkpoint`, `Evidence +1`, `challenges +1`, `comparison_preview_derived_from_current_run`, and `no_historical_run_store_query_in_this_slice`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the non-doc diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the review-comparison preview as implemented and move the next Pro focus to durable/auth-backed cross-run comparison.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/runs/{run_id}/review-comparison`; it does not change OSS APIs, enforce auth, accept credentials, mutate billing/quota, or execute provider calls.

### Risk / Tradeoff Notes

- Security: this slice does not authenticate or authorize requests, and it does not pretend to protect cross-run access. The comparison is derived from the requested local run and does not read provider credentials, accept secrets, call providers, mutate billing/quota, or query another tenant's history.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the comparison is deterministic and in-process. It builds small maps over one run's evidence and challenge arrays, adds no provider/database/Redis/event-store/worker load, and should stay negligible for the current local Pro payload size.
- Understanding: the deliberate tradeoff is shaping the review-delta UI before durable history exists. The baseline is a generated previous-checkpoint preview, so maintainers should not treat this as a true historical diff.
- Continuity: reused the shared domain crate, existing `ProRun` evidence/challenge types, Axum per-run endpoint style, web `fetchJson` helper, and compact card styling. OSS runtime paths remain untouched.

### Remaining Risks

- The comparison is not backed by durable run history and does not yet let users select another real run.
- The endpoint is keyless and non-enforcing; future hosted Pro must add real tenant/auth boundaries before exposing true cross-run comparisons.
- Future hosted Pro still needs tenant auth, durable run history, credential vault integration, quota ledger enforcement, worker execution, event storage, retry scheduling, and provider SDK integration before live adapter work is safe.

## Pro Product Core Slice 21 - Credential Vault Boundary Preview

### Scope

This task adds a keyless credential-vault boundary preview for the Pro Rust product core. The shared domain crate now defines credential class, access-rule, rotation-rule, and safeguard payloads; the API exposes a read-only vault-boundary endpoint; and the graph-first web shell renders a compact vault panel. No provider credentials are accepted, stored, read, logged, or echoed. No live provider calls, auth enforcement, billing, database/Redis/event-store connections, workers, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `CredentialVaultBoundary`, credential classes, vault access rules, vault rotation rules, and credential visibility/storage enums.
- Added `credential_vault_boundary()` returning `planned_no_secrets`, `connections_enabled=false`, and `secret_values_returned=false`.
- Added `GET /api/credential-vault-boundary`.
- Added a Pro web vault-boundary panel that renders credential classes, blocked access rules, and safeguards without rendering credential values.
- Updated Pro project state and architecture docs so maintainers can see this is a disconnected boundary contract, not a real vault.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - First result: failed because a domain test used `serde_json` without a domain dependency.
  - Fix: removed the `serde_json` assertion and checked payload fields directly, avoiding a new dependency.
  - Final result: passed.
  - API tests: `24 passed`.
  - Domain tests: `14 passed`.
  - Provider-routing tests: `10 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API credential-vault smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8823` with a temporary local run-store path.
  - Called `GET /api/credential-vault-boundary`.
  - Result: passed; mode was `planned_no_secrets`, `connections_enabled=false`, `secret_values_returned=false`, three credential classes and three access rules were returned, and safeguard `no_secret_values_in_requests_or_responses` was present.

- Pro browser credential-vault smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8824` and `retrocause-pro-web.exe` on `127.0.0.1:3038`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Result: passed; the vault panel rendered `Credential vault boundary`, `planned no secrets`, `connections off`, `secret values returned: no`, `Managed model provider credentials`, `api_routes_never_read_secret_values`, and `no_secret_values_in_requests_or_responses`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the non-doc diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the credential-vault boundary preview as implemented and move the next Pro focus toward quota-ledger/billing boundaries.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/credential-vault-boundary`; it does not change OSS APIs, accept credentials, store secrets, enforce auth, mutate billing/quota, or execute provider calls.

### Risk / Tradeoff Notes

- Security: this slice explicitly does not implement a vault. It does not accept credential input, store secrets, read secrets, log secrets, return secret values, enforce auth, or enable worker/provider execution. It only makes future credential ownership and access rules visible.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced. The failed `serde_json` test was fixed without adding the dependency.
- Performance: the endpoint returns one static in-process payload and the browser renders one compact panel. It adds no provider, database, Redis, event-store, worker, billing, or vault load.
- Understanding: the deliberate tradeoff is naming credential classes and access rules before real vault infrastructure exists. This helps future live-adapter work avoid ad hoc key handling while keeping the current system honest about not being secure vault storage.
- Continuity: reused the shared domain crate for static contract payloads, Axum read-only endpoint style, the web `fetchJson` helper, and existing compact boundary-card styling. OSS runtime paths remain untouched.

### Remaining Risks

- This is not a credential vault and should not be treated as one.
- There is still no real tenant auth, credential encryption, secret rotation, scoped worker lease, quota ledger, billing boundary, durable event storage, retry scheduler, or live source/provider call path.
- Future hosted Pro must implement real vault-backed metadata and worker-scoped secret access before any live adapter can execute provider calls.

## Pro Product Core Slice 22 - Quota Ledger/Billing Boundary Preview

### Scope

This task adds a preview-only quota-ledger and billing boundary for the Pro Rust product core. The shared domain crate now defines quota lanes, metering rules, rate-limit rules, billing decision mode, and safeguards; the API exposes a read-only boundary endpoint; and the graph-first web shell renders a compact quota-ledger panel. No payment provider integration, quota reservation, ledger mutation, billable usage emission, live provider calls, credential handling, auth enforcement, database/Redis/event-store connections, workers, OSS runtime changes, dependency changes, or package publishing were added.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `QuotaLedgerBoundary`, quota lanes, metering rules, rate-limit rules, and billing/quota accounting enums.
- Added `quota_ledger_boundary()` returning `planned_no_mutation`, `ledger_mutation_enabled=false`, `payment_provider_connected=false`, and no billable lanes.
- Added `GET /api/quota-ledger-boundary`.
- Added a Pro web quota-ledger panel that renders quota lanes, metering rules, and safeguards without enabling ledger writes or payment infrastructure.
- Updated Pro project state and architecture docs so maintainers can see this is a no-mutation boundary contract, not a billing system.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because Rustfmt wanted to reflow one domain-test assertion.
  - Fix: ran `cargo fmt --manifest-path pro/Cargo.toml --all`.
  - Final result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `25 passed`.
  - Domain tests: `15 passed`.
  - Provider-routing tests: `10 passed`.
  - Queue tests: `6 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API quota-ledger smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8825` with a temporary local run-store path.
  - Called `GET /api/quota-ledger-boundary`.
  - Result: passed; mode was `planned_no_mutation`, `ledger_mutation_enabled=false`, `payment_provider_connected=false`, four quota lanes were returned, and safeguard `no_billing_mutation_in_this_slice` was present.

- Pro browser quota-ledger smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8826` and `retrocause-pro-web.exe` on `127.0.0.1:3039`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Result: passed; the quota-ledger panel rendered `Quota ledger boundary`, `planned no mutation`, `ledger mutation off`, `payment provider: off`, `managed_model_pool`, and `no_billing_mutation_in_this_slice`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the non-doc diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the quota-ledger/billing boundary preview as implemented and move the next Pro focus toward worker lease/retry-scheduler boundaries.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/quota-ledger-boundary`; it does not change OSS APIs, accept credentials, connect payment infrastructure, mutate billing/quota, enforce auth, or execute provider calls.

### Risk / Tradeoff Notes

- Security: this slice explicitly does not implement billing, quota enforcement, or provider execution. It does not accept payment credentials, provider credentials, secrets, tokens, auth material, or user API keys. It does not enforce permissions or protect hosted resources.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the endpoint returns one static in-process payload and the browser renders one compact panel. It adds no provider, database, Redis, event-store, worker, billing, quota-ledger, or payment-provider load.
- Understanding: the deliberate tradeoff is naming quota/billing semantics before writing ledger rows. This gives live-adapter work a visible gate without pretending the current local Pro shell can charge, reserve quota, or enforce limits.
- Continuity: reused the shared domain crate, Axum read-only endpoint style, web `fetchJson` helper, and existing compact boundary-card styling. OSS runtime paths remain untouched.

### Remaining Risks

- This is not a quota ledger, billing engine, rate limiter, or payment integration.
- There is still no real tenant auth, quota reservation, usage write path, billing policy, payment provider connection, credential vault, scoped worker lease, durable event storage, retry scheduler, or live source/provider call path.
- Future hosted Pro must implement quota reservations and billing checks behind tenant auth, vault access, event storage, and worker leases before any live adapter can execute billable provider calls.

## Pro Product Core Slice 23 - Worker Lease/Retry Scheduler Boundary Preview

### Scope

This task adds a preview-only worker-lease and retry-scheduler boundary for the Pro Rust product core. The queue crate now defines lease rules, retry policies, idempotency rules, and safeguards; the API exposes a read-only boundary endpoint; and the graph-first web shell renders a compact worker-lease panel. No real workers, provider execution, queue persistence, Redis/database/event-store connections, credential access, auth enforcement, quota/billing mutation, OSS runtime changes, dependency changes, package publishing, retry loop, or live provider calls were added.

### Files Updated

- `pro/crates/queue/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `WorkerLeaseBoundary`, lease rules, retry scheduler rules, idempotency rules, and worker/retry status enums.
- Added `worker_lease_boundary()` returning `planned_no_workers`, `lease_store_connected=false`, `retry_scheduler_enabled=false`, and `execution_allowed=false`.
- Added `GET /api/worker-lease-boundary`.
- Added a Pro web worker-lease panel that renders lease rules, retry policies, and safeguards without enabling worker claims or retry scheduling.
- Updated Pro project state and architecture docs so maintainers can see this is a no-worker boundary contract, not a queue worker implementation.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because Rustfmt wanted to reflow several queue-crate lines.
  - Fix: ran `cargo fmt --manifest-path pro/Cargo.toml --all`.
  - Final result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed after formatting.
  - API tests: `26 passed`.
  - Domain tests: `15 passed`.
  - Provider-routing tests: `10 passed`.
  - Queue tests: `7 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API worker-lease smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8827` with a temporary local run-store path.
  - Called `GET /api/worker-lease-boundary`.
  - Result: passed; mode was `planned_no_workers`, lease store was disconnected, retry scheduler was disabled, execution was disabled, three retry rules were returned, and safeguard `no_worker_process_started` was present.

- Pro browser worker-lease smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8828` and `retrocause-pro-web.exe` on `127.0.0.1:3040`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Result: passed; the worker-lease panel rendered `Worker lease boundary`, `planned no workers`, `lease store: off`, `retry scheduler: off`, `provider_rate_limited_retry`, and `no_worker_process_started`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the non-doc diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the worker-lease/retry boundary preview as implemented and move the next Pro focus toward result-commit/event-store boundaries.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/worker-lease-boundary`; it does not change OSS APIs, start workers, connect a lease store, schedule retries, accept credentials, enforce auth, mutate quota/billing, or execute provider calls.

### Risk / Tradeoff Notes

- Security: this slice explicitly does not start workers or execute provider calls. It does not accept, read, store, log, or return provider secrets, payment credentials, auth tokens, or sensitive user credentials. It does not enforce permissions or protect hosted resources.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the endpoint returns one static in-process payload and the browser renders one compact panel. It adds no provider, database, Redis, event-store, worker, retry-scheduler, credential-vault, quota-ledger, or payment-provider load.
- Understanding: the deliberate tradeoff is naming lease, retry, and idempotency semantics before implementing workers. This gives live-adapter work a visible execution gate without pretending the current local Pro shell can claim jobs, retry provider calls, or reconcile partial results.
- Continuity: reused the existing queue crate, existing lifecycle/work-order contract pattern, Axum read-only endpoint style, web `fetchJson` helper, and compact boundary-card styling. OSS runtime paths remain untouched.

### Remaining Risks

- This is not a worker runtime, retry scheduler, durable lease store, idempotent provider executor, or event-backed result committer.
- There is still no real tenant auth, queue persistence, lease ownership, retry loop, event-store write path, credential vault, quota reservation, billing policy, payment provider connection, or live source/provider call path.
- Future hosted Pro must implement durable worker leases, bounded retry scheduling, idempotent provider calls, partial-result reconciliation, and event-store commits before any live adapter can execute safely.

## Pro Product Core Slice 24 - Result Commit/Event Store Boundary Preview

### Scope

This task adds a preview-only result-commit and event-store boundary for the Pro Rust product core. The shared domain crate now defines result commit stages, event-store write rules, partial-result reconciliation rules, and safeguards; the API exposes a read-only boundary endpoint; and the graph-first web shell renders a compact result-commit panel. No durable event writes, database/Redis connections, worker execution, provider execution, credential access, auth enforcement, quota/billing mutation, OSS runtime changes, dependency changes, package publishing, or live provider calls were added.

### Files Updated

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `ResultCommitBoundary`, commit stages, event-store write rules, partial-result reconciliation rules, and result-commit status enums.
- Added `result_commit_boundary()` returning `planned_no_writes`, `event_store_connected=false`, `commit_writes_enabled=false`, and `partial_reconciliation_enabled=false`.
- Added `GET /api/result-commit-boundary`.
- Added a Pro web result-commit panel that renders commit stages, event-write rules, reconciliation rules, and safeguards without enabling durable writes.
- Updated Pro project state and architecture docs so maintainers can see this is a disconnected boundary contract, not an event store.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - First result: failed because Rustfmt wanted to reflow several domain-test lines.
  - Fix: ran `cargo fmt --manifest-path pro/Cargo.toml --all`.
  - Final result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `27 passed`.
  - Domain tests: `16 passed`.
  - Provider-routing tests: `10 passed`.
  - Queue tests: `7 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API result-commit smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8831` with a temporary local run-store path.
  - Called `GET /api/result-commit-boundary`.
  - Result: passed; mode was `planned_no_writes`, event store was disconnected, commit writes were disabled, partial reconciliation was disabled, three commit stages and three event-write rules were returned, and safeguard `no_event_store_write_in_this_slice` was present.

- Pro browser result-commit smoke
  - First attempt counted intentionally aborted external font requests as console errors.
  - Re-ran with font `ERR_FAILED` messages ignored, matching previous Pro browser smoke behavior.
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8832` and `retrocause-pro-web.exe` on `127.0.0.1:3042`.
  - Result: passed; the result-commit panel rendered `Result commit boundary`, `planned no writes`, `event store: off`, `writes off`, `partial reconciliation: off`, `commit_evidence_events`, `api_routes_cannot_write_events`, and `no_event_store_write_in_this_slice`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no actual key-shaped tokens in the non-doc diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Pre-commit result: blocked because the base range included the previous committed worker-lease slice and reported `pro/crates/queue/src/lib.rs` as out of scope for this result-commit slice.
  - Interpretation: this was a range-selection issue before the current slice was committed, not a current worktree scope violation. The current slice intentionally touches only the contract-allowed domain/API/web/docs/evidence paths.
  - Final post-commit result: passed with no blocking errors.
  - Score: `90/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the result-commit/event-store boundary preview as implemented.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/result-commit-boundary`; it does not change OSS APIs, write events, enforce auth, accept credentials, mutate quota/billing, or execute provider calls.

- `agent-guardrails check --review --base-ref HEAD --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Pre-commit result: safe-to-deploy score `95/100`, with one non-blocking warning that no git changes were detected because this guardrails invocation did not include the uncommitted worktree diff.
  - Interpretation: useful for confirming the contract/evidence shape, but not the final merge gate.

### Risk / Tradeoff Notes

- Security: this slice explicitly does not implement an event store or result committer. It does not accept, read, store, log, or return provider secrets, payment credentials, auth tokens, or sensitive user credentials. It does not enforce permissions or protect hosted resources.
- Dependencies: no new crates, npm packages, lockfile changes, or version upgrades were introduced.
- Performance: the endpoint returns one static in-process payload and the browser renders one compact panel. It adds no provider, database, Redis, event-store, worker, retry-scheduler, credential-vault, quota-ledger, or payment-provider load.
- Understanding: the deliberate tradeoff is naming commit, event-write, and reconciliation semantics before implementing durable event storage. This keeps future live adapters from committing results directly inside routes while being honest that current payloads are previews.
- Continuity: reused the shared domain crate, Axum read-only endpoint style, web `fetchJson` helper, and compact boundary-card styling. OSS runtime paths remain untouched.

### Remaining Risks

- This is not an event store, durable result committer, audit log, reconciliation engine, or worker result writer.
- There is still no real tenant auth, quota reservation, credential vault access, durable event-store write path, worker lease ownership, retry scheduler, or live source/provider call path.
- Future hosted Pro must implement durable event writes, idempotent worker commits, partial-result reconciliation, tenant-scoped auth, quota reservations, vault handles, and storage boundaries before any live adapter can execute safely.

## Pro Product Core Slice 25 - Local Event Store/Run Event Replay

### Scope

This task adds a local durable event-store and run event replay slice for the Pro Rust product core. A new Rust event-store crate persists run-scoped event streams to a local JSON file, the Pro API initializes seed/create-run replay streams and exposes read-only event-log/replay endpoints, and the graph-first web shell renders a compact replay panel. This stays local-only and keyless: no Postgres/Redis, hosted auth, workers, provider execution, credential access, quota/billing mutation, OSS runtime changes, npm dependencies, package publishing, or live provider calls were added.

### Files Updated

- `pro/Cargo.toml`
- `pro/Cargo.lock`
- `pro/crates/event-store/Cargo.toml`
- `pro/crates/event-store/src/lib.rs`
- `pro/apps/api/Cargo.toml`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

### What Changed

- Added `crates/event-store` with `FileEventStore`, local JSON persistence, `RETROCAUSE_PRO_EVENT_STORE_PATH`, run-scoped `EventStoreEntry`, and `EventStoreReplay`.
- Persisted a replay stream for the canonical seed run when the Pro API opens, and for every successful `POST /api/runs` create request.
- Added `GET /api/runs/{run_id}/event-log` and `GET /api/runs/{run_id}/event-replay`.
- Added API/unit tests proving persisted event-log and replay payloads are scoped to the requested run and created runs get one replay event.
- Added event-store crate tests proving sample replay persistence, reopen-without-duplication, and event-log/replay consistency.
- Added a graph-first web event-replay panel that fetches `/api/runs/{run_id}/event-replay` and renders durable local mode, local-file replay, replay stream entries, and safeguards.
- Updated project state and Pro architecture docs to distinguish the existing derived `/events` timeline from the new local JSON replay stream, and to clarify that this is not hosted event storage or a worker/provider result commit path.

### Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `29 passed`.
  - Domain tests: `16 passed`.
  - Event-store tests: `3 passed`.
  - Provider-routing tests: `10 passed`.
  - Queue tests: `7 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API event-store/replay smoke
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8833` with temporary `RETROCAUSE_PRO_RUN_STORE_PATH` and `RETROCAUSE_PRO_EVENT_STORE_PATH`.
  - Called `GET /api/runs/run_semiconductor_controls_001/event-replay`.
  - Called `GET /api/runs/run_semiconductor_controls_001/event-log`.
  - Created a run through `POST /api/runs`.
  - Called `GET /api/runs/{created_run_id}/event-replay`.
  - Result: passed; seed replay mode was `local_file_replay`, durable was `true`, seed event count was `4`, created run id was `run_local_000001`, created replay event count was `1`, and the local event-store JSON file contained both the seed run id and created run id.

- Pro browser event-replay smoke
  - First attempt failed because PowerShell `Invoke-WebRequest` produced a local object-reference error while checking the web page, even though the web process was listening.
  - Re-ran with TCP readiness checks for the API/web ports.
  - Started `retrocause-pro-api.exe` on `127.0.0.1:8834` and `retrocause-pro-web.exe` on `127.0.0.1:3043`.
  - Aborted external font requests in Playwright so inline scripts could run without network font blocking.
  - Result: passed; the event-replay panel rendered `Event replay`, `local durable`, `local file replay`, `events`, and `local_file_event_store_only`.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Result: passed. A key-shaped scan for common provider-token prefixes and API-key assignment patterns found no key-shaped tokens in the git diff.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with concerns; no blocking errors.
  - Score: `75/100 (pass-with-concerns)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the project state was synchronized to mark the local event-store/replay slice as implemented and to move the next Pro focus away from the already-landed event-store boundary.
  - Non-blocking warning: `pro/crates/event-store/Cargo.toml` and `pro/crates/event-store/src/lib.rs` are state-related files. This was intentional because the slice adds the new local JSON event-store boundary that owns persisted run-event replay state.
  - Non-blocking warning: `pro/apps/api/src/main.rs` is an interface-changing file. This slice intentionally adds keyless local `GET /api/runs/{run_id}/event-log` and `GET /api/runs/{run_id}/event-replay`; it does not change OSS APIs, accept credentials, enforce auth, mutate quota/billing, start workers, or execute provider calls.
  - Non-blocking warning: `pro/Cargo.toml`, `pro/apps/api/Cargo.toml`, and `pro/crates/event-store/Cargo.toml` are config/dependency files. This was intentional because the workspace now includes one internal crate; no external crates, npm dependencies, package publishing, deployment config, or hosted infrastructure changes were added.

### Risk / Tradeoff Notes

- Security: this slice does not accept, read, store, log, or return provider secrets, payment credentials, auth tokens, or user API keys. It does not enforce hosted permissions or protect hosted resources. Replay is scoped by requested run id and only persists local derived run events.
- Dependencies: one new internal workspace crate was added: `retrocause-pro-event-store`. `Cargo.lock` changed because the workspace gained that crate, but no external crate versions or npm packages were added or upgraded.
- Performance: the local event store reads/writes one JSON file behind an in-process lock. This is acceptable for local alpha inspectability, but it is not a high-concurrency hosted store. Future hosted Pro should move event rows to a database/event log before multi-user worker writes.
- Understanding: the deliberate tradeoff is that `event-log` and `event-replay` can initialize a missing stream for a known run from the current derived timeline. That keeps local replay deterministic after restarts, but it is not an immutable audit-log guarantee.
- Continuity: reused existing Pro patterns: shared Rust crates, Axum state/endpoint style, local `.retrocause` defaults plus env overrides, server-rendered web panels, compact boundary-card styling, and existing run-event timeline vocabulary. OSS runtime paths remain untouched.

### Remaining Risks

- This is not hosted event storage, not a worker event queue, not a multi-tenant audit log, and not a provider result committer.
- Local JSON event-store writes are suitable for the Pro foundation and developer inspection only; they are not safe for concurrent hosted production workloads.
- Future hosted Pro still needs tenant auth, quota reservation, credential vault access, durable worker leases, idempotent result commits, and database-backed event rows before any live adapter can execute safely.
