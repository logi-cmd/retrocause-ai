import json
import os
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")

API_KEY = (
    os.environ.get("OPENROUTER_API_KEY")
    or os.environ.get("RETROCAUSE_OPENROUTER_KEY")
    or ""
).strip()
MODEL = "deepseek/deepseek-chat-v3-0324"
QUERY = "MH370为什么失踪"
URL = "http://127.0.0.1:8001/api/analyze/v2/stream"

if not API_KEY:
    raise SystemExit("Set OPENROUTER_API_KEY or RETROCAUSE_OPENROUTER_KEY before running.")

print(f"Testing SSE: {QUERY}")
print(f"URL: {URL}")

import time

t0 = time.time()

try:
    resp = requests.post(
        URL,
        json={
            "query": QUERY,
            "api_key": API_KEY,
            "model": MODEL,
        },
        stream=True,
        timeout=500,
    )

    print(f"HTTP {resp.status_code}")
    is_demo = None
    error_msg = None
    chains_count = 0

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
        except json.JSONDecodeError:
            continue

        etype = event.get("type", "")
        if etype == "progress":
            idx = event.get("step_index", "?")
            total = event.get("total_steps", "?")
            msg = event.get("message", "")
            elapsed = time.time() - t0
            print(f"  [{elapsed:.0f}s] [{idx}/{total}] {msg}")
        elif etype == "done":
            is_demo = event.get("is_demo")
            error_msg = event.get("error")
            data = event.get("data", {})
            chains = data.get("chains", [])
            chains_count = len(chains)
            nodes = sum(len(c.get("nodes", [])) for c in chains)
            edges = sum(len(c.get("edges", [])) for c in chains)
            elapsed = time.time() - t0
            print(f"\n=== DONE ({elapsed:.1f}s) ===")
            print(f"is_demo={is_demo}")
            print(f"error={error_msg}")
            print(f"chains={chains_count} nodes={nodes} edges={edges}")
            break
        elif etype == "error":
            error_msg = event.get("error")
            elapsed = time.time() - t0
            print(f"\n=== ERROR ({elapsed:.1f}s) ===")
            print(f"error={error_msg}")
            break

except Exception as e:
    elapsed = time.time() - t0
    print(f"FAILED ({elapsed:.1f}s): {type(e).__name__}: {e}")
