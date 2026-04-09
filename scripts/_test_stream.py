import requests
import json
import sys

query = sys.argv[1] if len(sys.argv) > 1 else "Why did dinosaurs go extinct?"
api_key = sys.argv[2] if len(sys.argv) > 2 else ""

print(f"Query: {query}")
print(f"API key: {api_key[:10]}..." if api_key else "No API key")
print("---")

resp = requests.post(
    "http://localhost:8000/api/analyze/v2/stream",
    json={"query": query, "api_key": api_key, "model": "openrouter"},
    stream=True,
    timeout=360,
)

print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('content-type')}")
print("---")

for line in resp.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data: "):
        continue
    payload = json.loads(line[6:])
    evt_type = payload.get("type")

    if evt_type == "progress":
        print(
            f"[{payload['step_index']}/{payload['total_steps']}] {payload['step']}: {payload['message']}"
        )
    elif evt_type == "done":
        is_demo = payload.get("is_demo")
        error = payload.get("error")
        print(f"\nDONE | is_demo={is_demo} | error={error}")
        if is_demo:
            print(">>> RETURNED DEMO FALLBACK <<<")
        else:
            chains = payload.get("data", {}).get("chains", [])
            print(
                f"Chains: {len(chains)}, first chain nodes: {len(chains[0]['nodes']) if chains else 0}"
            )
    elif evt_type == "error":
        print(f"ERROR: {payload.get('error')}")
    else:
        print(f"UNKNOWN: {payload}")
