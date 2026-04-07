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
- if the backend fails, the board falls back to explicitly labeled demo data

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
