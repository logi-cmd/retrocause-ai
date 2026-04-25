# RetroCause Pro Rust Architecture

Last updated: 2026-04-25

## Why a separate Rust workspace

The OSS Python/FastAPI + Next.js app remains the inspectable local product. Pro needs a different runtime shape: queueable jobs, durable run records, explicit quota ownership, and more controlled latency under provider pressure. That is a good fit for a separate Rust codebase rather than accreting hosted concerns into the OSS stack.

The Rust rewrite lives under `pro/` inside this repository so the product and architecture can evolve in the open without destabilizing OSS runtime paths.

## Current architecture goals

1. Establish a clean Rust workspace boundary.
 2. Define shared Pro domain types around graph-first runs, evidence anchors, challenge checks, source health, usage ledger entries, provider quota ownership, and cooldown state.
3. Stand up API endpoints that expose run summaries, run detail, graph payloads, file-backed local run creation, run-scoped local event replay, preview-only worker result dry-runs, result snapshot readiness gates, worker result commit intents, workspace access-gate decisions, composed execution-readiness decisions, reusable execution admission decisions, hosted intent create-request previews, pre-execution auth/vault/quota boundaries, keyless provider/search quota status, routing previews, preview-only execution jobs, execution handoff previews, execution intent previews, and a planned execution intent-store boundary.
4. Render a graph-first web shell from the same shared Rust payload and wire it to the local API create/read flow, provider-status view, execution-readiness panel, execution-admission panel, hosted intent create-request panel, pre-execution boundary panel, execution handoff preview panel, execution intent preview panel, and execution intent-store boundary panel.
5. Keep Pro separate from the OSS Python/FastAPI + Next.js runtime.

## Workspace layout

```text
pro/
  Cargo.toml
  apps/
    api/
    web/
  crates/
    domain/
    event-store/
    provider-routing/
    queue/
    run-store/
```

## Stack choice

### API

- `axum`
- `tokio`
- `serde`

Reason: small, explicit, good fit for future queue, cache, and run-record services.

### Web

- `axum`
- `maud`
- shared Rust domain crate

Reason: the first Pro shell wants a graph-first surface that compiles quickly and keeps the Rust web path simple. Server-rendered HTML gives us a real interface immediately without committing to a WASM/hydration stack too early.

This is a deliberate tradeoff:

- good now: faster iteration, fewer moving parts, easier first compile/test path
- deferred: richer client-side graph interaction, drag behavior, zoom state persistence, incremental hydration

If the graph workspace proves out, the next phase can move the web shell toward Leptos or another Rust-heavy client strategy without changing the domain model or API boundary.

## Shared domain

The first shared crate now defines:

- a `ProRun` payload
- run summaries
- graph nodes
- graph edges
- evidence anchors
- challenge checks
- source status cards
- usage ledger entries
- provider/search quota ownership entries
- workspace access context entries
- workspace access-gate decision entries
- credential-vault boundary entries
- quota-ledger and billing boundary entries
- result-commit and event-store boundary entries
- run event timeline and status vocabulary entries
- review-comparison payloads for evidence and challenge deltas
- source cooldown state
- verification steps
- an owned `CreateRunRequest` builder for process-local alpha run creation
- a canonical seed run used by both the API and the web shell

This keeps the API and web kickoff honest: they render the same shape instead of drifting into two separate demos.

The workspace access context is deliberately non-enforcing in this slice. It names the demo workspace, preview actor, preview-allowed actions, actions that require real auth later, and safeguards such as no sessions, no cookie issuance, no token validation, no credential reads, and no billing/quota mutation. It is an inspectable contract, not a login system.

The workspace access gate is also deliberately local and keyless in this slice. It evaluates a requested Pro action against the same preview workspace/actor context, allows only preview-safe actions such as graph inspection or preview-run creation, denies live/provider/worker/write actions, and returns blockers plus sensitive-data rules without accepting passwords, sessions, tokens, provider keys, or external auth assertions.

The credential-vault boundary is deliberately keyless and disconnected in this slice. It names future credential classes, metadata-only visibility, worker-scoped access requirements, rotation ownership, and safeguards while returning `secret_values_returned=false` and `connections_enabled=false`.

The quota-ledger and billing boundary is deliberately preview-only in this slice. It names future quota lanes, metering rules, rate-limit rules, payment-provider absence, and billing safeguards while returning `ledger_mutation_enabled=false`, `payment_provider_connected=false`, and no billable usage.

The result-commit and event-store boundary is deliberately preview-only in this slice. It names future commit stages, event write rules, and partial-result reconciliation rules while returning `event_store_connected=false`, `commit_writes_enabled=false`, and `partial_reconciliation_enabled=false`.

The run event timeline remains derived from the current `ProRun` record through `GET /api/runs/{run_id}/events`. A separate local event-store slice now persists that derived stream into a run-scoped JSON file for local replay through `GET /api/runs/{run_id}/event-log` and `GET /api/runs/{run_id}/event-replay`. This is local inspectability storage, not a hosted audit log, worker queue, or provider-result commit path.

The worker result dry-run is also deliberately preview-only. It uses the local replay stream as input and returns proposed result-commit steps, commit checks, and safeguards while keeping `execution_allowed=false`, `provider_execution_allowed=false`, `result_commit_allowed=false`, and `result_event_write_allowed=false`.

The result snapshot readiness gate is also deliberately preview-only. It derives a proposed non-persisted snapshot from the worker-result dry-run/local replay path, reports the hosted safety checks that still block persistence, and keeps `snapshot_persistence_allowed=false`, `result_event_write_allowed=false`, and `provider_execution_allowed=false`.

The worker result commit intent is also deliberately preview-only. It derives a rejected commit envelope from result snapshot readiness, exposes the preview idempotency key, future event writes, hosted blockers, and commit safeguards, and keeps `commit_allowed=false`, `result_event_write_allowed=false`, `snapshot_persistence_allowed=false`, and `provider_execution_allowed=false`.

The review comparison payload is also deliberately derived in this slice. It compares the current run to a generated previous-checkpoint preview and reports evidence/challenge deltas so the graph-review workflow has a concrete shape before durable run history, tenant auth, or cross-run selectors exist.

## Run store boundary

`crates/run-store` is the first Pro storage boundary. It currently provides a local JSON file-backed `FileRunStore` around `ProRun` records.

Current behavior:

- default path: `.retrocause/pro_runs.json`
- override: `RETROCAUSE_PRO_RUN_STORE_PATH`
- first open seeds the canonical sample run
- created runs are written to disk and survive API process restarts
- the API no longer owns raw `HashMap` or sequence state directly

This is intentionally an alpha local store. It is not encrypted storage, not a multi-tenant database, not a credential vault, and not the final hosted Pro persistence layer. The value is the boundary: future Postgres-backed storage should replace this crate's implementation without forcing the API routes to own storage details again.

`crates/run-store` also carries a no-connection hosted storage migration plan. It names the intended Postgres run/evidence/usage tables, Redis execution/cooldown queues, tenant and actor boundaries, row-level policy expectations, audit metadata, and worker-owned lease/credential responsibilities before any hosted store is connected.

## Event store boundary

`crates/event-store` is the first local event replay boundary. It currently provides a JSON file-backed `FileEventStore` around run-scoped event streams derived from `ProRun` records.

Current behavior:

- default path: `.retrocause/pro_events.json`
- override: `RETROCAUSE_PRO_EVENT_STORE_PATH`
- first API open persists replay events for the canonical seed run when that run exists
- `POST /api/runs` persists the created run's initial replay stream
- `GET /api/runs/{run_id}/event-log` returns the persisted entries for the requested run
- `GET /api/runs/{run_id}/event-replay` returns replay metadata, durable-local mode, event count, entries, and safeguards
- `POST /api/runs/{run_id}/worker-result-dry-run` derives proposed result commit steps from local replay without writing result events
- `POST /api/runs/{run_id}/result-snapshot-readiness` derives a non-persisting snapshot readiness gate from the worker result dry-run without writing result events
- `POST /api/runs/{run_id}/worker-result-commit-intent` derives a rejected worker-owned commit intent from snapshot readiness without writing result events or persisting snapshots

This is intentionally local-only alpha storage. It is not Postgres, Redis, a hosted tenant audit log, a worker event queue, a credential vault, or a provider result committer. The tradeoff is that read endpoints can initialize a missing local stream for a known run so restart continuity and replay UX stay deterministic; the worker result dry-run, snapshot readiness gate, and commit intent can then preview the commit envelope from that replay without mutating the run. Future hosted Pro should replace that with explicit worker-owned event writes once auth, quota, vault, worker leases, and result commits exist.

## Provider routing boundary

`crates/provider-routing` is the first Pro provider/source routing boundary. It currently produces a route preview plan from the static keyless provider-status payload.

Current behavior:

- input: workspace id, query, optional scenario, optional source policy
- output: preview-only route plan with lane decisions, cooldown hints, selected local lane, and warnings
- execution: always disabled in this slice
- selected local fallback: uploaded-evidence lane when the source policy allows it
- explicit blocked/deferred lanes: managed Pro model pool, workspace search, BYOK-later search, and market-search cooldown

This is intentionally not a provider executor. It does not read provider keys, call models/search APIs, enqueue jobs, bill usage, or store credentials. The value is the decision vocabulary: future executors can consume the same lane and decision semantics instead of inventing hidden routing behavior inside provider adapters.

`crates/provider-routing` also carries a dry provider-adapter contract, a non-executing adapter dry-run shape, the first gated live-adapter candidate, and a composed execution-readiness gate. The contract names the future adapter request fields, result fields, degradation states, quota guards, and partial-result rules before any provider implementation exists. The dry-run accepts a workspace id, query, provider lane, and source policy, then returns preview evidence, zero-billable usage ledger rows, visible degradation states, and safety warnings without reading credentials or calling providers. The OfoxAI model adapter candidate is registration-only: gate checks can show that dry-run, auth context, quota ownership, and event timeline previews were observed, but execution remains denied until real tenant auth, credential vault reads, quota ledger enforcement, and worker execution exist. The execution-readiness gate composes that provider gate with workspace access, worker commit, snapshot persistence, and observed-preview prerequisites so the future live execution path has one explicit denial payload before provider calls, credential reads, quota reservations, worker execution, or result writes are enabled. These shapes require explicit quota ownership, retry-after cooldown visibility, degraded source states, usage ledger rows, and evidence preservation before retries.

`crates/domain` also carries a pre-execution boundary that sits one step closer to the future hosted executor. It names the hosted tenant auth context, server workspace gate, credential-vault handle, quota reservation, durable worker lease, and idempotent result commit as blocking prerequisites. This is deliberately metadata-only: it does not accept sessions, passwords, JWTs, provider keys, or connector credentials; it does not issue vault handles, reserve quota, claim worker leases, call providers, mutate billing, or write results. The value is the shared handoff vocabulary future executors must consume before real calls can exist.

`crates/domain` also carries a reusable server-side execution admission payload. It composes the workspace/tenant auth gate, credential-vault boundary, quota-ledger boundary, and pre-execution boundary into a single denied decision with explicit gates, blockers, safeguards, and sensitive-data rules. This is not an authorization token and not a live executor: it does not issue admission tokens, read or return credentials, issue vault handles, reserve quota, mutate billing, persist queue intents, claim workers, call providers, or write result events. The value is the final server-computed prerequisite checklist before future hosted intent creation.

`crates/queue` now carries the hosted intent create-request preview that consumes that denied admission decision plus the planned intent-store and worker-lease boundaries. It returns the future durable-intent input contract, preview idempotency key, blocked write plan, combined blockers, and safeguards while keeping `create_request_allowed=false`, `intent_persistence_allowed=false`, `execution_allowed=false`, and `durable_intent_id_issued=false`. This is not durable persistence or execution authorization: it does not accept or return passwords, sessions, JWTs, provider keys, admission tokens, vault handles, quota reservation ids, or durable intent ids, and it does not connect Redis/Postgres, mutate billing/quota, claim workers, call providers, or write result events.

## Queue boundary

`crates/queue` is the first Pro execution-queue boundary. It currently provides an in-memory `ExecutionQueue` that turns a routing-preview request into a preview-only execution job.

Current behavior:

- input: the same workspace id, query, scenario, and source policy accepted by provider-routing preview
- output: execution job payload with id, workspace id, query, preview-only status, selected lane, and the full route plan
- worker contract: a non-executing work-order payload with route steps, routing warnings, selected lane, and explicit safeguards
- lifecycle contract: a non-executing hosted-worker stage/failure taxonomy that names future queue, worker, provider, partial-result, and terminal states before adapters exist
- worker lease/retry contract: a non-executing lease, retry, and idempotency boundary that names claim rules, retry policies, duplicate-call prevention, and partial-result preservation before workers exist
- execution handoff preview: a denied handoff payload that composes each job's work order with the pre-execution auth/vault/quota/worker/result boundary
- execution intent preview: a rejected intent envelope that composes the denied handoff with worker lease/retry rules and preview idempotency keys
- execution intent-store boundary: a planned durable store contract that names transition rules, idempotency requirements, retention rules, and replay-before-claim semantics while persistence remains disabled
- hosted intent create-request preview: a rejected server-side create request shape that composes denied admission, planned intent-store rules, worker-lease rules, future request fields, blocked write steps, and a preview idempotency key before any durable intent store exists
- storage: process-local memory only
- execution: always disabled in this slice

This is intentionally not a worker system. It does not read provider keys, call models/search APIs, persist queue state, bill usage, enforce tenant quotas, claim leases, connect an intent store, persist execution intents, or schedule background work. The value is the API, state, work-order, worker-lease, retry, handoff, intent, intent-store, and create-request boundary: future Redis/Postgres-backed queue workers should replace the in-memory implementation without making API routes own job sequencing, route-plan coupling, retry loops, idempotency semantics, pre-execution gate composition, intent persistence, replay semantics, or safety gate behavior.

## Near-term service split

### `apps/api`

Initial responsibility:

- health endpoint
- seed graph endpoint retained for compatibility
- `GET /api/runs`
- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/graph`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/event-log`
- `GET /api/runs/{run_id}/event-replay`
- `POST /api/runs/{run_id}/worker-result-dry-run`
- `POST /api/runs/{run_id}/result-snapshot-readiness`
- `POST /api/runs/{run_id}/worker-result-commit-intent`
- `GET /api/runs/{run_id}/review-comparison`
- `GET /api/workspace/access-context`
- `POST /api/workspace/access-gate`
- `GET /api/credential-vault-boundary`
- `GET /api/quota-ledger-boundary`
- `GET /api/result-commit-boundary`
- `GET /api/execution-preflight-boundary`
- `GET /api/provider-status`
- `GET /api/provider-adapter-contract`
- `GET /api/provider-adapter/candidates`
- `POST /api/provider-adapter/gate-check`
- `POST /api/provider-adapter/dry-run`
- `POST /api/execution-readiness`
- `POST /api/execution-admission`
- `POST /api/execution-intents/create-request`
- `GET /api/provider-route/preview`
- `POST /api/provider-route/preview`
- `GET /api/execution-jobs`
- `POST /api/execution-jobs`
- `GET /api/execution-jobs/{job_id}`
- `GET /api/execution-jobs/{job_id}/work-order`
- `GET /api/execution-jobs/{job_id}/handoff-preview`
- `GET /api/execution-jobs/{job_id}/intent-preview`
- `GET /api/execution-intent-store-boundary`
- `GET /api/execution-lifecycle`
- `GET /api/worker-lease-boundary`
- `GET /api/storage-plan`
- minimal local CORS headers for the separate Pro web port
- local JSON run storage through `crates/run-store`, shared by list/detail/graph reads and surviving API restarts
- local JSON event replay storage through `crates/event-store`, shared by seed/create-run writes plus run-scoped event-log/replay reads
- preview-only worker result dry-runs through `crates/event-store`, derived from local replay and blocked from result-event writes
- preview-only result snapshot readiness gates through `crates/event-store`, derived from worker result dry-runs and blocked from snapshot persistence
- preview-only worker result commit intents through `crates/event-store`, derived from snapshot readiness and blocked from result-event writes plus snapshot persistence
- local preview workspace access-gate decisions through `crates/domain`, blocking live/provider/worker/write actions until hosted auth, vault, quota, worker, and idempotent storage gates exist
- keyless pre-execution boundary decisions through `crates/domain`, blocking live execution until hosted auth, vault-handle issuance, quota reservation, worker lease, and idempotent result commit prerequisites exist
- keyless execution admission decisions through `crates/domain`, composing tenant/auth, vault-handle, quota-reservation, and preflight blockers into one reusable denied server-side payload before intent creation
- keyless hosted intent create-request previews through `crates/queue`, composing denied admission, planned intent-store, worker-lease, future request-field, write-plan, and idempotency blockers before durable intent creation exists
- composed execution-readiness decisions through `crates/provider-routing`, combining workspace, provider, worker, snapshot, and observed-preview blockers before any live execution path can be enabled
- no-connection hosted storage migration plan through `crates/run-store`
- local preview-only queue jobs through `crates/queue`, shared by list/detail reads while the API process is running
- local execution handoff previews through `crates/queue`, composing job work orders with the pre-execution boundary while execution remains denied
- local execution intent previews through `crates/queue`, composing denied handoffs with worker lease rules, preview idempotency keys, and intent-persistence blockers while execution remains denied
- planned execution intent-store boundaries through `crates/queue`, exposing future transition, idempotency, retention, and replay-before-claim rules while durable persistence remains disconnected
- future home for durable run status, queue control, provider routing, cooldown buckets, and saved-run access

The current run and event stores are intentionally local-file-backed. They are useful for proving the API behavior, graph payload contract, restart continuity, and local event replay, but they should not be treated as the hosted Pro data layer. The workspace access context, workspace access gate, credential-vault boundary, quota-ledger boundary, result-commit boundary, pre-execution boundary, execution-admission decision, hosted intent create-request preview, derived run-events, local event-log/replay, worker result dry-run, result snapshot readiness, worker result commit intent, review-comparison, provider-status, provider-route preview, execution-readiness, execution-job, execution handoff preview, execution intent preview, execution intent-store boundary, lifecycle, worker-lease, and storage-plan endpoints are static/keyless in this slice: they model tenant/auth vocabulary, credential handling vocabulary, quota/billing vocabulary, result/event commit vocabulary, snapshot-persistence vocabulary, run status vocabulary, replay vocabulary, review delta vocabulary, ownership, cooldown, routing semantics, readiness semantics, execution preconditions, admission semantics, create-request semantics, queue shape, worker handoff blockers, worker states, retry/idempotency semantics, intent-store semantics, and storage boundaries without exposing credential fields, mutating quota/billing state, connecting a payment provider, opening database/Redis connections, enforcing auth, issuing admission tokens, returning vault handles, returning quota reservation ids, claiming worker leases, persisting execution intents, scheduling retries, or calling real providers. Only the local event-log/replay endpoints write derived run-scoped events to the local JSON replay file; result-commit/provider/worker result dry-run/result snapshot readiness/worker result commit intent/workspace access-gate/execution-readiness/execution-admission/execution-intents/create-request/execution-preflight/execution-handoff/execution-intent/execution-intent-store routes still cannot write provider result events, persisted snapshots, credentials, sessions, quota rows, admission tokens, vault handles, quota reservations, or durable execution intents. The CORS behavior is local-alpha plumbing for `127.0.0.1` API/web development, not a production auth or permission boundary.

### `apps/web`

Initial responsibility:

- render the graph-first Pro workspace
- visualize the canonical run, including evidence anchors, challenge checks, source health, and usage ledger state
- create new in-memory runs through `POST /api/runs`
- reload run summaries, run detail, and graph payloads from the Pro API
- render the non-enforcing workspace/auth context from `GET /api/workspace/access-context`
- check the server-side preview workspace access gate through `POST /api/workspace/access-gate`, showing allow/deny status, blockers, safeguards, and sensitive-data rules before live execution exists
- render the planned credential-vault boundary from `GET /api/credential-vault-boundary`, showing credential classes, blocked access rules, and safeguards without showing values
- render the planned quota-ledger/billing boundary from `GET /api/quota-ledger-boundary`, showing quota lanes, metering rules, and billing safeguards without writing usage or connecting payment infrastructure
- render the planned result-commit/event-store boundary from `GET /api/result-commit-boundary`, showing commit stages, event write rules, partial-result reconciliation, and safeguards without writing durable events
- render the pre-execution boundary from `GET /api/execution-preflight-boundary`, showing hosted auth, vault-handle, quota-reservation, worker-lease, and idempotent-commit blockers without collecting credentials or enabling execution
- render a non-durable run event timeline from `GET /api/runs/{run_id}/events`
- render durable local event replay from `GET /api/runs/{run_id}/event-replay`, showing replay mode, event count, persisted entries, and replay safeguards
- run a preview-only worker result dry-run through `POST /api/runs/{run_id}/worker-result-dry-run`, showing proposed result steps, commit checks, blocked writes, and dry-run safeguards
- check preview-only result snapshot readiness through `POST /api/runs/{run_id}/result-snapshot-readiness`, showing proposed non-persisted snapshot metadata, blockers, and safeguards
- prepare a rejected preview-only worker result commit intent through `POST /api/runs/{run_id}/worker-result-commit-intent`, showing idempotency key preview, future event writes, blockers, and commit safeguards
- render a derived review-comparison panel from `GET /api/runs/{run_id}/review-comparison`, showing evidence/challenge deltas and preview safeguards
- show provider/search quota ownership, credential policy, and cooldown status through the local provider-status payload
- render the dry provider-adapter request/result/degradation contract from `GET /api/provider-adapter-contract`
- run a keyless provider-adapter dry-run through `POST /api/provider-adapter/dry-run`, showing zero billable units, evidence-preview count, degradation states, and calls-disabled state
- render the gated live-adapter candidate catalog from `GET /api/provider-adapter/candidates`
- run a denied live-adapter gate check through `POST /api/provider-adapter/gate-check`, showing which auth, quota, dry-run, event, vault, and worker gates block execution
- run a composed execution-readiness check through `POST /api/execution-readiness`, showing observed preview prerequisites plus workspace, provider, worker, and snapshot blockers before future live execution exists
- run a reusable execution-admission check through `POST /api/execution-admission`, showing tenant/auth, vault-handle, quota-reservation, and preflight blockers before hosted intent creation exists
- create and list preview-only execution jobs through the local execution-job API
- inspect queued job work orders through `GET /api/execution-jobs/{job_id}/work-order`, rendering route steps, routing warnings, selected lane, and execution safeguards while execution stays disabled
- inspect denied execution handoff previews through `GET /api/execution-jobs/{job_id}/handoff-preview`, rendering preflight blockers, work-order blockers, and handoff safeguards without enabling worker execution
- inspect rejected execution intent previews through `GET /api/execution-jobs/{job_id}/intent-preview`, rendering intent idempotency preview, worker-lease blockers, required capabilities, and safeguards without persisting intents
- render the planned execution intent-store boundary from `GET /api/execution-intent-store-boundary`, showing transition, idempotency, retention, and replay-before-claim rules while durable persistence stays disconnected
- render the hosted-worker lifecycle/failure taxonomy from `GET /api/execution-lifecycle` so future execution states are visible before live adapters exist
- render the worker-lease/retry boundary from `GET /api/worker-lease-boundary`, showing lease rules, retry policies, idempotency keys, and safeguards while workers and retry scheduling stay disabled
- render the hosted storage migration boundaries from `GET /api/storage-plan` so Postgres/Redis/tenant/worker ownership is visible before connections exist
- keep a browser-local selected-node state and graph inspector for evidence/challenge links, including focused evidence/challenge review items
- establish layout, palette, and information hierarchy for the knowledge-graph experience

## Future crates after the kickoff

- `crates/export`
- `crates/evidence-store`

`crates/run-store`, `crates/event-store`, `crates/provider-routing`, and `crates/queue` exist today. The other crates are intentionally not created yet; each should appear only when it removes real duplication or isolates a concrete boundary.

## Operational architecture direction

### Planned control plane

- Postgres for durable runs, evidence metadata, exports, and quota ledger
- Redis for queue coordination, cooldown state, and rate-limit buckets
- Worker processes for retrieval, extraction, graph synthesis, export, and scheduled reruns

### Run lifecycle direction

- `queued`
- `running`
- `cooling_down`
- `partial_live`
- `needs_followup`
- `ready_for_review`
- `blocked`

### Key ownership direction

- managed Pro quota
- workspace-managed quota
- BYOK
- uploaded-evidence only / local-only data

Those semantics should remain explicit in both API payloads and the graph workspace UI.

The current `POST /api/runs` path uses `queued` runs and managed/user-provided quota labels without calling model or search providers. The current `GET /api/provider-status` path exposes static ownership lanes for managed Pro quota, workspace-managed search quota, BYOK-later search, uploaded-evidence-only input, and an example market-search cooldown bucket. The current `POST /api/execution-jobs` path records a preview-only queue job from the routing plan, `GET /api/execution-jobs/{job_id}/work-order` exposes the non-executing work-order contract a future worker should consume, `GET /api/execution-jobs/{job_id}/handoff-preview` composes that work order with the pre-execution boundary so auth, vault, quota, worker lease, idempotent commit, and work-order execution blockers are visible before any worker handoff exists, and `GET /api/execution-jobs/{job_id}/intent-preview` derives a rejected execution-intent envelope with preview ids, worker lease blockers, and idempotency context before any durable queue intent exists. Live provider credentials, BYOK storage, workspace quotas, real cooldown enforcement, durable execution-intent persistence, and real worker execution remain future work.

The current `GET /api/workspace/access-context` path exposes a static local preview actor and permission vocabulary. It does not authenticate, authorize, issue sessions, validate tokens, store credentials, mutate billing/quota, or protect hosted resources. Future auth work should replace this preview context with real tenant and actor resolution before any provider execution is enabled.

The current `POST /api/workspace/access-gate` path evaluates a requested action against that preview context. It allows preview-safe actions, denies unknown workspaces, denies live provider calls, credential management, billing/quota viewing, worker result commits, and snapshot persistence until hosted auth and worker-owned gates exist. It does not accept passwords, tokens, sessions, provider credentials, or external auth claims, and it does not protect hosted resources yet. Future hosted Pro should make provider execution, credential reads, quota reservations, worker leases, and result commits consume this gate after real tenant/actor resolution exists.

The current `GET /api/credential-vault-boundary` path exposes planned credential classes, access rules, rotation rules, and safeguards. It does not accept credential input, read or store secrets, open a vault connection, return values, or enable workers. Future hosted Pro should replace it with metadata-only vault status after auth, quota ledger, and worker leases exist.

The current `GET /api/quota-ledger-boundary` path exposes planned quota lanes, metering rules, rate-limit rules, and billing safeguards. It does not write ledger rows, reserve quota, connect a payment provider, emit billable usage, enforce limits, or enable provider execution. Future hosted Pro should replace it with tenant-scoped quota reservations and billing policy checks after auth, vault, event-store, and worker leases exist.

The current `GET /api/worker-lease-boundary` path exposes planned worker-lease, retry, and idempotency rules. It does not start workers, claim leases, connect a lease store, schedule retries, read credentials, mutate quota/billing, or call providers. Future hosted Pro should replace it with durable lease claims, bounded retry scheduling, duplicate-call prevention, and partial-result reconciliation after tenant auth, quota reservations, vault access, and event-store writes exist.

The current `GET /api/result-commit-boundary` path exposes planned result-commit stages, event write rules, partial-result reconciliation rules, and safeguards. It does not write provider result events, mutate run state, claim worker leases, read credentials, reserve quota, or call providers. Future hosted Pro should replace it with worker-owned durable result/event commits after tenant auth, quota reservations, vault access, idempotent worker commits, and storage boundaries exist.

The current `GET /api/runs/{run_id}/events` path derives a non-durable timeline from the run record. `GET /api/runs/{run_id}/event-log` and `GET /api/runs/{run_id}/event-replay` persist and replay that run-scoped stream through the local JSON event-store. `POST /api/runs/{run_id}/worker-result-dry-run` uses that replay as input and returns proposed result commit steps without result-event writes. `POST /api/runs/{run_id}/result-snapshot-readiness` uses that dry-run shape to show why persisted result snapshots remain blocked. `POST /api/runs/{run_id}/worker-result-commit-intent` derives the next rejected worker-owned commit envelope, including idempotency key preview and future event-write blockers, without committing anything. This is useful for local replay UX, restart continuity, commit-flow shaping, snapshot gate visibility, and idempotency planning, but it is not a hosted audit log, not a worker status queue, not a persisted result snapshot, and not proof that provider result commits are safe. Future hosted Pro should replace or supplement it with tenant-scoped event-store rows once auth, quota reservations, worker leases, vault access, idempotency checks, and storage boundaries exist.

The current `GET /api/runs/{run_id}/review-comparison` path derives a previous-checkpoint preview from the requested run and reports evidence/challenge deltas. It is useful for shaping graph-review UI, but it is not a durable comparison against another tenant-scoped run. Future hosted Pro should replace the derived baseline with explicit run selection after auth and durable history exist.

The current `GET /api/provider-adapter/candidates` and `POST /api/provider-adapter/gate-check` paths register and inspect a future OfoxAI model adapter candidate. They do not execute the candidate. Even if preview gates are marked observed, the gate check returns `execution_allowed=false` until real auth enforcement, credential vault access, quota ledger enforcement, and worker execution are implemented.

The current `POST /api/execution-readiness` path is the first composed readiness checkpoint for future live execution. It accepts only observation booleans and local ids, then combines the workspace access gate, provider-adapter gate check, worker-result commit gate, and snapshot-persistence gate into one denial payload. It does not execute providers, read credentials, reserve quota, mutate billing, start workers, write result events, or persist snapshots. Future hosted Pro should make provider execution and worker result commits pass this composed checkpoint after real tenant auth, vault handles, quota reservations, worker leases, and idempotent event writes exist.

The current `POST /api/execution-admission` path is the reusable server-side admission payload that sits immediately before future hosted intent creation. It accepts local ids plus a requested action, then combines the workspace/tenant auth gate, credential-vault handle requirement, quota-reservation requirement, and pre-execution boundary into one denied decision. It does not issue admission tokens or capabilities, read credentials, issue vault handles, reserve quota, mutate billing, persist execution intents, claim workers, call providers, or write result events.

The current `POST /api/execution-intents/create-request` path is the rejected hosted intent create-request preview that consumes the denied admission decision plus the planned intent-store and worker-lease boundaries. It returns the future request-field contract, blocked write plan, preview idempotency key, combined blockers, and safeguards. It does not issue or accept admission tokens, vault handles, quota reservation ids, provider credentials, sessions, passwords, JWTs, or durable intent ids; it does not connect Redis/Postgres, persist execution intents, mutate quota/billing, claim workers, call providers, schedule retries, write result events, or authorize execution.

The current `GET /api/execution-preflight-boundary` path exposes the hosted prerequisites that must exist before any live execution handoff. It reports tenant auth, server workspace gate, vault-handle, quota-reservation, worker-lease, and idempotent-commit requirements as blocking. It does not accept or validate sessions, passwords, JWTs, provider keys, connector credentials, or auth claims; it does not issue handles, reserve quota, claim worker leases, call providers, mutate billing, or write results. Future hosted Pro should make the execution worker handoff consume this boundary before live calls can be queued.

The current `GET /api/execution-jobs/{job_id}/handoff-preview` path exposes the next denied handoff envelope for a preview-only queue job. It returns the job work order, the pre-execution boundary, combined blocking reasons, combined safeguards, and the next required hosted step. It does not create leases, start workers, reserve quota, read vault handles, call providers, persist results, or mutate queue state. Future hosted Pro should turn this preview into an execution intent only after real auth, vault handles, quota reservations, worker leases, and idempotent result commits exist.

The current `GET /api/execution-jobs/{job_id}/intent-preview` path exposes the next rejected intent envelope for a preview-only queue job. It returns the denied handoff preview, worker lease boundary, preview intent id, preview idempotency key, required lease capabilities, combined blockers, and safeguards. It does not persist a queue intent, create leases, start workers, reserve quota, read vault handles, call providers, schedule retries, persist results, or mutate queue state. Future hosted Pro should replace this preview with durable intent creation only after real auth, vault handles, quota reservations, lease store connections, retry scheduling, and idempotent result commits exist.

## Knowledge-graph UI direction

The Pro UI should feel like a graph command room, not a generic SaaS dashboard and not a direct carry-over from the OSS evidence board.

- dark, calm, editorial surfaces
- graph canvas as the largest area
- supporting detail revealed through overlays, trays, and inspectors instead of inherited side rails
- visible source states and challenge status
- no gradient-heavy AI dashboard styling

The kickoff web shell encodes that direction with a graph workspace that now supports browser-local node selection, an inspector for the active node's evidence/challenge links, focused evidence/challenge review items, provider quota status, derived review comparison, and preview-only execution-job status. Advanced interaction such as persisted layout state, graph editing, multi-select, and durable cross-run review workflows remains later work.

The current web shell is still intentionally lightweight: server-rendered HTML plus a small browser script for local API calls and DOM refresh. It is enough to prove the Pro run loop without committing to the eventual interactive graph client stack.

## Verification for this kickoff

- `cargo test --manifest-path pro/Cargo.toml`

That is enough for the kickoff because there is no deployment pipeline, persistence layer, or browser runtime yet.

The in-memory run-creation slice also uses:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`

The web/API wiring slice additionally uses a local browser smoke that starts `retrocause-pro-api.exe` and `retrocause-pro-web.exe`, submits the web create-run form, and verifies that the page reloads the API graph payload for the created run.

The provider-status slice adds focused unit coverage under:

- `cargo test --manifest-path pro/Cargo.toml`

The tests assert that quota ownership remains explicit, the static cooldown bucket is visible, and provider-status payloads do not contain API-key or secret-shaped fields.

The graph-interaction slice adds the same Rust test command plus a Playwright smoke that clicks a graph node and verifies that the inspector switches to the selected node while keeping only one node selected.

The run-store slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API restart smoke with `RETROCAUSE_PRO_RUN_STORE_PATH` proving a created run can be read after the API process restarts

The provider-routing slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/provider-route/preview` proving the response stays `preview_only`, does not allow execution, includes five lane decisions, and selects only the local uploaded-evidence lane

The queue-boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/execution-jobs`, `GET /api/execution-jobs`, and `GET /api/execution-jobs/{job_id}` proving created jobs stay preview-only, do not allow execution, and expose the selected local routing lane

The queue-status web slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- a browser smoke that starts the Pro API and web shell, clicks `Queue preview job`, and verifies that the execution queue panel shows a `job_local_*` preview job with execution off

The graph-review focus slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- a browser smoke that clicks an inspector evidence link and verifies that the corresponding evidence item receives browser-local focus state

The executor-contract slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/execution-jobs/{job_id}/work-order` proving the work order remains preview-only, includes route steps, and carries explicit safeguards

The route-step visibility web slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- a browser smoke that starts the Pro API and web shell, clicks `Queue preview job`, and verifies that the work-order detail panel shows route steps, the selected uploaded-evidence lane, and explicit disabled-execution safeguards

The worker-lifecycle contract slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/execution-lifecycle` proving the contract stays non-executing, includes worker/provider failure states, and keeps credential access behind future vault-owned workers
- a browser smoke that starts the Pro API and web shell and verifies that the lifecycle panel renders hosted worker stages and failure states without enabling execution

The storage-boundary contract slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/storage-plan` proving the plan keeps connections disabled while naming Postgres, Redis, tenant, and worker-ownership boundaries
- a browser smoke that starts the Pro API and web shell and verifies that the storage-boundary panel renders target stores and connection-disabled state

The provider-adapter contract slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/provider-adapter-contract` proving the contract stays non-executing while naming request/result fields, quota guards, degradation states, and partial-result rules
- a browser smoke that starts the Pro API and web shell and verifies that the adapter contract panel renders provider lane fields, rate-limit degradation, and calls-disabled state

The provider-adapter dry-run slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/provider-adapter/dry-run` proving the dry-run stays non-executing, returns zero billable units, preserves explicit provider lane/quota ownership, and exposes degradation warnings
- a browser smoke that starts the Pro API and web shell, clicks `Dry-run adapter`, and verifies that the adapter dry-run panel renders dry-run-only mode, calls-disabled state, zero billable units, and degradation states

The workspace/auth boundary preview slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/workspace/access-context` proving the context stays non-enforcing, shows preview and gated permissions, and names auth safeguards
- a browser smoke that starts the Pro API and web shell and verifies that the workspace access panel renders the preview actor, preview permissions, gated provider execution, and safeguards

The workspace access-gate slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/workspace/access-gate` proving preview graph inspection is allowed while provider execution, worker result commits, and unknown workspaces are denied without accepting secrets
- a browser smoke that starts the Pro API and web shell, clicks `Check access gate`, and verifies that the gate panel renders server-computed allow/deny status, blockers, safeguards, and sensitive-data rules

The run event/status vocabulary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/runs/{run_id}/events` proving the timeline is derived from the run record, non-durable, and includes status vocabulary plus event-store safeguards
- a browser smoke that starts the Pro API and web shell and verifies that the run event timeline renders current status, non-durable mode, recent events, status vocabulary, and timeline safeguards

The gated live-adapter candidate slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/provider-adapter/candidates` and `POST /api/provider-adapter/gate-check` proving the OfoxAI candidate is registered but execution remains denied with explicit auth, vault, quota, and worker blockers
- a browser smoke that starts the Pro API and web shell, runs the adapter dry-run, clicks `Check live gates`, and verifies that the live gate panel renders the OfoxAI candidate, denied execution, and blocking reasons

The graph-review comparison slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/runs/{run_id}/review-comparison` proving the comparison is derived, returns evidence/challenge added deltas, and keeps provider/credential access disabled
- a browser smoke that starts the Pro API and web shell and verifies that the review-comparison panel renders derived checkpoint mode, evidence/challenge delta counts, and comparison safeguards

The credential-vault boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/credential-vault-boundary` proving the vault boundary is disconnected, returns no secret values, and names blocked access rules plus safeguards
- a browser smoke that starts the Pro API and web shell and verifies that the vault-boundary panel renders connections-off state, secret-values-returned `no`, credential classes, and safeguards

The quota-ledger/billing boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/quota-ledger-boundary` proving ledger mutation and payment-provider connections stay off while quota lanes, metering rules, and safeguards are visible
- a browser smoke that starts the Pro API and web shell and verifies that the quota-ledger panel renders planned-no-mutation mode, ledger mutation off, payment provider off, quota lanes, and billing safeguards

The worker-lease/retry boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/worker-lease-boundary` proving worker leases, lease-store connections, retry scheduling, and execution stay disabled while lease/retry/idempotency rules are visible
- a browser smoke that starts the Pro API and web shell and verifies that the worker-lease panel renders planned-no-workers mode, lease store off, retry scheduler off, retry policies, and worker safeguards

The result-commit/event-store boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/result-commit-boundary` proving event-store connections, commit writes, and partial-result reconciliation stay disabled while commit stages, event write rules, and safeguards are visible
- a browser smoke that starts the Pro API and web shell and verifies that the result-commit panel renders planned-no-writes mode, event store off, writes off, partial reconciliation off, commit stages, event write rules, and commit safeguards

The local event-store/replay slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/runs/{run_id}/event-replay`, `GET /api/runs/{run_id}/event-log`, and `POST /api/runs` proving seed and created-run replay streams persist to the local JSON event store while hosted storage, workers, credentials, auth, quota, billing, and provider execution remain disabled
- a browser smoke that starts the Pro API and web shell and verifies that the event-replay panel renders local durable mode, local-file replay, replay events, and replay safeguards

The worker result dry-run slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/runs/{run_id}/worker-result-dry-run` proving the payload is derived from local replay, exposes proposed result commit steps, and keeps execution, provider calls, result-event writes, credentials, auth, quota, and billing disabled
- a browser smoke that starts the Pro API and web shell, clicks `Dry-run result commit`, and verifies that the worker-result panel renders preview-only local replay, blocked result writes, commit checks, and dry-run safeguards

The result snapshot readiness slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/runs/{run_id}/result-snapshot-readiness` proving the payload is derived from worker-result dry-run/local replay and keeps snapshot persistence, result-event writes, provider calls, credentials, auth, quota, and billing disabled
- a browser smoke that starts the Pro API and web shell, clicks `Check snapshot gate`, and verifies that the readiness panel renders preview-only gate mode, persistence off, readiness blockers, proposed non-persisted snapshot metadata, and safeguards

The worker result commit-intent slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/runs/{run_id}/worker-result-commit-intent` proving the payload is derived from result-snapshot readiness/local replay and keeps commits, result-event writes, snapshot persistence, provider calls, credentials, auth, quota, and billing disabled
- a browser smoke that starts the Pro API and web shell, clicks `Prepare commit intent`, and verifies that the commit-intent panel renders rejected mode, idempotency key preview, future event writes, blockers, and safeguards

The execution-readiness gate slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/execution-readiness` proving the composed payload keeps execution denied while exposing workspace, provider, worker, snapshot, and observed-preview blockers without secret-shaped fields
- a browser smoke that starts the Pro API and web shell, runs the local preview prerequisites, clicks `Check execution readiness`, and verifies that the readiness panel renders denied execution, observed prerequisites, blockers, and safeguards

The execution-admission gate slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/execution-admission` proving the server-computed payload keeps admission denied while exposing tenant/auth, vault-handle, quota-reservation, and preflight blockers without secret-shaped fields
- a browser smoke that starts the Pro API and web shell, clicks `Check admission gate`, and verifies that the admission panel renders denied admission, tenant auth, vault handle, quota reservation, and no provider execution or secret access safeguards

The hosted intent create-request preview slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/execution-intents/create-request` proving the payload keeps create requests, persistence, and execution rejected while exposing admission, intent-store, worker-lease, request-field, write-plan, and idempotency blockers without secret-shaped fields
- a browser smoke that starts the Pro API and web shell, clicks `Preview intent create request`, and verifies that the panel renders create-request rejection, admission denial, disconnected intent store, persistence off, no durable intent id, blocked write steps, and no-persistence safeguards

The pre-execution boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/execution-preflight-boundary` proving execution stays denied while hosted auth, vault-handle, quota-reservation, worker-lease, and idempotent-commit prerequisites are visible without secret-shaped fields
- a browser smoke that starts the Pro API and web shell and verifies that the pre-execution panel renders denied execution, hosted prerequisites, quota reservation, vault handle, handoff blockers, and safeguards

The execution handoff preview slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/execution-jobs` followed by `GET /api/execution-jobs/{job_id}/handoff-preview` proving the handoff stays denied while work-order, auth, vault, quota-reservation, worker-lease, and idempotent-commit blockers are visible without secret-shaped fields
- a browser smoke that starts the Pro API and web shell, clicks `Queue preview job`, and verifies that the handoff preview panel renders denied execution, quota reservation, work-order execution blockers, and handoff safeguards

The execution intent preview slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `POST /api/execution-jobs` followed by `GET /api/execution-jobs/{job_id}/intent-preview` proving the intent stays rejected while handoff, worker lease, idempotency, and persistence blockers are visible without secret-shaped fields
- a browser smoke that starts the Pro API and web shell, clicks `Queue preview job`, and verifies that the intent preview panel renders rejected intent creation, worker lease store, execution intent persistence, and no-persistence safeguards

The execution intent-store boundary slice adds:

- `cargo fmt --manifest-path pro/Cargo.toml --all -- --check`
- `cargo test --manifest-path pro/Cargo.toml`
- `cargo build --manifest-path pro/Cargo.toml`
- an API smoke for `GET /api/execution-intent-store-boundary` proving the planned store stays disconnected while transition, idempotency, retention, replay-before-claim, and no-persistence safeguards are visible without secret-shaped fields
- a browser smoke that starts the Pro API and web shell and verifies that the intent-store boundary panel renders planned-no-persistence mode, persistence off, transition rules, idempotency rules, retention rules, and no-intent-persistence safeguards
