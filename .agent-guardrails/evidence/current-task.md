# Current Task Evidence

## Task

Enhance the Pro Rust web shell with an awesome-design-md xAI-inspired visual/effects pass: dialogue-box-first homepage, star-map knowledge graph, and smooth cinematic UI motion while preserving all existing preview-only execution boundaries.

## Scope

- `DESIGN.md`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

## What Changed

- Updated `DESIGN.md` to name the awesome-design-md xAI reference as visual inspiration only, not affiliation, and to document the dialogue-first, star-map, low-cost cinematic-motion rules.
- Strengthened the Pro homepage dialogue surface:
  - label changed to `Ask a causal question`
  - primary action changed to `Map causes`
  - larger prompt textarea and subtle monochrome dialogue glint/sheen
- Enhanced the graph field as a star map:
  - two starfield layers
  - one cinematic scan layer
  - pointer-driven star parallax through CSS custom properties
  - wire-draw reveal using stroke dash offsets
  - staggered node entrance and selected-node glow
- Preserved the existing server-rendered Maud structure, inline browser script pattern, graph selection behavior, API fetch paths, and preview-only provider/queue/admission/intent/storage/vault/quota/event/review panels.
- Updated project-state and Pro architecture docs so the new visual/effects direction stays synchronized with current Pro behavior.

## Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: applied one mechanical Rust formatting change after `cargo fmt --check` identified line wrapping.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed after formatting.

- `cargo test --manifest-path pro/Cargo.toml`
  - Result: passed.
  - API tests: `40 passed`.
  - Domain tests: `22 passed`.
  - Event-store tests: `6 passed`.
  - Provider-routing tests: `12 passed`.
  - Queue tests: `11 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro browser smoke for `http://127.0.0.1:3007/`
  - Started `retrocause-pro-api.exe` and `retrocause-pro-web.exe` with temporary `.tmp/pro-smoke` run/event stores.
  - Playwright loaded the Pro shell, moved the pointer over the graph, captured `D:\opencode\retrocause-ai\.tmp\previews\pro-xai-cinematic-shell.png`, and verified:
    - title: `RetroCause Pro`
    - heading: `Causal star map`
    - question rail label: `Ask RetroCause`
    - prompt label: `Ask a causal question`
    - CTA: `Map causes`
    - star layers: `2`
    - scan layers: `1`
    - graph wires: `5`
    - graph nodes: `6`
    - visible central nodes: `6`
    - graph viewport: `1174 x 734.4375`
    - pointer cinematic variables changed from their defaults
    - no console errors
    - no secret-shaped key/secret/token/password fields rendered

- `git diff --check`
  - Result: passed. Git only emitted expected CRLF conversion warnings for touched text/Rust files.

- Sensitive-token scan across changed task files
  - Result: passed. No `sk-*`-style secrets or JWT-shaped tokens were found.

- Local process cleanup check
  - Result: passed. No `retrocause-pro-api` or `retrocause-pro-web` processes remained after browser smoke.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Pre-commit result: passed with score `90/100 (safe-to-deploy)`.
  - Post-commit result: passed with score `90/100 (safe-to-deploy)`.
  - Non-blocking warnings:
    - The task spans 4 top-level areas: `.agent-guardrails`, `DESIGN.md`, `docs`, and `pro`.
    - `docs/PROJECT_STATE.md` changed as a state file.
  - Disposition: both warnings are intentional because the user requested an awesome-design-md visual pass, the local design source changed, the Pro web shell changed, docs had to stay synchronized, and evidence/contract had to reflect the final scope.

## Risk / Tradeoff Notes

- This is a Pro web-shell visual/effects pass only. It does not change backend domain behavior, API routes, provider routing, queue semantics, storage, credentials, billing, workers, or OSS runtime.
- No Rust, npm, Python, icon, font, image, video, JavaScript framework, remote asset, provider, credential, or payment dependencies were added.
- Motion is deliberately low-cost: CSS opacity/transform/stroke animation plus pointer-driven CSS variables. It respects `prefers-reduced-motion` through the existing global motion override.
- The xAI reference is treated as style inspiration only. The UI keeps RetroCause identity and does not claim or imply external affiliation.
- The UI still exposes many preview-only panels because the current Pro product is boundary-first; this pass improves cinematic hierarchy and graph feel without enabling hosted execution.

## Remaining Risks

- Real hosted Pro is still not enabled. Tenant auth, vault handles, quota reservations, durable intent persistence, worker leases, provider calls, billing mutation, and result commits remain blocked or preview-only.
- The graph remains a static positioned star map. Dragging, zoom persistence, collision avoidance, and deeper graph review interactions remain future client-work.
- Guardrails passed for this visual-effects commit. Remaining warnings are intentional documentation/guardrails scope warnings, not blocking implementation errors.
