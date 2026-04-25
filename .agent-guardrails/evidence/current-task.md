# Current Task Evidence

## Task

Add the next Pro hosted intent create-request preview: a keyless, rejected server-side payload that composes denied execution admission, planned intent-store, and worker-lease blockers before any real durable hosted intent store exists.

## Scope

- `pro/crates/queue/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

## What Changed

- Added `ExecutionIntentCreateRequestPreview` and related field/write-step/status types in `crates/queue`.
- Added `execution_intent_create_request_preview(...)`, which composes:
  - the existing server-side execution admission decision
  - the planned execution intent-store boundary
  - the planned worker-lease/retry boundary
  - future request fields and blocked write steps
  - preview idempotency context
- Added keyless `POST /api/execution-intents/create-request` in the Pro API.
- Added a graph-first web action/panel, `Preview intent create request`, that renders create-request rejection, admission denial, disconnected intent store, persistence-off state, no durable intent id, request fields, write plan, blockers, and safeguards.
- Updated project-state and Pro architecture docs so this is documented as a rejected preview contract, not real auth, credential access, quota reservation, durable queue persistence, provider execution, worker execution, billing mutation, or result writing.

## Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all`
  - Result: completed formatting for the new Rust payload/API/Web changes.

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Result: passed.

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

- Pro API hosted intent create-request smoke
  - Started `retrocause-pro-api.exe` on localhost with temporary `RETROCAUSE_PRO_RUN_STORE_PATH` and `RETROCAUSE_PRO_EVENT_STORE_PATH`.
  - Called `GET /healthz`, then `POST /api/execution-intents/create-request`.
  - Result: passed; `create_request_allowed=false`, `intent_persistence_allowed=false`, `execution_allowed=false`, `durable_intent_id_issued=false`, admission stayed denied, intent store stayed disconnected, lease store stayed disconnected, 8 request fields and 4 blocked write steps were returned, and no key-shaped values were found.

- Pro browser hosted intent create-request smoke
  - Started Pro API and web shell on localhost with temporary local store paths.
  - Playwright loaded the graph-first web shell, clicked `Queue preview job`, clicked `Preview intent create request`, and verified the create-request panel rendered `create request rejected`, `admission denied`, `not connected`, `persistence: off`, `none issued`, blocked write steps, and `no durable intent id issued`.
  - Initial result: failed because the web panel sliced safeguards too aggressively and hid the explicit `no_durable_intent_id_issued` safeguard.
  - Fix: expanded the create-request safeguard list so the no-durable-id guard is visible.
  - Final result: passed; no key-shaped text was rendered.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Result: passed. No key-shaped tokens or provider-secret values were found in the diff.

- Local process cleanup check
  - Result: passed; no `retrocause-pro-api` or `retrocause-pro-web` service processes were left running after smoke tests.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with score `95/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the current Pro UX focus, done-recently entry, and next step were synchronized to include the hosted intent create-request preview.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with score `95/100 (safe-to-deploy)`.
  - Non-blocking warning matched the standard check: intentional project-state documentation update.

## Risk / Tradeoff Notes

- Security: this slice does not accept, validate, read, store, log, or return sessions, passwords, JWTs, provider secrets, search keys, connector credentials, payment credentials, auth tokens, admission tokens, vault handles, quota reservation ids, durable intent ids, or user API keys.
- Permissions: this is not hosted tenant auth or production authorization. It reuses the denied admission payload as a prerequisite checklist.
- Secrets: raw provider credentials never enter the payload; request fields name future vault-handle requirements only as metadata.
- Quota/billing: no quota is reserved, no ledger row is written, no payment provider is connected, and no billable usage is emitted.
- Execution: no provider calls, worker execution, worker lease claims, retry scheduling, result-event writes, or snapshot persistence were added.
- Persistence: no Redis/Postgres connection and no durable execution intent persistence were added. The payload deliberately returns `durable_intent_id_issued=false`.
- Dependencies: no new Rust crates, npm packages, Python packages, lockfile changes, Cargo config changes, or dependency upgrades were introduced.
- Performance: the create-request preview is an in-memory composition of existing boundary payloads. It adds no network calls, database calls, Redis calls, file writes, provider calls, or background work.
- Understanding: this defines the future durable intent input contract and duplicate-create/idempotency shape, but it is not real durable persistence and not execution authorization.
- Continuity: reused the existing execution admission payload, execution intent-store boundary, worker-lease boundary, Axum route style, web `fetchJson` helper, and compact graph-first panel patterns. OSS runtime paths remain untouched.

## Remaining Risks

- This is still preview-only and rejected. It is not tenant authentication, not credential-vault integration, not quota reservation, not admission-token issuance, not durable intent persistence, not worker lease claiming, not provider execution, not retry scheduling, not billing enforcement, and not result commit.
- Future hosted Pro should replace this rejected create-request preview with real durable intent creation only after tenant auth, vault handles, quota reservations, lease-store connections, replay-before-claim semantics, retry scheduling, and idempotent result-event commits exist.
- Guardrails standard and review checks passed. The remaining warning is the intentional project-state documentation update.
