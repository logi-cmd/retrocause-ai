"""SSE E2E test — verify real analysis (is_demo=False) through stream endpoint."""

import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

API_KEY = "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"
QUERY = "Why is the sky blue?"
MODEL = "deepseek/deepseek-chat-v3-0324"
BASE_URL = "https://openrouter.ai/api/v1"
ENDPOINT = "http://localhost:8001/api/analyze/v2/stream"

payload = {
    "query": QUERY,
    "api_key": API_KEY,
    "model_name": MODEL,
    "base_url": BASE_URL,
}

print(f"Query: {QUERY}")
print(f"Model: {MODEL}")
print(f"Endpoint: {ENDPOINT}")
print("---")

try:
    resp = requests.post(ENDPOINT, json=payload, stream=True, timeout=360)
    print(f"Status: {resp.status_code}")

    progress_events = []
    final_event = None

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        try:
            data = json.loads(line[6:])
        except json.JSONDecodeError:
            continue

        evt_type = data.get("type")

        if evt_type == "progress":
            step = data.get("step", "?")
            idx = data.get("step_index", "?")
            print(f"  [{idx}/9] {step}")
            progress_events.append(data)
        elif evt_type == "done":
            final_event = data
        elif evt_type == "error":
            print(f"  ERROR: {data}")

    print("\n=== FINAL RESULT ===")
    if final_event is None:
        print("FAIL: No 'done' event received!")
        sys.exit(1)

    is_demo = final_event.get("is_demo", True)
    error = final_event.get("error")
    result_data = final_event.get("data", {})

    print(f"is_demo: {is_demo}")
    print(f"error: {error}")

    if not is_demo and result_data:
        chains = result_data.get("chains", [])
        nodes_count = sum(len(c.get("nodes", [])) for c in chains)
        edges_count = sum(len(c.get("edges", [])) for c in chains)
        evidence_count = len(result_data.get("evidence_pool", []))

        print(f"hypotheses/chains: {len(chains)}")
        print(f"total nodes: {nodes_count}")
        print(f"total edges: {edges_count}")
        print(f"evidence items: {evidence_count}")

        if len(chains) > 0 and nodes_count > 0:
            print("\n✅ SSE E2E PASSED — real analysis returned!")
            sys.exit(0)
        else:
            print("\n❌ SSE E2E FAILED — is_demo=False but no chains/nodes")
            sys.exit(1)
    elif is_demo:
        print(f"\n❌ SSE E2E FAILED — still returning demo data")
        print(f"   error msg: {error}")
        sys.exit(1)
    else:
        print(f"\n❌ SSE E2E FAILED — unexpected state")
        sys.exit(1)

except requests.exceptions.Timeout:
    print("FAIL: Request timed out after 360s")
    sys.exit(1)
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
    sys.exit(1)
