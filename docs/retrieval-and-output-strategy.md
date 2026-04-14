# Retrieval And Output Strategy

Last updated: 2026-04-15

## Purpose

RetroCause should not behave like a single prompt that asks an LLM to explain an event. The product value comes from a controlled evidence pipeline: retrieve sources, extract factual evidence, build causal hypotheses, attach evidence to each claim, check counter-evidence, then produce a reviewable brief with explicit limits.

RetroCause 不应该只是“把问题交给大模型写一段解释”。产品价值来自一条可检查的证据流水线：检索来源、抽取事实证据、构建因果假设、把证据锚定到每个结论、检查反证，再输出带边界的可审阅简报。

## Current Pipeline

```text
User question
  -> query parsing and scenario routing
  -> source policy selection
  -> source adapter retrieval
  -> evidence extraction and stance classification
  -> evidence store and source trace
  -> causal graph construction
  -> hypothesis chain generation
  -> evidence anchoring
  -> challenge / refutation retrieval
  -> evaluation and production harness checks
  -> readable brief, production brief, Markdown export, evidence board
```

The important product boundary is that causal conclusions should come from evidence-backed structures, not free-form model confidence. If a production claim has no evidence id, it belongs in a verification step, gap, caveat, or limit section.

## Source Adapter Risk

Source adapters are one of the first places where personal and small-team Pro usage can fail:

- public web pages can block scraping or change HTML structure
- search APIs can return 429s or daily quota failures
- news sources may return broad but low-specificity results
- some providers allow only transient storage of search results
- time-sensitive queries can accidentally reuse stale evidence if cache keys do not include absolute dates

This means rate limiting must be handled as a product workflow, not only as a retry loop. Users should see which sources were checked, which were rate-limited, which used cache, and whether the result is still reviewable.

## Source Portfolio

RetroCause should use a portfolio of sources instead of betting on one provider.

### OSS Default Sources

- Web search adapters for broad discovery.
- AP News and GDELT for time-sensitive news coverage.
- Federal Register for official U.S. policy and regulatory material.
- ArXiv and Semantic Scholar for research context.
- User-provided API keys where possible.

### Candidate Hosted Sources

- Tavily: useful for AI-oriented search, extract, crawl, and research workflows. Its public docs list development and production rate limits, including higher production RPM and separate research endpoint limits: <https://docs.tavily.com/documentation/rate-limits>.
- Brave Search API: useful as an independent web index, but its terms restrict storing or caching search results beyond transient operational storage unless the plan permits it. See Brave Search API terms: <https://api-dashboard.search.brave.com/documentation/resources/terms-of-service>.
- Exa: useful for semantic search and content retrieval. Its docs describe returning text, summaries, highlights, and RAG-ready context strings, which fits research-style retrieval: <https://docs.exa.ai/reference/contents-retrieval-with-exa-api>.
- SerpAPI or similar SERP providers: useful as a fallback or high-precision Google-like provider. Pricing/throughput and account-usage APIs are explicit, which helps quota management: <https://serpapi.com/high-volume> and <https://serpapi.com/account-api>.

These candidates should be added behind source policies and provider budgets, not hardcoded into every run.

## Source Policies

Scenario selection should change retrieval behavior, not only prompt wording.

### Market / Investment

Default source mix:

- broad web/news source for latest event discovery
- financial or company filings where relevant
- macro or official data source where relevant
- high-confidence evidence only before producing action-oriented language

Output focus:

- likely drivers
- confidence and freshness
- source health
- what would change the view
- verification steps before trade/investment use

### Policy / Geopolitics

Default source mix:

- broad web/news source
- official policy/government sources
- wire or stable news sources when available
- regional/context sources where relevant

Output focus:

- negotiation constraints
- official/public-source support
- counterclaims and missing primary sources
- freshness and source-risk gates

### Postmortem

Default source mix:

- uploaded evidence or user-provided documents
- public incident reports/status pages
- public GitHub/issues/commits where relevant
- public news or web context only as supporting context

Output focus:

- timeline
- decision points
- causal contributors
- missing internal evidence
- concrete follow-up checks

## Run Orchestrator Direction

Personal and small-team Pro should solve rate limits with a lightweight run layer, not enterprise private deployment.

```text
Create run
  -> enqueue retrieval
  -> apply provider budget
  -> use cache when allowed
  -> retry or fallback on rate limit
  -> mark partial results honestly
  -> resume later stages when providers recover
```

Minimum run controls:

- user-level quota
- workspace-level quota for Team Lite
- per-provider RPM and monthly budget
- run-level max search queries, pages, evidence items, LLM calls, and challenge edges
- retry-after handling
- circuit breaker for repeated 429/403/timeouts
- cache key with normalized topic, scenario, language, absolute time window, and source policy

## Cache Policy

Cache is mandatory for sustainable multi-user use, but cache must respect freshness and provider terms.

Cache layers:

- search query result cache
- fetched page content cache
- extracted evidence cache
- source reliability metadata
- source trace and run metadata

Cache keys must include:

- normalized topic
- scenario
- locale
- source policy
- freshness requirement
- absolute date bucket for relative time queries such as today, yesterday, this week, or latest

For providers with restrictive result-storage terms, store only transient operational data or derived evidence permitted by the provider plan and product policy.

## Product Output Contract

Every user-facing result should answer:

- What is the likely explanation?
- What reasons support it?
- What evidence anchors each reason?
- What counter-evidence or challenge retrieval was checked?
- What is missing, stale, risky, or not ready?
- What should the user verify next?

Markdown is the OSS portable format. Pro should add saved runs, run history, PDF/DOCX export, scheduled watch topics, and Team Lite review flows.

## Skills And Development Workflow

Codex/gstack skills are development tools, not user-facing retrieval sources. Use them to improve the product:

- `gstack` / `browse`: dogfood live source traces and UI behavior.
- `qa`: test source failure and degraded-output UX.
- `investigate`: debug adapter 429/403/timeouts and parser drift.
- `benchmark`: measure run latency and cache impact.
- `canary`: monitor deployed source health after release.
- `document-release`: keep README, project state, and release docs synchronized.

Inside the product, a similar idea should become source/domain packs, such as `market_research`, `policy_geopolitics`, and `postmortem`, but those packs must still go through source policy, provider budget, cache, and traceability controls.

## Near-Term Implementation Order

1. Add source policy documentation and UI/source-trace language for rate-limited or degraded sources.
2. Add a lightweight `SourceBroker` layer that centralizes adapter ordering, fallback, cooldown, and source trace metadata.
3. Add provider budget metadata for each adapter.
4. Add Tavily and Brave adapters behind optional keys and source policies.
5. Add cache keys that include scenario and absolute time buckets.
6. Add a lightweight run model with `run_id`, `status`, `steps`, and usage ledger.
7. Add uploaded evidence for personal/small-team use before considering any enterprise connector or private deployment.

## Non-Goals

- Do not promise unlimited search or unlimited AI usage.
- Do not bypass provider rate limits by creating multiple accounts or hidden scraping paths.
- Do not make private deployment a near-term Pro requirement.
- Do not hide partial-live, stale, source-limited, or provider-limited states.
- Do not let source packs become prompt-only presets; they must affect retrieval policy and evidence requirements.
