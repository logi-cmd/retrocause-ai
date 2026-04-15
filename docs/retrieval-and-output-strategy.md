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

### Implemented Source Profile Baseline

Task 1 of the SourceBroker reliability pass adds a source profile registry in `retrocause.evidence_access`. Each source now has stable metadata for label, source kind, stability, cache policy, default RPM, monthly budget, and whether it requires an API key.

Implemented profiles:

- `ap_news`, `gdelt`, `gdelt_news`, and `web` for current news and broad discovery.
- `federal_register` for official U.S. policy records.
- `arxiv` and `semantic_scholar` for academic context.
- `tavily` and `brave` as optional hosted-search profiles before their adapters are added.

The broker still preserves explicit operator source overrides. When optional hosted sources are enabled, fresh market/news queries can try them before default discovery sources; policy/geopolitics queries keep AP News and Federal Register before hosted broad search so official and wire/news material stay prominent.

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

### Implemented Search Cache Scope

Task 2 of the SourceBroker reliability pass scopes the process-local search-result cache by:

- source adapter name
- source policy
- scenario
- language
- absolute time bucket
- normalized scoped query
- max result count

This prevents a market/news run, policy/geopolitics run, English run, Chinese run, or different relative-date bucket from silently reusing another run's retrieval results. Existing callers remain compatible through defaults, and collector-driven live retrieval now passes scenario and language from `plan_query()`.

### Implemented Source Degradation Statuses

Tasks 3 and 4 of the SourceBroker reliability pass give each source attempt stable retrieval-health metadata and expose it through V2 API retrieval traces plus Markdown/readable brief copy:

- `ok` for a successful upstream source call
- `cached` for a reused process-local cache hit
- `rate_limited` for HTTP 429-style provider limits, including parsed `Retry-After` seconds when available
- `forbidden` for HTTP 401/403-style auth or permission failures
- `timeout` for timeout exceptions
- `source_error` for general upstream failures such as connection errors
- `source_limited` for sources temporarily skipped because they are in cooldown after a recent failure

Each attempt also carries source label, source kind, stability, and cache policy from the source profile registry. The engine preserves these fields when compiling live pipeline results, and `_result_to_v2()` accepts both dict traces and `SourceAttempt` objects. Markdown source trace rows now say `rate-limited`, `source-limited`, `timeout`, or `source-error` directly instead of presenting degraded sources as silent zero-result rows. This is retrieval-health metadata only and does not introduce new causal claims.

### Implemented Optional Hosted Sources

Tavily and Brave Search are implemented as optional hosted sources. OSS remains runnable without a hosted-search account:

- `TAVILY_API_KEY` absent: Tavily is not registered in the app source map and SourceBroker ignores it.
- `TAVILY_API_KEY` present: Tavily can be included as an optional source and ordered by scenario-aware source policy.
- Tavily results map title, URL, content/snippet, raw content, score, and published date into `SearchResult`.
- Tavily metadata includes `provider=tavily`, `content_quality`, source domain, score, published date when present, and `cache_policy=derived_cache_allowed`.
- `BRAVE_SEARCH_API_KEY` absent: Brave Search is not registered in the app source map and SourceBroker ignores it.
- `BRAVE_SEARCH_API_KEY` present: Brave Search can be included as an optional source and ordered by scenario-aware source policy.
- Brave web results map title, URL, and description into `SearchResult`.
- Brave metadata includes `provider=brave`, `content_quality=snippet`, source domain, published date when present, and `cache_policy=transient_results_only` so downstream cache handling can respect restrictive result-storage terms.

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
