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
