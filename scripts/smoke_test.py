import httpx
import sys

BASE = "http://127.0.0.1:8000"
pass_count = 0
fail_count = 0


def check(name, condition, detail=""):
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f"  PASS  {name}")
    else:
        fail_count += 1
        print(f"  FAIL  {name} -- {detail}")


# === Backend Root ===
print("\n=== Backend Root ===")
r = httpx.get(f"{BASE}/")
check("root returns 200", r.status_code == 200)
check("root says ok", r.json().get("status") == "ok")

# === V2 API -- SVB query (demo) ===
print("\n=== V2 API -- SVB query (demo mode) ===")
r = httpx.post(f"{BASE}/api/analyze/v2", json={"query": "Why did SVB collapse?"}, timeout=30)
data = r.json()
check("V2 SVB returns 200", r.status_code == 200)
check("is_demo is True", data.get("is_demo") is True)
check("demo_topic is svb", data.get("demo_topic") == "svb")
check("has 1 chain", len(data.get("chains", [])) == 1)
check("chain has nodes", len(data["chains"][0].get("nodes", [])) > 0)
check("chain has edges", len(data["chains"][0].get("edges", [])) > 0)
check("has evidences", len(data.get("evidences", [])) > 0)
check("recommended_chain_id set", data.get("recommended_chain_id") == "demo_svb_primary")
check("upstream_map exists", "entries" in data.get("upstream_map", {}))

# === V2 API -- Dinosaur query (default demo) ===
print("\n=== V2 API -- Dinosaur query (default demo) ===")
r = httpx.post(
    f"{BASE}/api/analyze/v2", json={"query": "Why did dinosaurs go extinct?"}, timeout=30
)
data = r.json()
check("V2 dino returns 200", r.status_code == 200)
check("is_demo is True", data.get("is_demo") is True)
check("demo_topic is default", data.get("demo_topic") == "default")
check("has 2 chains", len(data.get("chains", [])) == 2, f"got {len(data.get('chains', []))}")
check("recommended is h1", data.get("recommended_chain_id") == "h1")
c0 = data["chains"][0]
check("chain h1 has counterfactual", len(c0.get("counterfactual", {}).get("items", [])) > 0)
check(
    "nodes have valid types",
    all(
        n.get("type") in ["cause", "effect", "mediator", "confounder"] for n in c0.get("nodes", [])
    ),
)
check(
    "node probabilities in [0,1]",
    all(0 <= n.get("probability", -1) <= 1 for n in c0.get("nodes", [])),
)
check(
    "edge strengths in [0,1]",
    all(0 <= e.get("strength", -1) <= 1 for e in c0.get("edges", [])),
)

# === V2 API -- stock query ===
print("\n=== V2 API -- Stock query ===")
r = httpx.post(f"{BASE}/api/analyze/v2", json={"query": "为什么某股票暴跌？"}, timeout=30)
data = r.json()
check("V2 stock returns 200", r.status_code == 200)
check("demo_topic is stock", data.get("demo_topic") == "stock")

# === V2 API -- crisis query ===
print("\n=== V2 API -- Crisis query ===")
r = httpx.post(f"{BASE}/api/analyze/v2", json={"query": "2008 financial crisis causes"}, timeout=30)
data = r.json()
check("V2 crisis returns 200", r.status_code == 200)
check("demo_topic is crisis", data.get("demo_topic") == "crisis")

# === V2 API -- rent query ===
print("\n=== V2 API -- Rent query ===")
r = httpx.post(
    f"{BASE}/api/analyze/v2", json={"query": "Why is rent so high in New York?"}, timeout=30
)
data = r.json()
check("V2 rent returns 200", r.status_code == 200)
check("demo_topic is rent", data.get("demo_topic") == "rent")

# === V1 API backward compat ===
print("\n=== V1 API -- Backward compatibility ===")
r = httpx.post(f"{BASE}/api/analyze", json={"query": "Why did SVB collapse?"}, timeout=30)
data = r.json()
check("V1 returns 200", r.status_code == 200)
check("V1 has nodes", len(data.get("nodes", [])) > 0)
check("V1 has edges", len(data.get("edges", [])) > 0)
check("V1 is_demo is True", data.get("is_demo") is True)

# === Edge/variable integrity ===
print("\n=== V2 API -- Edge/variable integrity ===")
r = httpx.post(f"{BASE}/api/analyze/v2", json={"query": "Why did SVB collapse?"}, timeout=30)
data = r.json()
for chain in data["chains"]:
    var_ids = {n["id"] for n in chain["nodes"]}
    for edge in chain["edges"]:
        src, tgt = edge["source"], edge["target"]
        check(
            f"edge {src}->{tgt} refs valid vars",
            src in var_ids and tgt in var_ids,
            f"source={src} target={tgt} vars={var_ids}",
        )

# === Frontend serves HTML ===
print("\n=== Frontend ===")
r = httpx.get("http://localhost:3005", timeout=15)
check("Frontend returns 200", r.status_code == 200)
check("HTML contains RetroCause", "RetroCause" in r.text or "retrocause" in r.text.lower())
check("HTML has React root", "__next" in r.text or "root" in r.text)

# === Summary ===
print(f"\n{'=' * 50}")
print(f"Total: {pass_count + fail_count} | PASS: {pass_count} | FAIL: {fail_count}")
if fail_count > 0:
    sys.exit(1)
else:
    print("All smoke tests passed!")
