# RetroCause Pro Rust Architecture

Last updated: 2026-04-24

## Why a separate Rust workspace

The OSS Python/FastAPI + Next.js app remains the inspectable local product. Pro needs a different runtime shape: queueable jobs, durable run records, explicit quota ownership, and more controlled latency under provider pressure. That is a good fit for a separate Rust codebase rather than accreting hosted concerns into the OSS stack.

The Rust rewrite lives under `pro/` inside this repository so the product and architecture can evolve in the open without destabilizing OSS runtime paths.

## Current architecture goals

1. Establish a clean Rust workspace boundary.
2. Define shared Pro domain types around graph-first runs, evidence anchors, challenge checks, source health, usage ledger entries, provider quota ownership, and cooldown state.
3. Stand up API endpoints that expose run summaries, run detail, graph payloads, file-backed local run creation, keyless provider/search quota status, routing previews, and preview-only execution jobs.
4. Render a graph-first web shell from the same shared Rust payload and wire it to the local API create/read flow plus provider-status view.
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

The credential-vault boundary is deliberately keyless and disconnected in this slice. It names future credential classes, metadata-only visibility, worker-scoped access requirements, rotation ownership, and safeguards while returning `secret_values_returned=false` and `connections_enabled=false`.

The quota-ledger and billing boundary is deliberately preview-only in this slice. It names future quota lanes, metering rules, rate-limit rules, payment-provider absence, and billing safeguards while returning `ledger_mutation_enabled=false`, `payment_provider_connected=false`, and no billable usage.

The result-commit and event-store boundary is deliberately preview-only in this slice. It names future commit stages, event write rules, and partial-result reconciliation rules while returning `event_store_connected=false`, `commit_writes_enabled=false`, and `partial_reconciliation_enabled=false`.

The run event timeline is deliberately non-durable in this slice. It is generated from the current `ProRun` record and names event/status vocabulary before an event store exists. It does not open an event-store connection, run workers, call providers, enforce auth, or mutate run state.

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

## Provider routing boundary

`crates/provider-routing` is the first Pro provider/source routing boundary. It currently produces a route preview plan from the static keyless provider-status payload.

Current behavior:

- input: workspace id, query, optional scenario, optional source policy
- output: preview-only route plan with lane decisions, cooldown hints, selected local lane, and warnings
- execution: always disabled in this slice
- selected local fallback: uploaded-evidence lane when the source policy allows it
- explicit blocked/deferred lanes: managed Pro model pool, workspace search, BYOK-later search, and market-search cooldown

This is intentionally not a provider executor. It does not read provider keys, call models/search APIs, enqueue jobs, bill usage, or store credentials. The value is the decision vocabulary: future executors can consume the same lane and decision semantics instead of inventing hidden routing behavior inside provider adapters.

`crates/provider-routing` also carries a dry provider-adapter contract, a non-executing adapter dry-run shape, and the first gated live-adapter candidate. The contract names the future adapter request fields, result fields, degradation states, quota guards, and partial-result rules before any provider implementation exists. The dry-run accepts a workspace id, query, provider lane, and source policy, then returns preview evidence, zero-billable usage ledger rows, visible degradation states, and safety warnings without reading credentials or calling providers. The OfoxAI model adapter candidate is registration-only: gate checks can show that dry-run, auth context, quota ownership, and event timeline previews were observed, but execution remains denied until real tenant auth, credential vault reads, quota ledger enforcement, and worker execution exist. These shapes require explicit quota ownership, retry-after cooldown visibility, degraded source states, usage ledger rows, and evidence preservation before retries.

## Queue boundary

`crates/queue` is the first Pro execution-queue boundary. It currently provides an in-memory `ExecutionQueue` that turns a routing-preview request into a preview-only execution job.

Current behavior:

- input: the same workspace id, query, scenario, and source policy accepted by provider-routing preview
- output: execution job payload with id, workspace id, query, preview-only status, selected lane, and the full route plan
- worker contract: a non-executing work-order payload with route steps, routing warnings, selected lane, and explicit safeguards
- lifecycle contract: a non-executing hosted-worker stage/failure taxonomy that names future queue, worker, provider, partial-result, and terminal states before adapters exist
- worker lease/retry contract: a non-executing lease, retry, and idempotency boundary that names claim rules, retry policies, duplicate-call prevention, and partial-result preservation before workers exist
- storage: process-local memory only
- execution: always disabled in this slice

This is intentionally not a worker system. It does not read provider keys, call models/search APIs, persist queue state, bill usage, enforce tenant quotas, claim leases, or schedule background work. The value is the API, state, work-order, worker-lease, and retry boundary: future Redis/Postgres-backed queue workers should replace the in-memory implementation without making API routes own job sequencing, route-plan coupling, retry loops, idempotency semantics, or safety gate behavior.

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
- `GET /api/runs/{run_id}/review-comparison`
- `GET /api/workspace/access-context`
- `GET /api/credential-vault-boundary`
- `GET /api/quota-ledger-boundary`
- `GET /api/result-commit-boundary`
- `GET /api/provider-status`
- `GET /api/provider-adapter-contract`
- `GET /api/provider-adapter/candidates`
- `POST /api/provider-adapter/gate-check`
- `POST /api/provider-adapter/dry-run`
- `GET /api/provider-route/preview`
- `POST /api/provider-route/preview`
- `GET /api/execution-jobs`
- `POST /api/execution-jobs`
- `GET /api/execution-jobs/{job_id}`
- `GET /api/execution-jobs/{job_id}/work-order`
- `GET /api/execution-lifecycle`
- `GET /api/worker-lease-boundary`
- `GET /api/storage-plan`
- minimal local CORS headers for the separate Pro web port
- local JSON run storage through `crates/run-store`, shared by list/detail/graph reads and surviving API restarts
- no-connection hosted storage migration plan through `crates/run-store`
- local preview-only queue jobs through `crates/queue`, shared by list/detail reads while the API process is running
- future home for durable run status, queue control, provider routing, cooldown buckets, and saved-run access

The current store is intentionally local-file-backed. It is useful for proving the API behavior, graph payload contract, and restart continuity, but it should not be treated as the hosted Pro data layer. The workspace access context, credential-vault boundary, quota-ledger boundary, result-commit boundary, run-events, review-comparison, provider-status, provider-route preview, execution-job, lifecycle, worker-lease, and storage-plan endpoints are static/keyless in this slice: they model tenant/auth vocabulary, credential handling vocabulary, quota/billing vocabulary, result/event commit vocabulary, run status vocabulary, review delta vocabulary, ownership, cooldown, routing semantics, queue shape, worker states, retry/idempotency semantics, and storage boundaries without exposing credential fields, mutating quota/billing state, connecting a payment provider, writing events, opening event-store/database/Redis connections, enforcing auth, claiming worker leases, scheduling retries, or calling real providers. The CORS behavior is local-alpha plumbing for `127.0.0.1` API/web development, not a production auth or permission boundary.

### `apps/web`

Initial responsibility:

- render the graph-first Pro workspace
- visualize the canonical run, including evidence anchors, challenge checks, source health, and usage ledger state
- create new in-memory runs through `POST /api/runs`
- reload run summaries, run detail, and graph payloads from the Pro API
- render the non-enforcing workspace/auth context from `GET /api/workspace/access-context`
- render the planned credential-vault boundary from `GET /api/credential-vault-boundary`, showing credential classes, blocked access rules, and safeguards without showing values
- render the planned quota-ledger/billing boundary from `GET /api/quota-ledger-boundary`, showing quota lanes, metering rules, and billing safeguards without writing usage or connecting payment infrastructure
- render the planned result-commit/event-store boundary from `GET /api/result-commit-boundary`, showing commit stages, event write rules, partial-result reconciliation, and safeguards without writing durable events
- render a non-durable run event timeline from `GET /api/runs/{run_id}/events`
- render a derived review-comparison panel from `GET /api/runs/{run_id}/review-comparison`, showing evidence/challenge deltas and preview safeguards
- show provider/search quota ownership, credential policy, and cooldown status through the local provider-status payload
- render the dry provider-adapter request/result/degradation contract from `GET /api/provider-adapter-contract`
- run a keyless provider-adapter dry-run through `POST /api/provider-adapter/dry-run`, showing zero billable units, evidence-preview count, degradation states, and calls-disabled state
- render the gated live-adapter candidate catalog from `GET /api/provider-adapter/candidates`
- run a denied live-adapter gate check through `POST /api/provider-adapter/gate-check`, showing which auth, quota, dry-run, event, vault, and worker gates block execution
- create and list preview-only execution jobs through the local execution-job API
- inspect queued job work orders through `GET /api/execution-jobs/{job_id}/work-order`, rendering route steps, routing warnings, selected lane, and execution safeguards while execution stays disabled
- render the hosted-worker lifecycle/failure taxonomy from `GET /api/execution-lifecycle` so future execution states are visible before live adapters exist
- render the worker-lease/retry boundary from `GET /api/worker-lease-boundary`, showing lease rules, retry policies, idempotency keys, and safeguards while workers and retry scheduling stay disabled
- render the hosted storage migration boundaries from `GET /api/storage-plan` so Postgres/Redis/tenant/worker ownership is visible before connections exist
- keep a browser-local selected-node state and graph inspector for evidence/challenge links, including focused evidence/challenge review items
- establish layout, palette, and information hierarchy for the knowledge-graph experience

## Future crates after the kickoff

- `crates/export`
- `crates/evidence-store`

`crates/run-store`, `crates/provider-routing`, and `crates/queue` exist today. The other crates are intentionally not created yet; each should appear only when it removes real duplication or isolates a concrete boundary.

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

The current `POST /api/runs` path uses `queued` runs and managed/user-provided quota labels without calling model or search providers. The current `GET /api/provider-status` path exposes static ownership lanes for managed Pro quota, workspace-managed search quota, BYOK-later search, uploaded-evidence-only input, and an example market-search cooldown bucket. The current `POST /api/execution-jobs` path records a preview-only queue job from the routing plan, and `GET /api/execution-jobs/{job_id}/work-order` exposes the non-executing work-order contract a future worker should consume. Live provider credentials, BYOK storage, workspace quotas, real cooldown enforcement, and real worker execution remain future work.

The current `GET /api/workspace/access-context` path exposes a static local preview actor and permission vocabulary. It does not authenticate, authorize, issue sessions, validate tokens, store credentials, mutate billing/quota, or protect hosted resources. Future auth work should replace this preview context with real tenant and actor resolution before any provider execution is enabled.

The current `GET /api/credential-vault-boundary` path exposes planned credential classes, access rules, rotation rules, and safeguards. It does not accept credential input, read or store secrets, open a vault connection, return values, or enable workers. Future hosted Pro should replace it with metadata-only vault status after auth, quota ledger, and worker leases exist.

The current `GET /api/quota-ledger-boundary` path exposes planned quota lanes, metering rules, rate-limit rules, and billing safeguards. It does not write ledger rows, reserve quota, connect a payment provider, emit billable usage, enforce limits, or enable provider execution. Future hosted Pro should replace it with tenant-scoped quota reservations and billing policy checks after auth, vault, event-store, and worker leases exist.

The current `GET /api/worker-lease-boundary` path exposes planned worker-lease, retry, and idempotency rules. It does not start workers, claim leases, connect a lease store, schedule retries, read credentials, mutate quota/billing, or call providers. Future hosted Pro should replace it with durable lease claims, bounded retry scheduling, duplicate-call prevention, and partial-result reconciliation after tenant auth, quota reservations, vault access, and event-store writes exist.

The current `GET /api/result-commit-boundary` path exposes planned result-commit stages, event write rules, partial-result reconciliation rules, and safeguards. It does not write events, open an event-store connection, mutate run state, claim worker leases, read credentials, reserve quota, or call providers. Future hosted Pro should replace it with durable event writes after tenant auth, quota reservations, vault access, idempotent worker commits, and storage boundaries exist.

The current `GET /api/runs/{run_id}/events` path derives a non-durable timeline from the run record. It is useful for UI and API vocabulary, but it is not an audit log, not a durable event stream, and not a worker status queue. Future hosted Pro should replace or supplement it with event-store rows once tenant/auth, worker leases, and storage boundaries exist.

The current `GET /api/runs/{run_id}/review-comparison` path derives a previous-checkpoint preview from the requested run and reports evidence/challenge deltas. It is useful for shaping graph-review UI, but it is not a durable comparison against another tenant-scoped run. Future hosted Pro should replace the derived baseline with explicit run selection after auth and durable history exist.

The current `GET /api/provider-adapter/candidates` and `POST /api/provider-adapter/gate-check` paths register and inspect a future OfoxAI model adapter candidate. They do not execute the candidate. Even if preview gates are marked observed, the gate check returns `execution_allowed=false` until real auth enforcement, credential vault access, quota ledger enforcement, and worker execution are implemented.

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
