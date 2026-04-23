# RetroCause Pro Rust Architecture Kickoff

Last updated: 2026-04-24

## Why a separate Rust workspace

The OSS Python/FastAPI + Next.js app remains the inspectable local product. Pro needs a different runtime shape: queueable jobs, durable run records, explicit quota ownership, and more controlled latency under provider pressure. That is a good fit for a separate Rust codebase rather than accreting hosted concerns into the OSS stack.

For the kickoff, the Rust rewrite lives under `pro/` inside this repository so the product and architecture can evolve in the open without destabilizing OSS runtime paths.

## Kickoff architecture goals

1. Establish a clean Rust workspace boundary.
2. Define the first shared Pro domain types around a graph-first run.
3. Stand up an API shell and a web shell that both compile and share the same seed run model.
4. Prove the UI direction: a knowledge-graph workspace as the default Pro surface.

## Workspace layout

```text
pro/
  Cargo.toml
  apps/
    api/
    web/
  crates/
    domain/
```

## Stack choice for the kickoff

### API

- `axum`
- `tokio`
- `serde`

Reason: small, explicit, good fit for future queue, cache, and run-record services.

### Web

- `axum`
- `maud`
- shared Rust domain crate

Reason: the kickoff wants a graph-first shell that compiles quickly and keeps the first Rust web surface simple. Server-rendered HTML gives us a real interface immediately without committing to a WASM/hydration stack too early.

This is a deliberate tradeoff:

- good now: faster iteration, fewer moving parts, easier first compile/test path
- deferred: richer client-side graph interaction, drag behavior, zoom state persistence, incremental hydration

If the graph workspace proves out, the next phase can move the web shell toward Leptos or another Rust-heavy client strategy without changing the domain model or API boundary.

## Shared domain

The first shared crate defines:

- graph nodes
- graph edges
- evidence/source status cards
- a run summary model
- a canonical seed run used by both the API and the web shell

This keeps the API and web kickoff honest: they render the same shape instead of drifting into two separate demos.

## Near-term service split

### `apps/api`

Initial responsibility:

- health endpoint
- seed graph endpoint
- future home for run creation, run status, queue control, and saved-run access

### `apps/web`

Initial responsibility:

- render the graph-first Pro workspace
- visualize a canonical run state
- establish layout, palette, and information hierarchy for the knowledge-graph experience

## Future crates after the kickoff

- `crates/run-store`
- `crates/queue`
- `crates/provider-routing`
- `crates/export`
- `crates/evidence-store`

These are intentionally not created yet. The kickoff only adds abstraction that removes immediate duplication between API and web.

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

## Knowledge-graph UI direction

The Pro UI should feel like a review desk, not a generic SaaS dashboard.

- dark, calm, editorial surfaces
- graph canvas as the largest area
- side rails for operator summary and evidence review
- visible source states and challenge status
- no gradient-heavy AI dashboard styling

The kickoff web shell encodes that direction with a static graph workspace, while leaving advanced interaction for later.

## Verification for this kickoff

- `cargo test --manifest-path pro/Cargo.toml`

That is enough for the kickoff because there is no deployment pipeline, persistence layer, or browser runtime yet.
