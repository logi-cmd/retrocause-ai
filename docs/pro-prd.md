# RetroCause Pro PRD

Last updated: 2026-04-24

## Product thesis

RetroCause OSS proves that inspectable causal analysis is useful. RetroCause Pro should monetize the repeated workflow around that insight: durable runs, clearer operator status, queued execution under rate limits, richer evidence review, and deliverables that a person can actually send to a colleague or client.

The product is not "more AI text." The product is a faster path from a live question to a reviewable, source-backed knowledge graph and exportable brief.

## Target user

### Primary

- Independent analysts, consultants, and operators who repeatedly explain why events happened.
- Small research teams that need a shared run history, explicit source reliability, and stakeholder-ready output.

### Secondary

- Builders and researchers who already use the OSS version locally and want hosted continuity, saved runs, and more reliable delivery.

## Jobs to be done

1. When something important happens, give me a run I can trust enough to review instead of rebuilding the whole explanation from scratch.
2. Show me the graph of causes, evidence anchors, counterpoints, and degraded sources in one place.
3. Preserve enough run history that I can compare what changed between yesterday's explanation and today's.
4. Export something that already looks like a briefing artifact, not a raw model dump.
5. Be honest when sources, providers, or quotas are degraded.

## Non-goals

- Generic chat workspace
- Hidden retries or silent fallback that conceal provider trouble
- Enterprise deployment, SSO, document-level ACL, or private connectors in v1
- Rebuilding the OSS local app in place

## Product principles

### 1. Graph first

The primary Pro surface is a knowledge-graph workspace. The user should understand the current explanation by looking at nodes, edges, evidence anchors, and challenge coverage before reading a long report.

### 2. Delivery over novelty

Every run should end in one of three honest states:

- ready to review
- needs follow-up
- blocked with explicit reason

### 3. Source truth stays visible

Every major claim must stay tied to evidence or to an explicit missing-evidence caveat. Degraded-source states are product states, not debug leftovers.

### 4. Queueing is part of the product

Rate limits and provider cooling-down are expected. Pro should turn those constraints into visible workflow states rather than random failure.

## V1 workflow

### Trigger

The user creates a run from a saved watch topic, pasted query, or uploaded evidence set.

### Process

1. Pro routes the run through the right source policy.
2. The run enters a queued or active state.
3. The graph canvas fills with the current best explanation, evidence, and challenge coverage.
4. The side rails show run state, source health, evidence pack, and next review actions.
5. The user exports or shares the run after review.

### Deliverable definition

A successful Pro run produces:

- a reviewable knowledge graph
- a concise operator summary
- evidence anchors and source trace
- challenge/refutation coverage
- caveats and next verification steps
- an export artifact or shareable review state

## MVP scope

### Included

- Hosted run records with run status and step history
- Knowledge-graph workspace as the default run view
- Evidence and source-health side rails
- Saved runs and compare-ready structure
- Uploaded evidence library
- Export-ready report schema
- Solo Pro quotas and usage ledger

### Deferred

- Team Lite comments and review links
- Scheduled watch topics
- Billing integration
- Full document ingest pipeline beyond lightweight supported formats

## UX shape

### Primary layout

- Center: knowledge graph canvas
- Left: operator summary, run status, next actions
- Right: evidence pack, source-health ledger, challenge coverage

### Critical states

- queued
- active
- partial-live
- cooling down
- cached
- needs more evidence
- ready for review
- blocked

## Pricing hypothesis

Start with Solo Pro.

- Base plan: monthly run allowance, export allowance, and managed quota
- BYOK tier or add-on: user-managed provider/search keys with lower managed-quota pressure
- Deep review or scheduled rerun limits stay explicit instead of "unlimited"

## Success metrics

- Time to first reviewable graph under 3 minutes on a normal successful run
- At least 80% of successful runs produce an artifact that can be forwarded with light editing
- Users can explain why they trust or distrust the result by pointing to evidence, challenge coverage, and source status
- Failed runs are understood, not merely observed

## Build sequence

1. Rust workspace and graph-first shell
2. Durable run model and API skeleton
3. Evidence/source side rails
4. Saved run and comparison primitives
5. Export pipeline
