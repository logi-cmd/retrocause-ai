# RetroCause Operational Plan

> Scope: cost control, rate-limit resilience, caching, concurrency budgets, source strategy, and OSS vs Pro operational split.

## 1. Operating Goal

RetroCause should be:

- quality first
- usable under source throttling
- honest when it degrades
- cheap enough to run on modest OSS infrastructure

The product must not collapse into "demo only" just because one source or one query path is slow.

## 2. Operating Principles

1. Prefer `partial_live` over silent failure.
2. Prefer bounded budgets over open-ended retries.
3. Prefer high-quality cached evidence over repeated low-value upstream calls.
4. Separate stable background knowledge from fresh event evidence.
5. Treat source outages and 429s as normal operating conditions, not exceptions.
6. Keep OSS runnable on small infrastructure; reserve higher operational complexity for Pro.

## 2.1 Current bottlenecks from recent debugging

Recent end-to-end debugging exposed a more concrete operating picture:

- provider auth or model-access failures can still consume a full live attempt unless preflighted earlier
- query decomposition can generate unusable placeholder subqueries
- generic source routing wastes budget on low-fit sources for time-sensitive questions
- public-source fragility is not rare edge behavior, it is normal operating behavior

This matters because the product cost problem is not only "too many requests."
It is also "too many bad requests."

Operationally, the highest-leverage savings come from stopping doomed runs earlier.

## 2.2 Implemented live-path hardening

The current OSS live path now includes these safeguards:

- evidence retrieval now passes through `retrocause/evidence_access.py` instead of letting each collector path call adapters directly
- query planning identifies domain, time window, language, coarse entities, and scenario before source selection
- source brokering routes market/news/policy/academic questions to scenario-fit source classes while still honoring `RETROCAUSE_ENABLED_SOURCES`
- search aggregation combines multiple adapters and sorts results by quality tier before LLM extraction
- source pacing, short-lived search-result caching, and source cooldown are centralized so one failed source does not trigger repeated high-frequency calls
- API V2 responses can expose retrieval trace rows showing source, query, result count, cache hit, and source error/cooldown status
- model-access preflight before expensive retrieval starts
- query-decomposition validation for placeholder/generic causal prompts
- unanchored-year rejection, so a query without a date cannot silently become a stale year-specific search
- Chinese time-sensitive/geopolitical questions prefer English retrieval queries while retaining the original Chinese query as fallback
- Chinese policy/regulatory questions reject over-generic rewrites unless event-specific anchors are preserved
- geopolitics routes to `ap_news`, `federal_register`, `gdelt`, then `web`, with AP and official fulltext able to satisfy the first live evidence budget before slower fallback sources are used
- Federal Register is only active for policy-shaped queries such as export controls, sanctions, tariffs, and semiconductor regulation, avoiding unnecessary calls for ordinary diplomatic-event questions
- trusted fulltext is still preferred, but extraction prompts are bounded to a compact evidence window to avoid oversized LLM calls
- evidence extracted from merged source batches is attributed back to the best matching source result, instead of blindly inheriting the first result's source metadata
- graph variables and extracted evidence are linked with snake_case/natural-language matching so high-quality evidence is not lost because of formatting mismatch
- interactive `from_env()` runs keep debate refinement off by default; debate remains available for deeper/offline runs with `RETROCAUSE_DEBATE_MAX_ROUNDS`

Cold-start validation on the query "为什么美国会同意与伊朗进行首轮谈判？" with OpenRouter DeepSeek and AP News returned `analysis_mode=live` with trusted fulltext evidence, graph variables, anchored edges, and hypothesis chains in about one minute on the local test machine.

Policy-query validation on "美国为什么会推出新的半导体出口管制？" returned `analysis_mode=live` with 16 evidence items, mixed NEWS/ARCHIVE sources, Federal Register trusted fulltext, 2 chains, 7 nodes, and 7 edges. GDELT is therefore no longer a single point of failure for this class of query.

## 3. Query Classes

RetroCause should not route every question the same way.

### 3.1 Evergreen / historical

Examples:

- "Why did SVB collapse?"
- "Why did the Roman Empire collapse?"

Recommended handling:

- favor cached evidence, curated topic packs, and authoritative background sources
- freshness window can be broad
- repeated queries should reuse the local evidence store aggressively

### 3.2 Time-sensitive / market / news

Examples:

- "Why did this stock fall today?"
- "Why is this company down this morning?"

Recommended handling:

- require a time window in the cache key
- default to a trading-day or 24h freshness window
- never let yesterday's event evidence explain today's move without an explicit background label

### 3.3 Long-tail exploratory

Examples:

- one-off open-world queries with little reuse potential

Recommended handling:

- bounded live retrieval
- explicit `partial_live` if evidence remains thin
- do not over-invest search budget when reuse probability is low

### 3.4 Policy / geopolitical / diplomatic events

Examples:

- "Why did the US agree to talks with Iran?"
- "Why did country X change its tariff stance this week?"

Recommended handling:

- treat as time-sensitive unless clearly historical
- prioritize AP/GDELT/web, trusted official domains, and reporting-oriented sources
- avoid sending the first retrieval budget to academic sources
- require explicit freshness and provenance surfacing because narratives can shift quickly

## 4. Retrieval Budgets

The current architecture already leans toward low fan-out. The operational rule should be stricter:

- cap the interactive path at a small, predictable upstream budget
- keep source fan-out shallow
- stop searching when the quality threshold is met or the budget is exhausted

Initial target budgets:

- search batches per query: 1
- sources per batch: 3 to 4, depending on scenario fit
- page-body fetches per query: 1 to 2, with 3 only for trusted domains
- targeted retry rounds: 1
- total hard stop: if evidence quality is still weak after the budget, return `partial_live`

This is an initial operating envelope, not a permanent ceiling. Raise it only when telemetry proves the extra spend improves evidence quality.

### 4.1 Bounded expansion for thin geopolitical/news coverage

For policy, geopolitical, and news-like questions, the first successful source can still be too narrow.
The current OSS path therefore allows a small quality-first expansion before declaring the evidence set sufficient:

- keep only a small number of scenario-specific subqueries
- require at least two source adapters to be attempted when available
- include official regulatory sources for policy-shaped queries before broad-discovery fallbacks
- require a stronger high-quality evidence count before stopping early
- preserve the hard stop and return `partial_live` if the wider bounded pass still cannot meet quality requirements

This is intentionally not "search more until something appears."
It is a constrained coverage rule: broaden source coverage when the result would otherwise be too thin, but do not let fan-out grow unbounded.

### 4.2 Stop-loss rules

To keep cost controlled, the live path should stop early when one of these conditions is met:

- provider/model preflight fails
- decomposition output is rejected as template-like or low-specificity
- source routing produces no viable source class for the scenario
- enough trusted evidence has already been collected
- remaining budget can no longer improve the mode above `partial_live`

This turns budget policy into a quality-preserving stop-loss, not a crude throttle.

## 5. Coalescing and Caching

Cache design should be layered, not monolithic.

### 5.1 Request coalescing

- Canonicalize queries into a topic key: entity + event type + locale + time window.
- Coalesce identical or near-identical requests for 30 to 120 seconds.
- For hot topics, one refresh job should serve multiple users.

Expected effect:

- duplicate burst traffic can often be reduced by a large factor on the same topic window
- the exact gain depends on traffic shape, but repeated-event workloads should see the biggest benefit

### 5.2 Cache layers

- search-result cache: short TTL, used to avoid repeated search fan-out
- page-body cache: short to medium TTL, used to avoid repeated fetches of the same URL
- evidence cache: medium TTL, stores extracted high-quality evidence
- topic pack cache: long TTL, stores curated or manually reviewed evidence for repeat topics

### 5.3 Freshness boundaries

- never reuse event evidence across the wrong time window
- relative windows such as `today`, `yesterday`, and `trading_day` must be converted into absolute calendar buckets before cache/store reuse
- live retrieval queries for relative windows should carry concrete date context, so "yesterday" on different days cannot collapse into the same search/cache key
- explicitly dated source results outside the inferred window must be filtered before LLM evidence extraction and graph construction
- undated results for strong fresh-news and market windows must show a target-date signal in the title, URL, snippet, or fetched page text; otherwise they should be treated as insufficiently fresh rather than used as event evidence
- stable background evidence may be reused across days or weeks
- fresh event evidence must remain time-bucketed

### 5.4 Cache policy by evidence class

- stable background evidence
  - long TTL
  - broad reuse
  - safe for store packing

- fresh event evidence
  - short TTL
  - strict time-bucket reuse only
  - must carry captured-at metadata

- degraded fallback evidence
  - short TTL
  - should never become a durable quality asset
  - should not be promoted into the high-quality evidence store

## 6. Concurrency Budgets

The important limit is not just "how many requests can we fire," but "how much of the pipeline can fan out at once without hurting quality."

Recommended starting policy:

- one query should trigger only a small number of concurrent upstream actions
- page-body fetches should be serialized or lightly parallelized per domain
- source adapters should each have their own circuit breaker and cooldown
- if the queue is full, serve a cached or `partial_live` response instead of letting the request stall indefinitely

Operationally, this is safer than unlimited parallelism because:

- it limits burst cost
- it reduces 429 amplification
- it prevents a single hot topic from starving the rest of the system

### 6.1 Concurrency should follow scenario fit

Recommended default shape:

- evergreen queries
  - more reuse, less concurrency

- breaking-news and market queries
  - slightly more fresh retrieval concurrency
  - still capped by domain and source health

- long-tail queries
  - lowest concurrency and shortest stop-loss window

This keeps cost aligned with expected user value and reuse probability.

## 7. Source Strategy

### 7.1 OSS source policy

OSS should favor sources that are:

- free or low-cost
- observable
- cacheable
- legally and operationally low risk

Good OSS candidates:

- the local high-quality evidence store
- official reports and authoritative domains
- arXiv / academic metadata
- web search used as discovery, not as the final truth source

OSS should treat expensive or fragile sources as opportunistic supplements, not dependencies.

### 7.2 Pro source policy

Pro can justify more operational complexity if it buys reliability and quality.

Good Pro candidates:

- authenticated search APIs
- licensed news or market feeds
- private corpora and customer connectors
- domain-specific ingestion pipelines

### 7.3 Source health model

Every source should have a live health profile:

- success rate
- p95 latency
- recent 429/timeout count
- freshness quality
- estimated cost per successful retrieval

If a source degrades, it should be cooled down or disabled rather than kept in the critical path.

### 7.4 Source routing policy

Source choice should be scenario-native:

- evergreen / science / history
  - evidence store
  - academic or archival sources
  - selective web supplement

- policy / geopolitics / breaking news
  - AP News first when available for trusted fulltext journalism
  - GDELT as a broad discovery layer with strict pacing/cooldown
  - trusted web and official domains first
  - web fulltext before snippet-heavy fallback
  - academic sources only as secondary context

- market / company move
  - time-windowed news, company statements, filings, and market-context sources first
  - evidence store only as labeled background context

The operational mistake to avoid is "same source set for every query."

## 8. Quality Gates

The system should only label a run as `live` when the evidence is genuinely strong.

Proposed gate conditions:

- at least one trusted anchor or two independent evidence classes
- no single source class dominates the run
- fallback-summary evidence does not dominate the causal chain
- time-sensitive questions have evidence inside the required freshness window
- unresolved conflicts are explicitly surfaced instead of smoothed over

If these conditions are not met, the run should be `partial_live` and explain what is missing.

### 8.1 Live must be reachable

The quality bar should stay strict, but not impossible.

For each scenario, define a reachable `live` contract:

- evergreen
  - strong reused evidence plus one trusted live confirmation may be enough

- breaking-news / geopolitics
  - fresh trusted fulltext from a small number of strong sources may be enough

- market move
  - fresh event evidence plus clearly separated background evidence may be enough

If `live` only happens when every source works perfectly, the mode is not operationally meaningful.

## 9. OSS vs Pro, Operationally

### OSS should optimize for

- bounded cost
- transparent degradation
- low setup friction
- local caches and local evidence reuse
- single-machine or small-container deployability
- inspectability for contributors and early users

### Pro should optimize for

- higher throughput
- queue-based background refresh
- persistent workspaces
- team sharing and auditability
- private data and customer-specific corpora
- premium source reliability
- stronger SLA and support expectations

### Practical boundary

- OSS should not depend on paid feeds to remain usable.
- Pro may use paid feeds to improve freshness, coverage, and reliability.
- OSS should remain understandable without hidden infrastructure.
- Pro can add managed infrastructure where it materially improves repeated use.

## 10. Metrics That Matter

Track the following at minimum:

- live success rate
- partial_live rate
- fallback-summary share
- cache hit rate
- request coalescing hit rate
- source success / timeout / 429 rate
- p95 end-to-end latency
- cost per resolved query

Suggested interpretation:

- rising cache hit rate with stable quality is good
- rising partial_live rate is acceptable only if the user still gets a useful answer
- rising fallback-summary share is a quality warning
- rising cost per resolved query means the source mix or budgets need adjustment

Also track:

- provider preflight failure rate
- scenario routing mismatch rate
- decomposition rejection rate
- stop-loss exit rate before retrieval
- cost per scenario class

## 11. Non-Goals

Do not turn RetroCause OSS into:

- a generic crawler
- an always-online full web mirror
- a feature-limited teaser for Pro
- a system that silently overstates confidence to hide limit failures

The operational goal is not "never hit a limit." The goal is "hit limits without losing the product."

---

## 12. Lessons From Open-Source Systems

Several adjacent open-source systems converge on the same pattern:

- they do not eliminate rate limits
- they make rate limits survivable through budgets, queues, caches, and explicit degradation

### 12.1 Crawl4AI-style lesson

What is useful:

- per-domain throttling
- adaptive backoff with jitter
- explicit dispatcher-level concurrency control

Why it matters for RetroCause:

- the web path should be controlled before requests are sent, not only after failures occur
- domain-specific cooldown is safer than one global switch
- page fetch concurrency should remain low and predictable

What not to copy blindly:

- RetroCause is not a generic crawler
- we should borrow the control model, not inherit crawler-level product scope

### 12.2 Firecrawl-style lesson

What is useful:

- queue-based async jobs
- background refresh for heavy retrieval
- resource admission thresholds
- operational separation between interactive requests and long-running fetch work

Why it matters for RetroCause:

- hot topics should not trigger duplicate interactive fan-out
- repeated live refresh should move into controlled background work
- the system should prefer serving a bounded answer over blocking the whole request path

What not to copy blindly:

- OSS should not become a queue-heavy managed crawling platform
- Firecrawl-like infrastructure belongs mostly to Pro or to a later optional OSS deployment mode

### 12.3 LangChain-style lesson

What is useful:

- simple token-bucket rate limiting at the client boundary
- explicit requests-per-second budgeting

Why it matters for RetroCause:

- every external source adapter should eventually have a pre-request budget, not only post-failure cooldown
- this is the simplest way to stop retry storms and accidental burst amplification

What not to copy blindly:

- in-memory limiter alone is not enough for multi-process or multi-instance deployments

### 12.4 Rate-limiter-flexible-style lesson

What is useful:

- points-per-duration budgeting
- block periods after overrun
- distributed limiter patterns using Redis

Why it matters for RetroCause:

- Pro can use distributed rate-limit state to coordinate burst traffic safely
- OSS can start with local limiter patterns, then optionally add a Redis-backed mode later

What not to copy blindly:

- rate limiting alone does not improve evidence quality
- limiter policy must remain subordinate to the quality contract

### 12.5 Unified conclusion

The strongest shared lesson is:

- mature systems do not solve rate limits by "trying harder"
- they solve them by spending less retrieval budget per user-visible answer

For RetroCause, that means:

- tighter budgets
- request coalescing
- time-aware caches
- source health control
- background refresh where justified
- explicit `partial_live` rather than silent failure or fake confidence

## 13. Immediate optimization backlog under the current architecture

The current OSS architecture does not need a rewrite to improve materially.
It needs a sharper operating layer.

Highest-priority optimizations:

1. Evidence Access Layer
   - implemented as `retrocause/evidence_access.py`
   - owns query planner, source broker, search aggregator, quality ordering, source pacing, short-lived cache, source cooldown, and retrieval trace metadata
   - keeps source adapters focused on a single upstream source instead of spreading routing/cost logic across adapters

2. provider/model preflight
   - fail fast on auth, region, or model-access issues
   - do not spend retrieval budget after a known provider failure

3. decomposition validation and fallback rewrite
   - reject placeholder outputs
   - fall back to safer canonicalized rewrite instead of shipping bad subqueries

4. scenario-aware source routing
   - route policy, geopolitics, and market questions away from academic-first paths

5. costed stop-loss policy
   - stop live runs once the remaining budget cannot realistically upgrade the mode

6. source-health-informed routing
   - incorporate recent 429 / timeout signals directly into routing decisions

7. multilingual retrieval normalization
   - improve Chinese and mixed-language searchability without forcing every question through brittle free-form decomposition

These items are the shortest path to better live reachability without giving up quality or cost discipline.
