# RetroCause Mature Product Plan

> Updated: 2026-04-12
> Purpose: define a quality-first, cost-aware, rate-limit-resilient product strategy for RetroCause across OSS and future Pro.

---

## 1. Executive Summary

RetroCause should optimize for one hard promise:

> turn a why-question into an inspectable explanation artifact that is honest about evidence quality, freshness, and uncertainty.

That means the product should not compete on "always live" or "always more sources."
It should compete on:

- evidence quality
- trustworthy degradation
- structured explanation value
- repeatable workflows where users need to inspect and communicate causality

The system should remain usable under throttling, avoid pretending weak evidence is strong, and control cost by bounding retrieval rather than chasing the whole web.

---

## 2. Design Principles

1. Quality is the top constraint.
2. Availability matters, but not at the cost of false confidence.
3. Retrieval must be budgeted.
4. Freshness must be explicit.
5. Time-sensitive queries must be treated differently from evergreen queries.
6. OSS should remain runnable and honest.
7. Pro should justify payment through repeatability, reliability, and workflow completion.

---

## 3. Debate Summary

This plan was stress-tested through three conflicting lenses:

### Architecture-quality position

- strongest point: evidence tiering and quality gates must be the contract, not just metadata
- rebuttal to naive alternatives:
  - "just search more" increases noise and rate-limit pressure
  - "just cache everything" breaks time-sensitive correctness
  - "just move to Rust" does not solve evidence quality by itself

### Cost/ops position

- strongest point: rate limits and burst cost are product constraints, not incidental implementation issues
- rebuttal to naive alternatives:
  - "retry until it works" amplifies cost and throttling
  - "unlimited parallelism" creates burst failure and queue starvation
  - "make OSS depend on premium sources" breaks low-friction OSS usability

### Product/UX position

- strongest point: users must understand whether a result is current, cached, partial, or synthetic before they trust it
- rebuttal to naive alternatives:
  - "hide demo or partial states" destroys trust
  - "make everything real-time" is a cost trap
  - "launch a huge domain-pack catalog" creates shallow, hard-to-maintain product breadth

### Final synthesis

The winning strategy is:

- quality-gated retrieval
- time-aware caching
- explicit degradation to `partial_live`
- narrow, valuable OSS scope
- Pro value built around repeated workflows and stronger operational substrate

---

## 4. Product Thesis

RetroCause is most valuable when the user does not merely want an answer.
It is strongest when the user wants:

- competing explanations
- evidence they can inspect
- uncertainty that is visible
- an artifact they can explain to someone else

Weak use cases:

- simple fact lookup
- one-shot casual chat
- situations where the user does not care about evidence provenance

Strong use cases:

- event and market postmortems
- company or policy shock analysis
- historical and strategic retrospectives
- repeated explanation workflows for teams, clients, or stakeholders

---

## 5. Quality Contract

RetroCause should never blur quality states.

### 5.1 Runtime modes

- `live`
  - trusted or high-grade evidence is present
  - freshness requirements are met
  - fallback summaries do not dominate
  - at least one trusted anchor or cross-source support exists

- `partial_live`
  - live evidence exists
  - some freshness, coverage, or source-quality requirement is weak
  - the product remains usable, but the result is explicitly downgraded

- `demo`
  - no meaningful live run was available
  - the system returns an explicit demonstration artifact

### 5.2 Evidence tiers

Recommended evidence hierarchy:

1. `trusted_fulltext`
2. `fulltext`
3. `structured_source`
4. `trusted_snippet`
5. `snippet`
6. `cache_reuse`
7. `fallback_summary`

Rules:

- only top tiers should be able to anchor causal edges
- low tiers may support exploration, but should not significantly raise confidence
- `fallback_summary` should never be allowed to silently dominate a run

### 5.3 Time contract

All time-sensitive queries must carry an explicit or inferred time window.

Examples:

- stock or market move: trading day or intraday bucket
- breaking news: last 24h
- incident update: last 24h or last 7d depending on query shape
- historical question: broad window, freshness less important

Stable background evidence may be reused widely.
Fresh event evidence must be time-bucketed.

---

## 6. Retrieval Architecture

The mature retrieval pattern should be:

1. query classification
2. topic canonicalization
3. time-window inference
4. local evidence-store lookup
5. bounded discovery search
6. small-number page-body fetch
7. evidence extraction and scoring
8. quality gating
9. reasoning over filtered evidence

### 6.5 Current architecture gaps

The current OSS architecture already has the right outer contract:

- explicit `live` / `partial_live` / `demo`
- evidence tiers
- time-aware caching
- local evidence reuse

But recent live debugging shows four gaps still block broad reliability:

1. query understanding is still fragile
   - decomposition can emit placeholder template queries
   - Chinese and multilingual questions are not yet consistently rewritten into search-effective forms

2. source routing is too generic
   - time-sensitive geopolitics, finance, and policy queries should not route like evergreen science questions
   - academic sources are still overused in scenarios where web, official statements, or market/news evidence should lead

3. provider and model availability is still discovered too late
   - auth, region, and model-access failures should be detected before the full retrieval pipeline starts

4. live eligibility is not yet scenario-tuned enough
   - the quality bar should remain high
   - but the path to `live` must be reachable for each supported scenario, not only for ideal multi-source runs

### 6.6 Current implemented improvements

The OSS implementation now moves several quality/cost controls into the default live path:

- Evidence Access Layer is now a real service boundary in `retrocause/evidence_access.py`, covering query planning, scenario-aware source brokering, multi-source search aggregation, quality-first result sorting, short-lived search caching, source pacing, source cooldown, and retrieval trace output
- API V2 and the homepage can now surface retrieval trace rows, so users can see what the system searched, which sources responded, which results came from cache, and which sources failed or cooled down
- scenario-aware source routing sends geopolitical/news questions to AP News, Federal Register, GDELT, and web before academic sources
- AP News can provide trusted fulltext evidence for time-sensitive diplomatic and policy questions
- Federal Register can provide official trusted fulltext for policy/regulatory questions such as export controls, sanctions, tariffs, and semiconductor restrictions
- GDELT is treated as a paced broad-discovery adapter rather than an unlimited fan-out source
- generated retrieval queries are rejected if they are generic, placeholder-like, or invent years not present in the user question
- Chinese questions can be rewritten into English search-effective queries while preserving the original query as fallback, and policy questions now reject generic rewrites that drop event-specific anchors
- fulltext remains the preferred evidence substrate, but prompt payloads are compacted before LLM extraction to control latency and cost
- geopolitical/news queries now have a bounded second-source coverage rule: if the first source yields thin evidence, the collector continues across another scenario-fit adapter before stopping
- extracted evidence from merged source batches is best-effort attributed to the source result it actually matches, preserving provenance when news and official-source results are extracted together
- graph evidence linking now tolerates snake_case vs natural-language variable differences, reducing unnecessary CausalRAG retries
- online debate refinement is opt-in for `from_env()` interactive runs because it is expensive and does not replace evidence quality
- the homepage now exposes retrieval progress as a step trace and lets users click chains, connected edges, and evidence rows to inspect why a graph element is highlighted

These changes are intended to make `live` reachable without lowering the quality bar: the product still prefers trusted fulltext evidence, but avoids wasteful calls that do not improve evidence quality.

### 6.1 Query classification

Classify queries into:

- evergreen / historical
- time-sensitive / market / news
- long-tail exploratory

This determines freshness window, cache policy, and retrieval budget.

### 6.2 Topic canonicalization

Cache and coalescing keys should be based on:

- entity
- event type
- locale
- time window

Not just raw text.

### 6.3 Evidence store

Use a local high-quality evidence store for:

- repeated queries
- related queries
- curated topic packs
- strong background evidence

Do not treat it as a full web mirror.
Treat it as a reusable quality asset.

### 6.4 Discovery vs evidence

Web search should be discovery-first.

- search results identify candidates
- only a few high-value pages are fetched
- only page-body or structured evidence should become high-grade evidence

Search snippets alone are not enough for strong confidence.

---

## 7. Cost and Rate-Limit Strategy

RetroCause should not aim for "never rate-limited."
It should aim for "rate-limited without becoming unusable."

### 7.1 Hard budgets

Starting interactive envelope:

- search batches per query: 1
- sources per batch: up to 3
- page-body fetches: 1 to 2, rarely 3
- targeted retry rounds: 1
- online debate rounds: 0 by default, opt-in for deeper analysis
- hard stop: return `partial_live` after budget exhaustion

Raise budgets only when telemetry proves quality gains justify the extra cost.

### 7.2 Request coalescing

For hot topics:

- coalesce requests for 30 to 120 seconds
- run one refresh job for many near-identical users
- serve multiple users from the same fresh evidence window

### 7.3 Multi-layer caching

- search-result cache
- page-body cache
- extracted-evidence cache
- curated topic-pack cache

Caches must be freshness-aware.
Time-sensitive evidence must not leak across wrong time windows.

### 7.4 Source health and cooling

Each source should maintain:

- success rate
- timeout rate
- 429 rate
- latency
- freshness quality
- estimated cost per success

When a source degrades:

- cool it down
- lower its priority
- do not keep it in the critical path indefinitely

### 7.5 Concurrency policy

- cap per-query fan-out
- serialize or lightly parallelize page fetches per domain
- avoid retry storms
- prefer cached answers over queue starvation

### 7.6 Cost posture by scenario

RetroCause should not spend the same retrieval budget on every question.

Recommended budget classes:

- evergreen / historical
  - spend more on store reuse and curated background evidence
  - spend less on fresh discovery

- news / geopolitics / policy
  - spend more on fresh discovery and trusted-domain fulltext fetch
  - spend less on academic lookups

- market / company move
  - spend first on time-windowed event evidence
  - reuse background pack only as labeled context
  - stop early if fresh evidence remains too thin

- long-tail exploratory
  - stay on the cheapest bounded path
  - degrade honestly instead of chasing expensive, low-reuse retrieval

---

## 8. User Trust UX

Trust UX is not documentation garnish.
It is the product surface.

Every result should show:

- mode: `live`, `partial_live`, `demo`
- freshness status
- evidence mix
- confidence and uncertainty
- what is missing

The UI should answer:

- how current is this result
- how strong is the evidence
- what part is background vs fresh event evidence
- whether I should trust this for a real decision

Do not hide degraded states.
Honest degradation is part of the product.

---

## 9. Domain Packs

Domain packs should be curated product units, not prompt presets.

Each pack should define:

- target use case
- allowed source classes
- trusted domains
- freshness windows
- evidence requirements
- output conventions

Recommended first packs:

- market move analysis
- company postmortem
- policy shock analysis
- crisis timeline and causal update

Do not launch too many packs early.
Few strong packs are better than many shallow ones.

### 9.1 Scenario packs before broad domain packs

Before building many named domain packs, RetroCause should first support a smaller set of scenario-level operating modes:

- evergreen explanation
- breaking-news explanation
- market move explanation
- policy / geopolitical explanation
- company postmortem explanation

Reason:

- these scenario modes directly control routing, freshness, budgets, and quality gates
- they solve more real product behavior than a large but shallow catalog of domain labels

---

## 10. OSS Plan

OSS should deliver the full product idea clearly and honestly.

### OSS goals

- ask a why-question
- see competing chains
- inspect evidence
- see quality and freshness states
- understand uncertainty
- reuse local high-quality evidence
- remain usable under moderate throttling

### OSS constraints

- no dependency on expensive premium feeds for basic usability
- bounded retrieval budgets
- transparent limits
- easy local setup
- contribution-friendly architecture

### OSS should not optimize for

- heavy persistent workspaces
- team collaboration
- enterprise audit trails
- premium connectors as requirements
- deep multi-agent orchestration as the core promise

---

## 11. Pro Plan

Pro should not be "OSS plus more tokens."
It should complete repeated workflows.

### Pro value

- stronger real-analysis reliability
- premium and authenticated source access
- background refresh jobs
- saved workspaces and history
- comparison history
- report export
- collaboration and stakeholder communication
- customer-specific corpora and connectors
- domain packs for repeated high-value jobs

### Pro architecture direction

The current likely direction remains:

- OSS on the current Python + FastAPI + Next.js stack
- Pro as a separate operationally stronger product line, potentially with a Rust full-stack runtime

Important caveat:

- Rust is an implementation choice, not the quality thesis
- quality still depends mainly on evidence selection, grounding, evaluation, calibration, and failure handling

---

## 12. Metrics

The product should be managed by metrics, not intuition.

Minimum metrics:

- live success rate
- partial_live rate
- demo rate
- fallback-summary share
- cache hit rate
- request coalescing hit rate
- source success / timeout / 429 rate
- p95 latency
- cost per resolved query
- trusted-evidence share
- freshness-window compliance for time-sensitive queries

Interpretation:

- a higher cache hit rate is good only if freshness compliance remains healthy
- a rising partial_live rate is acceptable only if answers remain useful and honest
- a rising fallback-summary share is a quality alarm
- a rising cost per resolved query is an operating alarm

Additional scenario metrics:

- live rate by scenario class
- partial_live top reasons by scenario class
- provider preflight failure rate
- decomposition rejection rate
- trusted fulltext share by scenario class
- query rewrite hit rate for Chinese and multilingual queries

---

## 13. Open-Source Implementation Guidance

The mature plan should be informed by adjacent open-source systems, but not copied mechanically.

### 13.1 What to borrow

Borrow these patterns aggressively:

- per-source and per-domain rate limiting
- token-bucket or points-per-duration budgets
- adaptive backoff
- request coalescing for hot topics
- queue-based refresh for heavier retrieval paths
- strong separation between discovery search and evidence-grade fetch

### 13.2 What not to borrow blindly

Avoid these traps:

- turning RetroCause into a general crawler
- assuming more agents solve rate limits or evidence quality
- assuming premium search alone solves trust
- assuming a Rust rewrite solves epistemic correctness

### 13.3 RetroCause-specific conclusion

RetroCause has a harder job than generic web agents because retrieval quality directly affects:

- graph structure
- hypothesis quality
- anchoring quality
- user trust in the explanation artifact

So our adaptation must keep the quality contract in front of the ops contract:

- first gate evidence quality
- then budget retrieval
- then degrade honestly

---

## 14. Phased Roadmap

### Phase 1: honest OSS resilience

- enforce quality gates for `live`
- improve time-aware caching keys
- add request coalescing
- strengthen trusted-domain and fulltext handling
- expose clearer freshness and evidence quality in UI
- add provider/model preflight before live runs
- reject placeholder decomposition output and fall back to safer rewrite paths
- add scenario-aware source routing

### Phase 2: curated repeat workflows

- add first domain packs
- add better query classification and time-window inference
- add stronger evaluation gating
- add better exports for explanation artifacts
- add multilingual query rewrite and scenario-specific retrieval prompts
- add source health scoring into routing decisions
- add scenario-level budget tuning from telemetry

### Phase 3: Pro workflow completion

- background refresh jobs
- persistent workspace/history
- premium sources and connectors
- collaboration and reporting
- operational SLA and stronger queueing substrate

---

## 15. Non-Goals

Do not optimize for:

- scraping the whole web
- answering every query fully live
- hiding degraded states to feel more polished
- using more agents as a substitute for better evidence
- making OSS depend on premium infrastructure

---

## 16. Bottom Line

The mature RetroCause strategy is:

- quality first
- bounded live retrieval
- time-aware evidence reuse
- explicit degradation
- OSS for honest product understanding
- Pro for repeated, higher-trust workflow value

If RetroCause follows this plan, it can become a product users actually want to return to:

- because it is useful when evidence is strong
- because it remains usable when sources are weak
- and because it tells the truth about which of those two situations they are in

To make that true across more scenarios, the next architecture optimizations are not "more agents" or "more search."
They are:

- better query understanding
- better scenario routing
- earlier provider failure detection
- tighter cost envelopes per scenario
- clearer criteria for when `live` is reachable
