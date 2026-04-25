# Current Task Evidence

## Task

Add the Pro execution admission gate: a reusable server-side payload that composes tenant/auth, credential-vault handle, quota reservation, and pre-execution blockers before any real hosted execution intent store is created.

## Scope

- `pro/crates/domain/src/lib.rs`
- `pro/apps/api/src/main.rs`
- `pro/apps/web/src/main.rs`
- `docs/PROJECT_STATE.md`
- `docs/pro-rust-architecture.md`
- `.agent-guardrails/task-contract.json`
- `.agent-guardrails/evidence/current-task.md`

## What Changed

- Added `ExecutionAdmissionRequest`, `ExecutionAdmissionDecision`, `ExecutionAdmissionGate`, and related admission status enums in the Pro domain crate.
- Added `execution_admission(...)`, which composes:
  - server-computed workspace/tenant access gate
  - keyless credential-vault boundary
  - preview-only quota-ledger boundary
  - pre-execution hosted prerequisite boundary
- Added keyless `POST /api/execution-admission` in the Pro API.
- Added a graph-first web action/panel for checking execution admission from the current run.
- Updated project state and Pro architecture docs so this is documented as a denied prerequisite payload, not a real authorization token, vault handle, quota reservation, durable intent, provider execution path, worker path, or result writer.

## Commands Run

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
  - Initial result: failed because rustfmt wanted to reflow new imports and admission payload/test formatting.
  - Fix: ran `cargo fmt --manifest-path pro/Cargo.toml --all`.
  - Final result: passed.

- `cargo test --manifest-path pro/Cargo.toml`
  - Initial result: failed because an over-broad test assertion treated the literal safety phrase `passwords` as a leaked password value.
  - Fix: kept the key-shaped checks for `sk-`, `api_key`, and `bearer` values while allowing guardrail prose that says passwords are not accepted.
  - Final result: passed.
  - API tests: `39 passed`.
  - Domain tests: `22 passed`.
  - Event-store tests: `6 passed`.
  - Provider-routing tests: `12 passed`.
  - Queue tests: `10 passed`.
  - Run-store tests: `4 passed`.
  - Web tests: `2 passed`.

- `cargo build --manifest-path pro/Cargo.toml`
  - Result: passed.

- Pro API execution-admission smoke
  - Started `retrocause-pro-api.exe` on a dynamic localhost port with temporary `RETROCAUSE_PRO_RUN_STORE_PATH` and `RETROCAUSE_PRO_EVENT_STORE_PATH`.
  - Called `GET /healthz`, then `POST /api/execution-admission`.
  - Result: passed; status was `denied_requires_hosted_gates`, `admitted=false`, `execution_allowed=false`, 4 gates were returned, 11 blockers were returned, tenant/auth, vault-handle, quota-reservation, and pre-execution gates were present, and no key-shaped values were found.

- Pro browser execution-admission smoke
  - Started the Pro API and web shell on dynamic localhost ports.
  - Playwright loaded the graph-first web shell, clicked `Check admission gate`, and verified the admission panel rendered `admission denied`, `tenant auth`, `vault handle`, `quota reservation`, and `no provider execution or secret access`.
  - Result: passed; no request failures, console errors, page errors, or key-shaped text were found.

- `git diff --check`
  - Result: passed. Git only emitted CRLF conversion warnings for touched text files.

- Sensitive-token diff scan
  - Initial result: the broad scan reported the literal test assertion text `api_key` / `bearer`.
  - Final refined scan result: passed. No key-shaped tokens, credential assignments, bearer values, or provider-secret assignments were found in the executable diff.

- Local process cleanup check
  - Result: passed; no `retrocause-pro-api` or `retrocause-pro-web` service processes were left running after smoke tests.

- `agent-guardrails check --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with score `95/100 (safe-to-deploy)`.
  - Non-blocking warning: `docs/PROJECT_STATE.md` changed as a state file. This was intentional because the current Pro focus, done-recently entry, and next step were synchronized to include the execution admission gate.

- `agent-guardrails check --review --base-ref HEAD~1 --commands-run "cargo test --manifest-path pro/Cargo.toml"`
  - Result: passed with score `95/100 (safe-to-deploy)`.
  - Non-blocking warning matched the standard check: intentional project-state documentation update.

## Risk / Tradeoff Notes

- Security: this slice does not accept, validate, read, store, log, or return sessions, passwords, JWTs, provider secrets, search keys, connector credentials, payment credentials, auth tokens, admission tokens, or user API keys. It does not enforce hosted permissions or protect hosted resources.
- Dependencies: no new Rust crates, npm packages, Python packages, lockfile changes, Cargo config changes, or dependency upgrades were introduced.
- Performance: the admission payload is an in-memory composition of existing static/domain boundaries. It adds no provider calls, database calls, Redis calls, file writes, quota-ledger writes, billing writes, worker leases, retry scheduling, queue persistence, or result-event writes.
- Understanding: this is a server-computed prerequisite checklist and not a real execution authorization token. It stays denied until hosted tenant auth, vault-handle issuance, quota reservation, worker lease, durable intent storage, and idempotent result commit storage exist.
- Continuity: reused the existing workspace access gate, credential-vault boundary, quota-ledger boundary, pre-execution boundary, Axum route style, web `fetchJson`, and compact graph-first panel patterns. OSS runtime paths remain untouched.

## Remaining Risks

- This is not tenant authentication, not a credential vault, not quota reservation, not an admission token, not durable intent persistence, not worker lease claiming, not provider execution, not billing enforcement, and not result commit.
- Future hosted Pro should replace this denied admission payload with a real admission-to-intent creation path only after real tenant auth, vault handles, quota reservations, lease-store connections, retry scheduling, replay semantics, and idempotent result-event commits exist.
