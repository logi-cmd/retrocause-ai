# RetroCause Manual Smoke Test

## Goal

Quickly verify that the OSS demo is runnable, understandable, and does not mislead users about demo vs real analysis.

## Environment

- Python 3.10+
- Node.js / npm available
- Dependencies installed
- Optional: model API key if you want to compare real analysis vs demo mode

## Launch

```bash
pip install -e ".[dev]"
cd frontend && npm install && cd ..
python start.py
```

Expected:

- frontend reachable at `http://localhost:3005`
- backend reachable at `http://127.0.0.1:8000`

If port `3005` is already occupied, stop the existing Next.js dev server first.

---

## Scenario 1 — Initial load

1. Open the frontend homepage.
2. Confirm the page renders with the white evidence-board UI.
3. Confirm left / center / right three-panel layout is visible.
4. Confirm no obvious dark-terminal leftovers remain in the active view.

Expected:

- white / paper-like visual system
- header + status bar visible
- hypothesis list visible
- chain / graph area visible
- right-side detail area visible
- query area reads as an investigation brief, with provider/API-key controls collapsed under advanced settings
- provider settings show OpenRouter as the fixed OSS provider rather than a multi-provider dropdown
- command bar shows coverage/source health chips when live or partial-live evidence is available
- left and right panels can be hidden from subtle embedded controls and restored from low-emphasis edge tabs
- the center view hint avoids the old "drag canvas" wording, stays away from the bottom drag area, and does not block dragging evidence notes
- canvas zoom controls are visible near the top of the board, can zoom in/out, and can reset to 100%
- dragging a single sticky note downward leaves only a compact bottom safety area, so the lower canvas remains usable without clipping the note

---

## Scenario 2 — Demo mode transparency

1. Submit a query without configuring a real model backend.
2. Inspect the top informational banner.

Expected:

- banner says current result is in demo mode
- banner shows the user query text
- UI does **not** imply the returned chain is a real analyzed result for that exact question

---

## Scenario 3 — Query flow

Try queries such as:

- `Why did SVB collapse?`
- `Why did the 2008 financial crisis happen?`
- `为什么某股票暴跌？`

Expected:

- request completes without frontend crash
- hypothesis list updates or remains usable
- chain view remains interactive
- right panel remains coherent
- expanding and collapsing provider settings does not clear the query
- submit button remains visually disabled while the query is empty or a run is loading

---

## Scenario 3.5 — Browser UI local real-analysis path

1. Open the homepage left panel.
2. Enter a supported provider mode.
3. Paste a valid API key.
4. Submit a query.

Expected:

- request body includes `query`, `model`, and `api_key`
- homepage does not claim hosted/SaaS-grade credential handling
- if the backend succeeds, the board is labeled as live analysis
- after completion, the status panel can show source trace rows with source name, query text, hit count, cache marker, or source error/cooldown
- if the backend fails, the board falls back to explicitly labeled demo data

---

## Scenario 3.5b - Back-to-back live query isolation

1. Submit a live query about one topic, for example Iran talks.
2. Immediately submit a different live query, for example `美国为什么会推出新的半导体出口管制？`.
3. Watch the status strip and evidence board while the second run is in flight.

Expected:

- the board switches to the second query immediately instead of keeping the old completed board as if it were current
- stale SSE events from the first request do not overwrite the second request
- the final result query and evidence topic match the second request
- the evidence list does not reuse thin CJK overlap from an unrelated prior query

---

## Scenario 3.6 — Streamlit demo honesty

1. Launch `streamlit run retrocause/app/entry.py` without an API key.
2. Observe the initial screen.
3. Run a query without entering a key.

Expected:

- Streamlit shows a persistent demo warning banner
- the result is clearly presented as demo/example output
- the demo can be topic-aware rather than always defaulting to the dinosaur example
- the app does not silently imply the result is real analysis

---

## Scenario 4 — Multi-hop tracing

1. Click a node in the main chain.
2. Confirm the node becomes selected.
3. Check the right panel for upstream causes.
4. Click one upstream cause in the right panel.

Expected:

- selected path is visually highlighted
- right panel updates for the clicked node
- upstream causes can be traversed step-by-step
- switching chain B and then chain A updates the active chain state without console border shorthand warnings

---

## Scenario 5 — View switching

Switch across all available views:

- Chain view
- Causal graph view
- Debate view
- Table view

Expected:

- no rendering error
- all views follow the evidence-board design language
- no old black-terminal theme remains in these views

---

## Scenario 6 — Evidence readability

1. Select a node with incoming evidence.
2. Inspect the evidence section in the right panel.

Expected:

- evidence is grouped clearly
- reliability distinctions are visible
- weights / labels are readable

---

## Scenario 7 — Fallback resilience

1. Stop or break backend availability.
2. Reload frontend and submit a query.

Expected:

- frontend does not hard crash
- connection state reflects failure
- app falls back to usable demo data or safe state

---

## Command Checks

Run these before release:

```bash
python -m pytest tests/ -v
ruff check retrocause/
cd frontend && npm run build
```

Expected:

- pytest passing
- ruff passing
- Next.js build passing

---

## Known environment caveats

- On Windows consoles, direct Python stdout may display UTF-8 Chinese text as garbled if the console encoding is GBK. This does **not** necessarily mean the FastAPI JSON response is wrong.
- Browser automation may fail if Chrome/Playwright browser binaries are not installed locally.

---

## Recent real-analysis validation

Local validation on 2026-04-12 used OpenRouter DeepSeek with the query:

- `为什么美国会同意与伊朗进行首轮谈判？`

Observed result:

- `analysis_mode=live`
- `freshness_status=mixed`
- 15 v2 evidence items
- 5 v2 chains
- 6 variables
- 6 edges
- evidence methods included `llm_fulltext_trusted` and `store_cache`
- GDELT failed during the run, but the product still returned a live evidence chain instead of demo fallback

Manual expectation for this scenario:

- geopolitics/news questions should route through scenario-fit sources instead of academic-first sources
- the UI should show a streaming retrieval trace while the pipeline is running
- evidence coverage should not collapse to only one or two causal evidence items when another bounded scenario-fit adapter is available
- broad-source failures should degrade through other bounded sources instead of silently becoming demo fallback

Latest local validation on 2026-04-12 also used OpenRouter DeepSeek with the query:

- `美国为什么会推出新的半导体出口管制？`

Observed result:

- `analysis_mode=live`
- `freshness_status=mixed`
- 16 v2 evidence items
- 2 v2 chains
- 7 unique nodes
- 7 unique edges
- evidence methods included `llm_fulltext_trusted` and `store_cache`
- evidence sources included both `NEWS` and official `ARCHIVE`
- Federal Register official documents supplied trusted full-text policy evidence
- no stale Iran-topic evidence appeared in the result

Manual expectation for this scenario:

- Chinese policy questions should keep event-specific retrieval anchors such as `semiconductor` and `export controls`
- generic rewrites like `United States why reasons diplomacy foreign policy` should be rejected
- public-news source weakness should be offset by bounded official-source retrieval when the query is regulatory/policy-shaped
- extracted evidence should be attributed to its best matching source result, not blindly to the first result in a merged batch

Latest clean browser validation on 2026-04-12 used Playwright against a freshly started FastAPI backend and Next.js frontend with the same query:

- `美国为什么会推出新的半导体出口管制？`

Observed browser result:

- `/api/analyze/v2/stream` returned a non-demo live result
- 8 causal graph cards were rendered by default
- 7 chain buttons were available for comparison
- switching between Chinese and English preserved all 8 graph cards instead of resetting to demo/default state
- clicking a graph card and clicking hypothesis-chain controls produced no console errors or page errors
- chain-compare controls must support B -> A switching with the selected chain reflected by `aria-pressed`, and must not mix React inline border shorthand with side-specific border properties
- locale persistence must be applied after hydration, so stored English/Chinese preference does not create a React hydration mismatch on first render

Regression command:

- set `RETROCAUSE_OPENROUTER_KEY`
- start backend on `127.0.0.1:8000`
- start frontend on `localhost:3005`
- run `npx -y -p playwright node scripts/_qa_frontend_live.js`

Quality expectation for this scenario:

- live/news/policy graph construction should not accept a collapsed 3-4 node graph when the evidence supports a broader causal DAG
- if the first LLM graph is too narrow, the graph builder may spend one extra model call to retry for broader evidence-supported coverage
- the default board should prefer the evidence-wide causal map when the DAG is broader than any single root-to-outcome path

Latest clean browser validation on 2026-04-12 also covered a time-sensitive crypto/finance query:

- `比特币今日价格为何跳水`

Observed browser result:

- `/api/analyze/v2/stream` returned a non-demo live result
- 8 causal graph cards were rendered by default
- 7 chain buttons were available for comparison
- Chinese-mode graph cards passed the localization check instead of rendering mostly English variable labels
- switching between Chinese and English preserved all 8 graph cards
- clicking a graph card and clicking hypothesis-chain controls produced no console errors or page errors

Regression command:

- set `RETROCAUSE_OPENROUTER_KEY`
- set `RETROCAUSE_QA_SCENARIO=bitcoin`
- set `RETROCAUSE_QA_MIN_CARDS=6`
- set `RETROCAUSE_QA_EXPECTED_PATTERN=比特币|Bitcoin|BTC|加密货币`
- start backend on `127.0.0.1:8000`
- start frontend on `localhost:3005`
- run `npx -y -p playwright node scripts/_qa_frontend_live.js`

Quality expectation for this scenario:

- Chinese crypto market-move questions should parse as `finance`, not `general`
- retrieval queries should preserve `Bitcoin`, `BTC`, `price`, and selloff/drop anchors
- finance/crypto graphs should use the same low-coverage retry gate as live news/policy questions
- Chinese UI cards should not expose mostly English market/policy variable labels
