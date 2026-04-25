# Current Task Evidence

## Task

Restructure the Pro Rust web shell so the root page is an awesome-design-md xAI-inspired dialogue-only homepage, while the knowledge graph, source, gate, queue, evidence, and review controls live on the separate `/graph` workspace. Keep the graph as a cinematic galaxy/star-map surface and preserve all preview-only hosted execution boundaries.

## Scope

- `DESIGN.md`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

## What Changed

- Added a separate `GET /graph` web route while keeping `/` as a dialogue-only causal question entry page.
- The root page now renders only the brand/navigation, star/orbit background, one large causal question form, and the explicit Pro alpha boundary copy.
- The root page no longer renders graph nodes, provider/source panels, queue panels, graph inspector, evidence, review, or gate panels.
- The root form routes to `/graph?question=...`; the graph page stages that question into the existing run-creation console without auto-executing providers.
- Kept the existing `/graph` Pro API/client patterns and all preview-only provider, queue, admission, intent, storage, vault, quota, event, result, and review panels.
- Fixed the previous unassigned `control-rail` layout regression by keeping access/event/review preview panels inside the graph page's scrollable question rail instead of adding an extra grid item.
- Added `resizeGalaxyField()` so the 1220x720 graph coordinate space scales and centers inside the current graph viewport; browser smoke verified all six graph nodes remain visible and not clipped.
- Updated `DESIGN.md`, `docs/PROJECT_STATE.md`, and `docs/pro-rust-architecture.md` to document the dialogue-home plus galaxy-graph route split.
- Updated the task contract to match the revised user request and expected browser smokes for `/` and `/graph`.

## Commands Run

- Read-before-edit context:
  - `Get-Content AGENTS.md`
  - `Get-Content docs\PROJECT_STATE.md`
  - `Get-Content README.md -TotalCount 180`
  - `Get-Content pyproject.toml`
  - `Get-Content DESIGN.md`
  - `Get-Content .agent-guardrails\task-contract.json`
  - `Get-Content pro\apps\web\src\main.rs`

- awesome-design-md reference:
  - Read `C:\Users\97504\.codex\skills\awesome-design-md\SKILL.md`
  - Read the local catalog/stub for xAI
  - Fetched the live `https://getdesign.md/x.ai/design-md` page; the reference identifies xAI as stark monochrome and futuristic minimalism. Used it as inspiration only, with RetroCause identity preserved.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Initial result: failed on import ordering after route changes.
  - Follow-up: ran `cargo fmt --manifest-path pro/Cargo.toml --all`.
  - Final result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `40 passed`.
  - Domain tests: `22 passed`.
  - Event-store tests: `6 passed`.
  - Provider-routing tests: `12 passed`.
  - Queue tests: `11 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `3 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed after stopping the temporary local web process that had locked `retrocause-pro-web.exe`.

- Pro browser smoke for `http://127.0.0.1:3007/` and `http://127.0.0.1:3007/graph`
  - Started `retrocause-pro-api.exe` and `retrocause-pro-web.exe` with temporary `.tmp/pro-smoke` run/event stores.
  - Captured screenshots:
    - `D:\opencode\retrocause-ai\.tmp\previews\pro-xai-dialogue-home.png`
    - `D:\opencode\retrocause-ai\.tmp\previews\pro-xai-galaxy-graph.png`
  - Root page verified:
    - title: `RetroCause Pro`
    - dialogue h1: `Map the causes behind any complex event.`
    - `.home-dialogue` opacity reached `1` after entrance animation
    - question form submits to `/graph` with method `get`
    - home star layers: `2`
    - home orbit layers: `2`
    - no provider panel, source panel, queue panel, graph inspector, or graph nodes on the homepage
    - no secret-shaped key/secret/token/password fields
  - Graph page verified:
    - heading: `Causal star map`
    - staged homepage question preserved in the graph console
    - graph nodes: `6`
    - graph wires: `10`
    - star layers: `2`
    - scan layers: `1`
    - provider/source/inspector panels render on `/graph`
    - pointer variables moved to `72%` / `38%`
    - graph scale: `0.672`
    - visible nodes: `6`
    - clipped-right nodes: `0`
    - no console errors
    - no secret-shaped key/secret/token/password fields

- `git diff --check`
  - Result: passed.
  - Git emitted expected CRLF conversion warnings for touched text/Rust files only.

- Sensitive-token scan across changed task files
  - Result: passed. No `sk-*`-style secrets, JWT-shaped tokens, or key/password/token assignments were found.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with score `90/100 (safe-to-deploy)`.
  - Blocking errors: `0`.
  - Non-blocking warnings:
    - The task spans 4 top-level areas: `.agent-guardrails`, `DESIGN.md`, `docs`, and `pro`.
    - `docs/PROJECT_STATE.md` changed as a state file.
  - Disposition: both warnings are intentional for this task. The user explicitly requested an awesome-design-md Pro redesign, the root `DESIGN.md` had to reflect the new design source, the Pro web shell changed, docs had to stay synchronized, and the guardrails contract/evidence had to reflect the final route split.

## Risk / Tradeoff Notes

- This is a Pro web-shell visual/route-structure change only. It does not change backend domain behavior, API semantics, provider routing, queue semantics, storage, credentials, billing, workers, or OSS runtime.
- No Rust, npm, Python, image, icon, font, JavaScript framework, provider, credential, or payment dependencies were added.
- The root page stages a question into `/graph` instead of auto-creating a run. That keeps the homepage cinematic and avoids silently mutating local run storage from a simple landing interaction.
- The graph fit uses CSS transform scaling around the existing graph coordinate system. This keeps existing domain payloads intact, but future graph UX should eventually use a real interactive graph renderer with zoom/pan/collision handling.
- The xAI reference is treated as style inspiration only. The UI keeps RetroCause identity and does not claim or imply external affiliation.

## Remaining Risks

- Real hosted Pro is still not enabled. Tenant auth, vault handles, quota reservations, durable intent persistence, worker leases, provider calls, billing mutation, and result commits remain blocked or preview-only.
- The graph remains a static positioned star map with browser-local selection. Dragging, zoom persistence, collision avoidance, cross-run comparison selection, and deep review workflows remain future client work.
- Guardrails passed with two intentional non-blocking warnings about multi-area docs/evidence scope.
