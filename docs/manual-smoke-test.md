# RetroCause Manual Smoke Test

## Goal

Verify that the OSS browser/API path is runnable, keyless, understandable, and
honest about local/demo output.

## Environment

- Python 3.10+
- Node.js / npm available
- Dependencies installed
- No model or search provider key is required for the OSS smoke path

## Launch

```bash
pip install -e ".[dev]"
npm install
npm --prefix frontend install
python start.py
```

Expected:

- frontend reachable at `http://127.0.0.1:3005`
- backend reachable at `http://127.0.0.1:8000`
- homepage renders without asking for model/search credentials

## Scenario 1 - Initial Load

1. Open the frontend homepage.
2. Confirm the evidence board renders.
3. Confirm the query panel, graph board, source trace, saved runs, and uploaded
   evidence areas remain usable.
4. Open OSS analysis settings.

Expected:

- no provider key field is visible
- no search key field is visible
- no OpenRouter provider appears in the active catalog
- settings describe the keyless OSS boundary

## Scenario 2 - Keyless Query Flow

1. Submit `Why did SVB collapse?`.
2. Submit `Why did the 2008 financial crisis happen?`.
3. Submit `芯原股份今天盘中为什么下跌？` through the Chinese A-share sample.

Expected:

- each request completes without a frontend crash
- each result is explicitly local/demo or keyless OSS analysis
- graph cards, source trace, challenge coverage, and copyable Markdown remain
  available
- Chinese text is not visibly corrupted in the query or primary result labels

## Scenario 3 - Provider Compatibility Endpoints

Run:

```bash
curl http://127.0.0.1:8000/api/providers
```

Expected:

- response is HTTP 200
- response contains the active keyless provider catalog
- response does not contain `openrouter`

Run:

```bash
curl -X POST http://127.0.0.1:8000/api/providers/preflight ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"ofoxai\"}"
```

Expected:

- response is HTTP 200
- response status is `disabled`
- response explains that provider preflight is disabled in OSS

## Scenario 4 - Local Workflow Features

1. Run an analysis.
2. Reopen the saved-runs panel.
3. Upload a short pasted evidence note.
4. Reopen the saved run.

Expected:

- run id, run steps, and usage ledger are visible
- saved runs remain local
- pasted evidence is labeled as user-provided local evidence
- no hosted storage, team sharing, or credential handling is implied

## Scenario 5 - Narrow Viewport

1. Resize the browser to a narrow viewport.
2. Toggle side panels.
3. Pan or inspect the board.

Expected:

- panel controls remain visible
- text stays inside its containers
- graph paths do not produce `NaN` SVG values
- no console error appears for duplicate React keys

## Automated Commands

Run before release work:

```bash
npm test
python scripts/live_stability_probe.py
```

Expected:

- `npm test` passes
- the stability probe writes `.agent-guardrails/evidence/local-stability-probe.json`
- the probe report contains no secret fields

## Environment Caveats

- On Windows consoles, direct stdout may display UTF-8 Chinese text incorrectly
  even when FastAPI JSON is valid.
- On Windows PowerShell, send Chinese JSON as UTF-8 bytes if calling the API
  directly.
- Browser automation may need Playwright/Chromium installed locally.
