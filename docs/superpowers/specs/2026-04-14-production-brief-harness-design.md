# Production Brief Harness Design

Date: 2026-04-14

## Purpose

RetroCause should stop optimizing the product around one impressive example question. The product value is not that it can explain a single US/Iran talks case. The value is that a user can ask a real production question and receive an evidence-grounded brief that is readable, reviewable, portable, and honest about what is missing.

The next product layer is the **Production Brief Harness**. It turns the existing causal analysis result into a scenario-aware output for three common workflows:

- Market and investment research
- Policy and geopolitics analysis
- Company or operations postmortems

This belongs in the OSS version because it is core product usefulness for a single local run. Pro remains the workflow and delivery layer: hosted runs, saved runs, PDF/DOCX, team sharing, schedules, source policies, branded reports, comparisons, approval flows, and audit logs.

## Product Principle

The system must optimize for production usefulness, not single-case polish.

The US/Iran Islamabad talks query remains useful as a regression case because it exercises Chinese input, live retrieval, source trace, challenge coverage, graph labels, and Markdown export. It must not drive hardcoded product behavior. Product logic should be scenario-general, evidence-grounded, and reusable across domains.

## Supported Scenarios

### Market Brief

Use when the user asks about prices, markets, assets, companies, rates, inflation, sentiment, liquidity, or financial shocks.

Users want to see:

- The most likely market driver
- Short-term shocks versus structural drivers
- Bull and bear counterpoints
- Watchlist signals to monitor next
- Evidence freshness and source quality

Output sections:

- Key drivers
- Bull case / Bear case
- Short-term vs structural factors
- Watchlist signals
- Evidence gaps

Freshness gate:

- Recent market queries such as today, yesterday, latest, live, price drop, or selloff require fresh or explicitly time-bounded evidence.
- If fresh evidence is missing, the production status must be `needs_more_evidence`, not `ready_for_brief`.

### Policy / Geopolitics Brief

Use when the user asks about countries, governments, talks, sanctions, war, elections, policy decisions, official statements, or diplomatic outcomes.

Users want to see:

- Actor positions
- Binding constraints
- Disagreement points
- Alternative narratives
- Missing primary sources
- Source reliability across official, wire, index, and web sources

Output sections:

- Actor positions
- Binding constraints
- Disagreement points
- Alternative narratives
- Missing primary sources

Freshness gate:

- Recent policy or geopolitical queries require fresh evidence or a clear source-risk warning.
- If only weak web search evidence is available, a brief can still be generated, but the status should degrade unless the limits and next verification steps are explicit.

### Postmortem Brief

Use when the user asks why an incident, outage, launch failure, churn spike, operational miss, or internal failure happened.

Users want to see:

- Root cause versus contributing factors
- Trigger events
- Amplifying factors
- Controllable and uncontrollable factors
- Corrective actions
- Verification checklist

Output sections:

- Root cause
- Trigger events
- Amplifying factors
- Controllable vs uncontrollable
- Corrective actions
- Verification checklist

Freshness and evidence gate:

- Internal postmortem questions need internal evidence such as logs, tickets, metrics, customer feedback, or incident notes before the system can mark the result ready.
- If only public web evidence is available for an internal incident, the status must be `not_actionable` or `needs_more_evidence`, with explicit next steps requesting internal artifacts.

## API Design

Keep `/api/analyze/v2` backward-compatible. Add optional request and response fields instead of replacing the current schema.

Request addition:

```python
scenario_override: Optional[str] = None
```

Allowed values:

- `market`
- `policy_geopolitics`
- `postmortem`
- `general`

If omitted, the backend detects the scenario. If provided, the override wins and the response records that the user selected it.

Response additions:

```python
scenario: {
  "id": "market" | "policy_geopolitics" | "postmortem" | "general",
  "label": str,
  "confidence": float,
  "signals": list[str],
  "override_available": bool
}
```

```python
production_brief: {
  "title": str,
  "executive_answer": str,
  "sections": list[{
    "id": str,
    "title": str,
    "items": list[{
      "claim": str,
      "evidence_ids": list[str],
      "confidence": float,
      "risk": "low" | "medium" | "high"
    }]
  }],
  "decision_implications": list[str],
  "next_verification_steps": list[str],
  "limits": list[str]
}
```

```python
production_harness: {
  "status": "ready_for_brief" | "needs_more_evidence" | "not_actionable" | "blocked",
  "score": float,
  "checks": list[{
    "id": str,
    "status": "pass" | "warn" | "fail",
    "detail": str
  }],
  "user_value_summary": str
}
```

The existing `product_harness` stays for compatibility. `production_harness` is stricter and user-value oriented.

## Scenario Detection

First implementation should use deterministic rules, not a new LLM call.

Signals:

- Parsed domain from the existing parser
- Query keywords
- Relative or absolute time expressions
- Retrieval source mix
- Common event verbs such as failed, collapsed, dropped, outage, talks, agreement, sanctions, launch, incident

Market examples:

- price, stock, crypto, bitcoin, market, rate, inflation, selloff, ETF
- 股价, 暴跌, 比特币, 市场, 利率, 通胀, 资金流

Policy / geopolitics examples:

- country, government, sanctions, talks, agreement, election, war, policy, official
- 国家, 政府, 谈判, 协议, 制裁, 政策, 选举, 冲突

Postmortem examples:

- incident, outage, failure, downtime, churn, launch failed, root cause, retrospective
- 事故, 宕机, 失败, 流失, 复盘, 根因, 故障

When signals tie, prefer `general` unless the user manually selected a scenario.

## Evidence Anchoring Rules

Every production claim must be evidence-anchored.

Rules:

- A section item that makes a causal or diagnostic claim must include at least one `evidence_id`.
- If no evidence supports a potential claim, that text belongs in `limits` or `next_verification_steps`, not in a conclusion section.
- Confidence values must stay in `[0, 1]`.
- Source count is a coverage signal, not a truth guarantee.
- "No challenge evidence found" means none was found or attached in this retrieval pass, not that no refutation exists anywhere.
- LLM-generated causal conclusions must not be surfaced without source references or evidence ids.

## Freshness Gating

The production harness must consume existing `freshness_status`, `time_range`, `retrieval_trace`, and source metadata.

Checks:

- Recent market query has fresh evidence.
- Recent policy/geopolitics query has fresh evidence or explicit source-risk warnings.
- Internal postmortem query has internal/user-provided evidence before being marked ready.
- Retrieval trace is present for live results.
- Failed-source count is visible when source access fails.

Status behavior:

- `ready_for_brief`: enough evidence, source trace, scenario fit, and next-step clarity.
- `needs_more_evidence`: useful partial result, but freshness, source mix, or challenge coverage is weak.
- `not_actionable`: output lacks the evidence type needed for the scenario.
- `blocked`: provider/model/source failure prevents useful analysis.

## Frontend Design

Add a `Use case` selector near model settings:

- Auto
- Market brief
- Policy / geopolitics brief
- Postmortem brief

Default is Auto. User override is passed to the API.

Upgrade the readable brief card into a Production Brief card:

- Scenario label
- Production status
- Evidence health summary
- Scenario-specific sections
- Decision implications
- Next verification steps
- Limits

Keep the evidence board, source trace, challenge coverage, and graph. They are the audit layer beneath the brief.

Copy behavior:

- `Copy report` copies scenario-specific Markdown.
- Manual-copy fallback remains.
- Markdown title changes by scenario:
  - `RetroCause Market Brief`
  - `RetroCause Policy / Geopolitics Brief`
  - `RetroCause Postmortem Brief`
  - `RetroCause Research Brief`

## Localization Strategy

Remove single-case product logic from the main localization path.

Allowed:

- General scenario labels
- General causal roles such as root cause, trigger, amplifier, constraint, outcome
- General terms such as agreement, sanctions, negotiation, price drop, outage, root cause
- Preserve model-provided entity names when translating would be risky

Avoid:

- Product logic hardcoded to one news case
- A growing phrase table for every golden-case entity
- Generic fallback labels that erase causal meaning, such as replacing specific labels with "market impact factor"

Golden cases should test behavior, not become product behavior.

## Testing Plan

Add tests for:

- Market scenario detection
- Policy/geopolitics scenario detection
- Postmortem scenario detection
- Scenario override precedence
- Production brief claim evidence anchoring
- Market brief sections
- Policy/geopolitics brief sections
- Postmortem brief sections
- Freshness gating for recent market queries
- Source-risk warning for recent policy/geopolitics queries
- Internal-evidence warning for postmortem queries
- Frontend use-case selector
- Frontend Production Brief rendering
- Markdown report title changes by scenario
- Golden-case label regression that checks labels stay specific without requiring case-specific translations

## Non-Goals For First Implementation

- No PDF/DOCX export
- No team sharing
- No saved runs
- No scheduled briefings
- No source policy UI
- No account system
- No new LLM report-writing pass
- No large graph interaction rewrite
- No hardcoded optimization for one news event

## Rollout Plan

1. Add schema models and deterministic scenario detection.
2. Add production brief builder using existing grounded response fields.
3. Add production harness checks and freshness gates.
4. Add request override support.
5. Update frontend selector and Production Brief rendering.
6. Update Markdown export template.
7. Replace single-case label expectations with general specificity tests.
8. Sync README, project state, and evidence notes.
9. Run focused tests, root `npm test`, and `agent-guardrails check`.

## Acceptance Criteria

- The same backend path supports market, policy/geopolitics, and postmortem briefs.
- Manual scenario override works.
- Every production brief claim has evidence ids or is moved to limits/verification steps.
- Recent market questions cannot be marked ready without fresh evidence.
- Policy/geopolitics briefs expose source risk when primary or stable sources are weak.
- Postmortem briefs ask for internal evidence when only external sources exist.
- The frontend shows a scenario-aware production brief and preserves the audit trail.
- The OSS/Pro boundary remains intact.
