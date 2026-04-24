# RetroCause OSS / Pro Positioning

> Updated: 2026-04-07
> Purpose: public explanation of what OSS should be, what Pro could become, why users might pay, and where the real moat must come from.

---

## 1. Core Product Thesis

RetroCause should not compete as “yet another AI answer box.”

Its strongest product thesis is:

> turn a vague why-question into an inspectable explanation artifact with visible competing chains, evidence links, and uncertainty signals.

That matters because users often do **not** just need an answer. They need something they can:

- inspect
- compare
- challenge
- explain to someone else
- revisit later

This is the center of gravity for both OSS and Pro.

---

## 2. What the OSS Version Should Do

The OSS version should be a **real product experience**, not a crippled teaser.

It should help users:

1. ask a why-question
2. see a structured causal chain instead of a blob of text
3. compare competing explanations
4. inspect supporting vs refuting evidence
5. see confidence / coverage / uncertainty signals
6. understand when the system is showing demo fallback instead of real analysis

### OSS release bar

The OSS version is ready to publish when it is:

- runnable by a GitHub visitor without guessing setup
- visually coherent and understandable
- explicit about its limitations
- stable enough that the main demo flow does not feel broken
- honest about real analysis vs demo mode

### OSS is not for

- guaranteed causal truth
- production decision support
- “trust us blindly” workflows

Its job is to make the product idea legible and useful.

---

## 3. What the Pro Version Should Be

The Pro version should not just mean “more tokens” or “more features.”

It should mean **better workflow outcomes** for users whose cost of being wrong is higher.

### Best Pro candidates

1. **Higher-trust real analysis**
   - better evidence handling
   - stronger source provenance
   - better uncertainty calibration
   - domain-specific prompts / templates / guardrails

2. **Richer comparison workflows**
   - compare multiple chains side-by-side
   - inspect support vs refutation balance
   - identify which assumptions drive the result most strongly

3. **Scenario and intervention workflows**
   - stronger what-if analysis
   - factor intervention panels
   - clearer sensitivity analysis and confidence degradation

4. **Team / client / report workflows**
   - saved workspaces
   - shareable explanation links
   - exportable explanation reports
   - explain-it-to-my-team views

5. **Higher-value domain packs**
   - market events
   - crisis analysis
   - investment/news postmortems
   - strategic retrospectives

6. **A more operationally robust product substrate**
   - streaming-first analysis UX
   - shared typed models from backend to frontend
   - lower-latency graph/layout operations
   - lower infra cost for sustained real-analysis usage

The current planning direction is that this substrate may live in a separate **full-stack Rust Pro architecture**, rather than being forced into the OSS stack by default.

### What should stay in OSS

- the core evidence-board idea
- basic why-question exploration
- visible competing chains
- visible uncertainty / demo labeling

### Architecture split

- **OSS should continue to ship on the current Python stack** (`FastAPI + Python pipeline + Next.js evidence board`).
- **Pro can diverge architecturally** if that materially improves reliability, streaming UX, shared typing, and cost structure.
- The current direction is to treat Pro as a **separate full-stack Rust line**, not as a thin feature gate over the OSS codebase.
- Operationally, OSS should stay budgeted, cache-heavy, and transparent about degradation, while Pro can add queue-based refresh, premium feeds, and higher-throughput workflows. The detailed policy lives in [`docs/operational-plan.md`](./operational-plan.md).

This split exists because the two products have different jobs:

- OSS must be runnable, inspectable, and contribution-friendly.
- Pro must be dependable enough for repeated, higher-stakes workflows.

If the core idea is hidden, OSS stops being a strong distribution engine.

---

## 4. Who Actually Has the Pain?

Not all users have the same pain.

### User segment A — curious explainers / early adopters

They want to understand complex events better than a normal chat answer.

Examples:

- “Why did SVB collapse?”
- “Why did the 2008 crisis happen?”
- “Why is rent so high?”

Pain level: **moderate**

They will try OSS. They may share screenshots. They are good for growth, but weak for monetization.

### User segment B — analysts / operators / strategy people

They need to explain a causal story to teammates, managers, clients, or stakeholders.

Examples:

- postmortems
- market event analysis
- startup failure retrospectives
- internal strategy memos

Pain level: **high**

They care about:

- competing explanations
- explicit uncertainty
- explainability to others
- reusable output

This is the strongest early Pro segment.

### User segment C — high-stakes knowledge workers

They work in settings where sloppy explanation is expensive.

Examples:

- finance
- risk research
- advisory
- policy / geopolitical analysis

Pain level: **very high**, but trust bar is also very high.

They will only pay if the product becomes materially more reliable than generic chat workflows.

---

## 5. Why Would Anyone Pay?

Users will not pay because the UI looks cool.

They will pay if RetroCause saves them time or reduces explanation risk in situations where a normal LLM answer is too weak.

### Real payment triggers

1. **I need to compare explanations, not just get one**
2. **I need to show where the answer came from**
3. **I need to explain this to another person clearly**
4. **I need visible uncertainty, not fake confidence**
5. **I need to reuse this analysis in repeated workflows**

### Weak payment triggers

- “AI but prettier”
- decorative graph output
- generic summarization with a causal label on top

---

## 6. Does It Solve a Real Scenario?

Yes — but only in a specific form.

RetroCause is most useful when the user needs an **explanation artifact**, not just a text answer.

Strong scenarios:

- understanding major events with multiple competing causes
- postmortems and retrospectives
- explaining complex events to a team or client
- comparing alternative causal narratives
- surfacing uncertainty and evidence thinness instead of hiding them

Weak scenarios:

- simple factual lookup
- one-shot casual chat
- cases where the user does not care about evidence or uncertainty

---

## 7. Difference vs ChatGPT / Perplexity

### ChatGPT / Claude

Strengths:

- fast
- flexible
- fluent

Weaknesses for this problem:

- explanation structure is unstable
- evidence provenance is usually weaker
- competing explanations are not first-class objects
- uncertainty often remains hidden in prose

### Perplexity

Strengths:

- stronger search/citation habit
- good answer engine for research summaries

Weaknesses for this problem:

- not built around explicit competing chains
- not built around causal comparison workflows
- not built around intervention / factor impact framing

### RetroCause advantage

Its advantage is not “more intelligence.”

Its advantage is:

- explanation as structure
- explicit evidence attachment
- explicit uncertainty signaling
- competing causal chains as first-class output
- a visual reasoning artifact people can inspect and discuss

### Hard truth

If RetroCause cannot deliver stable-enough live evidence for a scenario, and does not add meaningful structural value on top, users should use ChatGPT or a search-first tool instead.

That is not a messaging problem.
It is the core product test.

RetroCause only earns repeated use when it gives the user something harder to get from generic chat:

- better separation between background and fresh evidence
- time-window-aware explanations
- competing explanations with explicit support and weakness
- a reusable explanation artifact, not just a one-off answer

---

## 8. Is There a Real Moat?

### What is **not** a moat

- using many libraries
- a fancy graph UI by itself
- “we use AI plus graphs”
- generic LLM orchestration

### What could become a moat

1. **Better evidence-grounded explanation quality**
   - stronger evidence anchoring
   - better support/refutation handling
   - better calibration of confidence vs uncertainty

2. **Workflow-specific explanation output**
   - outputs tuned for postmortems, market events, retrospectives, stakeholder communication

3. **Trust-preserving product behavior**
   - explicit failure states
   - explicit demo labeling
   - refusal to overstate confidence

4. **Repeated-use assets and templates**
   - domain packs
   - reusable explanation structures
   - organization memory / saved workspaces / comparison history

5. **Data flywheel (only if built carefully)**
   - which evidence users keep or discard
   - which chains survive scrutiny
   - which interventions matter repeatedly in a domain

This is only a moat if the product learns from repeated use, not if it just stores logs.

### What recent evidence suggests

Recent high-signal references point in four practical directions:

1. **Evidence-grounded quality should be measured, not assumed**
   - RAG evaluation frameworks such as **RAGAS**, **TruLens**, and **Vectara FCS** all converge on the idea that explanation quality must be audited via context precision/recall, groundedness, and factual consistency.
   - For RetroCause, that means future moat should come from measuring:
     - evidence coverage
     - support vs refutation balance
     - factual consistency of explanation text
     - confidence / uncertainty calibration gaps

2. **Workflow-specific outputs beat generic answer generation**
   - Practical systems win when they produce artifacts tuned for the job: postmortems, market-event explainers, stakeholder summaries, and comparison reports.
   - This supports building Pro around repeated workflows where a user needs to explain causality to someone else, not just read it privately.

3. **Trust-preserving behavior is product design, not just model quality**
   - Strong patterns include explicit failure states, visible fallback labeling, progressive disclosure, and citation-aware verification.
   - RetroCause already has a seed of this with explicit `is_demo`, evidence tags, confidence/uncertainty signals, and support/refutation structure.
   - The moat comes from refusing fake confidence in ambiguous situations.

4. **Reusable domain packs can become a distribution and retention layer**
   - Anthropic-style skills / domain packs point toward reusable vertical workflows, not just prompt presets.
   - For RetroCause, the strongest packs are likely to be:
     - market event analysis
     - crisis / postmortem explanation
     - strategic retrospective workflows
     - policy / macro event explainers

### Strong external references

- **DoWhy** (causal refutation and robustness): https://github.com/py-why/dowhy
- **RAGAS** (groundedness and retrieval metrics): https://docs.ragas.io/
- **TruLens** (groundedness / feedback evaluation): https://github.com/truera/trulens
- **Vectara FCS integration** (factual consistency scoring): https://docs.langchain.com/oss/python/integrations/vectorstores/vectara
- **Anthropic Agent Skills** (reusable workflow packs): https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills
- **GitHub Copilot memory system** (trust-preserving verification and reusable organizational knowledge): https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot
- **Observable interpretable AI for data analysis** (progressive disclosure / visible work): https://observablehq.com/blog/playing-safely-with-fire-building-interpretable-ai-for-data-analysis

---

## 9. Recommended Product Strategy

### Frontier placement

**Good OSS frontier bets**:

- evidence-grounded evaluation
- citation-grounded explanation output
- support vs refutation balance
- lightweight graph-guided retrieval / CausalRAG-style retrieval
- uncertainty communication that makes weak evidence and weak chains explicit

These strengthen the core OSS promise: inspectable, honest, evidence-aware explanation.

**Better Pro-first frontier bets**:

- strong provenance ledger and reusable organization memory
- persistent workspaces and history
- heavy multi-agent workflows
- streaming long-running analysis UX
- stakeholder / client reporting flows
- reusable domain packs for repeated high-stakes explanation jobs

These are more naturally productized around repeated work, operational depth, and team use—not around first-touch OSS understanding.

### Near term

- finish the OSS version until it is honestly usable
- publish only when the demo path, docs, and trust signals are solid
- use OSS to validate repeated why-question interest and workflow behavior
- improve live reachability by fixing provider preflight, query rewrite, and source-routing gaps before adding broader surface area

### Medium term

- identify one high-value repeated workflow where explanation quality matters
- build Pro around that workflow instead of around generic feature gating

### Scenario strategy

Do not promise identical strength for every question shape.
Make RetroCause clearly better in a few scenario families first:

- market and company move explanations
- policy / geopolitical explanations
- postmortem and retrospective explanations
- historically grounded multi-cause explanations

The moat is not breadth alone.
It is that the system behaves correctly, honestly, and repeatably inside these scenario families.

### OSS and Pro optimization split

OSS should focus on:

- honest mode labeling
- bounded live retrieval
- scenario-aware routing
- local evidence reuse
- visible evidence quality and freshness

Pro should focus on:

- better source coverage and authentication
- stronger background refresh and hot-topic handling
- persistent workspaces and comparison history
- team-facing explanation workflows
- higher throughput with lower marginal cost per repeated analysis

### Product rule

> OSS should make users understand and like the product. Pro should make high-frequency users depend on it.

---

## 10. Bottom Line

RetroCause can become meaningful if it stays focused on a hard but real job:

> helping people inspect, compare, and communicate causal explanations more honestly than a normal chat answer.

That is a real pain.

But it only becomes a durable business if the Pro version improves:

- trust
- repeatability
- stakeholder communication
- workflow usefulness in settings where bad explanations are costly

Without that, it remains an impressive demo.

---

## 11. Related Docs

- [`docs/mature-product-plan.md`](./mature-product-plan.md) — unified quality-first, cost-aware, rate-limit-resilient product plan
- [`docs/operational-plan.md`](./operational-plan.md) — concrete operating policy for budgets, caching, and source resilience
