# RetroCause Pro Planning Kickoff

Last updated: 2026-04-24

## Why This Exists

The OSS line now qualifies as a stable-deliverable local alpha, with the latest public GitHub release still at `v0.1.0-alpha.5`. That unlocks Pro planning, but it does not justify building hosted Pro inside the current Python/FastAPI + Next.js repo.

This document is the starting point for the next phase: define the first paid RetroCause workflow clearly enough that a separate Rust implementation can be planned on purpose.

## Planning Goal

Define a Pro product that monetizes repeated causal-brief workflows without weakening the OSS inspectability promise.

The paid value should be:

- faster delivery under provider and source limits
- durable saved runs and comparisons
- uploaded evidence libraries
- stakeholder-ready export
- scheduled reruns and change alerts
- small-team review and quota controls

The paid value should not be:

- generic "more AI"
- hidden provider retries with no user visibility
- a vague enterprise platform

## Constraints

- Keep OSS as the local inspectable product.
- Do not continue growing hosted infrastructure in this repo.
- Treat Pro as a separate full-stack Rust rewrite.
- Preserve explicit source trace, challenge coverage, uncertainty, and quota ownership in Pro outputs.

## First Product Hypothesis

Start with `Solo Pro`, then expand to `Team Lite` only after the single-user workflow is crisp.

Reason:

- Solo Pro has the clearest value loop: one person needs a reviewable brief quickly and repeatedly.
- It keeps quota, provider routing, cache, export, and run queue problems smaller.
- Team features are easier to add after the run object, export artifact, and audit trail already exist.

## Workstreams

### 1. Product Scope

- lock the exact deliverable for a successful paid run
- define what is OSS-only, Pro-only, and BYOK-only
- define pricing guardrails by run volume, export volume, and scheduled topics

### 2. Runtime Architecture

- choose Rust web framework, queue, storage, cache, and worker topology
- define sync vs queued vs scheduled execution boundaries
- define the run object and lifecycle states

### 3. Quota And Key Ownership

- define managed quota vs BYOK vs workspace-managed quota
- define provider/search cooldown, retry-after, and fallback behavior
- define usage ledger semantics for billing and audit

### 4. Evidence And Reports

- define uploaded evidence ingestion and citation storage
- define report schema for Markdown, PDF, and DOCX
- define saved-run comparison model and diff surface

### 5. Team Lite Boundary

- define read-only review links
- define reviewer notes vs model-generated content
- keep document-level ACL and enterprise controls out of the first scope

## Immediate Planning Deliverables

1. Pro PRD
   - target users
   - jobs to be done
   - pricing hypothesis
   - success metrics

2. System Architecture Note
   - Rust stack choice
   - queue and worker model
   - storage and cache layout
   - provider/search routing control plane

3. Quota And Billing Policy
   - managed vs BYOK routing
   - budget exhaustion behavior
   - audit and ledger fields

4. Data Model Draft
   - run record
   - evidence item
   - uploaded document
   - export artifact
   - comparison snapshot

## Suggested Sequence

1. Write the Pro PRD.
2. Freeze the OSS/Pro boundary in docs.
3. Write the Rust system architecture note.
4. Define quota and key-management policy.
5. Define the run/evidence/export data model.
6. Re-check whether `Solo Pro` still beats `Team Lite` as the first build.

## Non-Goals For This Kickoff

- no hosted Pro implementation in this repo
- no billing integration yet
- no enterprise roadmap inflation
- no multi-tenant infrastructure code in Python/FastAPI + Next.js

## Exit Criteria For Planning Phase 1

This kickoff is complete when all of these exist:

- a written Pro PRD
- a written Rust architecture note
- a written quota/key-management policy
- a written run/evidence/export data model
- a clear decision on `Solo Pro` first vs `Team Lite` first
