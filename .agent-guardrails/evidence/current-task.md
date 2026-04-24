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
