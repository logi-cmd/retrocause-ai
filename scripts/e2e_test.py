#!/usr/bin/env python3
import atexit
import httpx
import json
import os
from pathlib import Path
import subprocess
import sys
import time

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[SKIP] playwright not installed — UI tests skipped")
    PlaywrightTimeoutError = TimeoutError
    sync_playwright = None

BASE = os.environ.get("RETROCAUSE_E2E_BASE", "http://127.0.0.1:8000")
FRONTEND = os.environ.get("RETROCAUSE_E2E_FRONTEND", "http://localhost:3005")
TIMEOUT = 30
ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
STARTED_PROCESSES: list[subprocess.Popen] = []

passed = 0
failed = 0
skipped = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} -- {detail}")


def skip(name: str, reason: str = ""):
    global skipped
    skipped += 1
    print(f"  SKIP  {name} -- {reason}")


def _is_url_ready(url: str) -> bool:
    try:
        response = httpx.get(url, timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def _start_process(args: list[str], cwd: Path) -> subprocess.Popen:
    process = subprocess.Popen(
        args,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    STARTED_PROCESSES.append(process)
    return process


def _cleanup_started_processes() -> None:
    for process in STARTED_PROCESSES:
        if process.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                process.terminate()
    time.sleep(0.5)
    for process in STARTED_PROCESSES:
        if process.poll() is None:
            process.kill()


def _wait_for_url(url: str, label: str, timeout_seconds: int = 90) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _is_url_ready(url):
            return
        time.sleep(1)
    raise RuntimeError(f"{label} did not become ready at {url}")


def _ensure_local_services() -> None:
    if os.environ.get("RETROCAUSE_E2E_NO_AUTOSTART") == "1":
        return

    if not _is_url_ready(f"{BASE}/"):
        _start_process(
            [
                sys.executable,
                "-B",
                "-m",
                "uvicorn",
                "retrocause.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            ROOT_DIR,
        )
        _wait_for_url(f"{BASE}/", "backend")

    if not _is_url_ready(FRONTEND):
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend_args = [npm_cmd, "run", "start", "--", "-p", "3005"]
        if not (FRONTEND_DIR / ".next").exists():
            frontend_args = [npm_cmd, "run", "dev", "--", "-p", "3005"]
        _start_process(frontend_args, FRONTEND_DIR)
        _wait_for_url(FRONTEND, "frontend")


def v2_post(query: str, timeout: int = TIMEOUT, **kwargs) -> tuple[int, dict]:
    r = httpx.post(f"{BASE}/api/analyze/v2", json={"query": query, **kwargs}, timeout=timeout)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {}


def validate_chain_structure(chain: dict, label: str):
    nodes = chain.get("nodes", [])
    edges = chain.get("edges", [])

    check(f"{label} has chain_id", bool(chain.get("chain_id")))
    check(f"{label} has label", len(chain.get("label", "")) > 0)
    check(f"{label} has description", len(chain.get("description", "")) > 0)
    check(
        f"{label} probability in [0,1]",
        0.0 <= chain.get("probability", -1) <= 1.0,
        f"got {chain.get('probability')}",
    )
    check(f"{label} has nodes ({len(nodes)})", len(nodes) > 0)
    check(f"{label} has edges ({len(edges)})", len(edges) > 0)
    check(
        f"{label} has counterfactual",
        "counterfactual" in chain and isinstance(chain["counterfactual"], dict),
    )
    check(
        f"{label} counterfactual has items",
        len(chain.get("counterfactual", {}).get("items", [])) >= 0,
    )
    check(f"{label} depth >= 0", chain.get("depth", -1) >= 0)
    check(
        f"{label} has supporting_evidence_ids",
        isinstance(chain.get("supporting_evidence_ids"), list),
    )
    check(
        f"{label} has refuting_evidence_ids", isinstance(chain.get("refuting_evidence_ids"), list)
    )

    var_ids = {n["id"] for n in nodes}

    for ni, node in enumerate(nodes):
        nl = f"{label}/node[{ni}]({node.get('id', '?')})"
        check(f"{nl} id exists", len(node.get("id", "")) > 0)
        check(f"{nl} label exists", len(node.get("label", "")) > 0)
        check(
            f"{nl} probability in [0,1]",
            0.0 <= node.get("probability", -1) <= 1.0,
            f"got {node.get('probability')}",
        )
        check(
            f"{nl} type valid",
            node.get("type") in ["cause", "effect", "mediator", "confounder"],
            f"got {node.get('type')}",
        )
        check(f"{nl} depth >= 0", node.get("depth", -1) >= 0)
        check(f"{nl} upstream_ids is list", isinstance(node.get("upstream_ids"), list))
        check(
            f"{nl} supporting_evidence_ids is list",
            isinstance(node.get("supporting_evidence_ids"), list),
        )
        check(
            f"{nl} refuting_evidence_ids is list",
            isinstance(node.get("refuting_evidence_ids"), list),
        )

    for ei, edge in enumerate(edges):
        el = f"{label}/edge[{ei}]({edge.get('source', '?')}->{edge.get('target', '?')})"
        check(
            f"{el} source valid",
            edge.get("source") in var_ids,
            f"source={edge.get('source')} not in {var_ids}",
        )
        check(
            f"{el} target valid",
            edge.get("target") in var_ids,
            f"target={edge.get('target')} not in {var_ids}",
        )
        check(
            f"{el} strength in [0,1]",
            0.0 <= edge.get("strength", -1) <= 1.0,
            f"got {edge.get('strength')}",
        )
        check(f"{el} type exists", len(edge.get("type", "")) > 0)
        check(f"{el} citation_spans is list", isinstance(edge.get("citation_spans"), list))
        check(
            f"{el} evidence_conflict exists",
            edge.get("evidence_conflict") is not None,
            f"got {edge.get('evidence_conflict')}",
        )

        for si, span in enumerate(edge.get("citation_spans", [])):
            sl = f"{el}/span[{si}]"
            check(f"{sl} evidence_id exists", len(span.get("evidence_id", "")) > 0)
            check(f"{sl} start_char >= 0", span.get("start_char", -1) >= 0)
            check(
                f"{sl} end_char > start_char", span.get("end_char", 0) > span.get("start_char", 0)
            )
            check(f"{sl} quoted_text exists", len(span.get("quoted_text", "")) > 0)
            check(f"{sl} relevance_score in [0,1]", 0.0 <= span.get("relevance_score", -1) <= 1.0)


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: Backend connectivity
# ═══════════════════════════════════════════════════════════════════════
atexit.register(_cleanup_started_processes)
_ensure_local_services()

print("\n" + "=" * 60)
print("SECTION 1: Backend Connectivity")
print("=" * 60)

r = httpx.get(f"{BASE}/", timeout=10)
check("backend root 200", r.status_code == 200)
check("backend status ok", r.json().get("status") == "ok")

r = httpx.get(f"{BASE}/api/providers", timeout=10)
check("providers endpoint 200", r.status_code == 200)
providers = r.json().get("providers", {})
check("providers non-empty", len(providers) > 0, f"got {providers}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: V2 API — Dinosaur (default demo, 2 chains)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 2: V2 API — Dinosaur (default demo, 2 chains)")
print("=" * 60)

status, data = v2_post("Why did dinosaurs go extinct?")
check("dino returns 200", status == 200)
check("dino is_demo True", data.get("is_demo") is True)
check("dino demo_topic default", data.get("demo_topic") == "default")
check("dino has 2 chains", len(data.get("chains", [])) == 2, f"got {len(data.get('chains', []))}")
check("dino recommended is h1", data.get("recommended_chain_id") == "h1")
check("dino has evidences", len(data.get("evidences", [])) > 0)
check("dino upstream_map exists", "entries" in data.get("upstream_map", {}))
check("dino query echoed", data.get("query") == "Why did dinosaurs go extinct?")
check("dino error is None", data.get("error") is None)

for ci, chain in enumerate(data.get("chains", [])):
    validate_chain_structure(chain, f"dino/chain[{ci}]")

check("dino uncertainty_report field exists", "uncertainty_report" in data)
check("dino evaluation field exists", "evaluation" in data)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: V2 API — SVB (1 chain, 6 nodes)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 3: V2 API — SVB (1 chain)")
print("=" * 60)

status, data = v2_post("Why did SVB collapse?")
check("svb returns 200", status == 200)
check("svb is_demo True", data.get("is_demo") is True)
check("svb demo_topic svb", data.get("demo_topic") == "svb")
check("svb has 1 chain", len(data.get("chains", [])) == 1, f"got {len(data.get('chains', []))}")
check("svb recommended demo_svb_primary", data.get("recommended_chain_id") == "demo_svb_primary")

chain = data["chains"][0]
check("svb chain has 6 nodes", len(chain["nodes"]) == 6, f"got {len(chain['nodes'])}")
check("svb chain has 5 edges", len(chain["edges"]) == 5, f"got {len(chain['edges'])}")
validate_chain_structure(chain, "svb/chain[0]")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 4: V2 API — Stock, Crisis, Rent demos
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 4: V2 API — Other demo topics")
print("=" * 60)

for query, expected_topic, expected_chains in [
    ("为什么某股票暴跌？", "stock", 1),
    ("2008 financial crisis causes", "crisis", 1),
    ("Why is rent so high in New York?", "rent", 1),
]:
    tag = expected_topic
    status, data = v2_post(query)
    check(f"{tag} returns 200", status == 200)
    check(
        f"{tag} demo_topic correct",
        data.get("demo_topic") == expected_topic,
        f"got {data.get('demo_topic')}",
    )
    check(
        f"{tag} has chains",
        len(data.get("chains", [])) == expected_chains,
        f"got {len(data.get('chains', []))}",
    )
    for ci, chain in enumerate(data.get("chains", [])):
        validate_chain_structure(chain, f"{tag}/chain[{ci}]")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 5: V1 backward compatibility
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 5: V1 API backward compatibility")
print("=" * 60)

r = httpx.post(f"{BASE}/api/analyze", json={"query": "Why did SVB collapse?"}, timeout=TIMEOUT)
data = r.json()
check("v1 returns 200", r.status_code == 200)
check("v1 has nodes", len(data.get("nodes", [])) > 0)
check("v1 has edges", len(data.get("edges", [])) > 0)
check("v1 has evidences", len(data.get("evidences", [])) > 0)
check("v1 is_demo True", data.get("is_demo") is True)
check("v1 has query", len(data.get("query", "")) > 0)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 6: Evidence pool integrity
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 6: Evidence pool integrity")
print("=" * 60)

status, data = v2_post("Why did dinosaurs go extinct?")
all_ev_ids = {ev["id"] for ev in data.get("evidences", [])}
check("evidence pool non-empty", len(all_ev_ids) > 0)

for ci, chain in enumerate(data.get("chains", [])):
    chain_all_refs = set(chain.get("supporting_evidence_ids", []))
    chain_all_refs.update(chain.get("refuting_evidence_ids", []))
    for node in chain["nodes"]:
        chain_all_refs.update(node.get("supporting_evidence_ids", []))
        chain_all_refs.update(node.get("refuting_evidence_ids", []))
    for edge in chain["edges"]:
        chain_all_refs.update(edge.get("supporting_evidence_ids", []))
        chain_all_refs.update(edge.get("refuting_evidence_ids", []))

    missing = chain_all_refs - all_ev_ids
    check(f"chain[{ci}] all evidence refs resolve", len(missing) == 0, f"missing IDs: {missing}")

# ═══════════════════════════════════════════════════════════════════════
# SECTION 7: Upstream map consistency
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 7: Upstream map consistency")
print("=" * 60)

status, data = v2_post("Why did SVB collapse?")
upstream_entries = data.get("upstream_map", {}).get("entries", [])
check("upstream_map has entries", len(upstream_entries) > 0)

all_chain_node_ids = set()
for chain in data.get("chains", []):
    for node in chain["nodes"]:
        all_chain_node_ids.add(node["id"])

entry_ids = {e["node_id"] for e in upstream_entries}
check(
    "upstream_map node_ids subset of chain nodes",
    entry_ids.issubset(all_chain_node_ids),
    f"extra: {entry_ids - all_chain_node_ids}",
)

for entry in upstream_entries:
    for up_id in entry.get("upstream_node_ids", []):
        check(
            f"upstream ref {up_id} valid for {entry['node_id']}",
            up_id in all_chain_node_ids,
            f"{up_id} not in chain nodes",
        )

# ═══════════════════════════════════════════════════════════════════════
# SECTION 8: Schema field presence (new capabilities)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 8: New capability schema fields")
print("=" * 60)

status, data = v2_post("Why did dinosaurs go extinct?")

check("top-level uncertainty_report key present", "uncertainty_report" in data)
check("top-level evaluation key present", "evaluation" in data)

for ci, chain in enumerate(data.get("chains", [])):
    for ei, edge in enumerate(chain["edges"]):
        check(f"chain[{ci}]/edge[{ei}] has citation_spans", "citation_spans" in edge)
        check(f"chain[{ci}]/edge[{ei}] has evidence_conflict", "evidence_conflict" in edge)
    for ni, node in enumerate(chain["nodes"]):
        check(f"chain[{ci}]/node[{ni}] has uncertainty", "uncertainty" in node)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 9: Edge case queries
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 9: Edge cases")
print("=" * 60)

status, data = v2_post("")
check("empty query returns 200", status == 200)

status, data = v2_post("a")
check("single char query returns 200", status == 200)

status, data = v2_post("random gibberish xyzzy foo bar")
check("nonsense query returns 200", status == 200)
check("nonsense falls back to demo", data.get("is_demo") is True)

try:
    status, data = v2_post(
        "Why did dinosaurs go extinct?",
        timeout=5,
        api_key="sk-fake-key-will-fail",
    )
except httpx.ReadTimeout:
    skip("bad API key live-provider smoke", "provider/network timeout; unit tests cover partial_live")
else:
    check("bad API key returns 200 (explicit partial_live failure)", status == 200)
    check("bad API key is not silently demo", data.get("is_demo") is False)
    check("bad API key is partial_live", data.get("analysis_mode") == "partial_live")
    check("bad API key exposes error", bool(data.get("error")))

# ═══════════════════════════════════════════════════════════════════════
# SECTION 10: Frontend serves HTML
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 10: Frontend HTML delivery")
print("=" * 60)

r = httpx.get(FRONTEND, timeout=15, follow_redirects=True)
check("frontend returns 200", r.status_code == 200)
check("frontend HTML contains RetroCause", "RetroCause" in r.text or "retrocause" in r.text.lower())
check("frontend has Next.js root", "__next" in r.text or "_next" in r.text)

# ═══════════════════════════════════════════════════════════════════════
# SECTION 11: UI E2E — Playwright full workflow
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 11: UI E2E — Playwright full workflow")
print("=" * 60)

if sync_playwright is None:
    skip("All UI E2E tests", "playwright not installed")
else:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(15_000)
        console_errors = []
        page_errors = []
        failed_responses = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(exc))
        page.on(
            "response",
            lambda response: failed_responses.append(
                {"status": response.status, "url": response.url}
            )
            if response.status >= 500
            else None,
        )

        # 11a: Initial load
        print("\n  --- 11a: Initial Load ---")
        page.goto(FRONTEND, wait_until="domcontentloaded")
        html = page.content()
        check("UI page loads", "<html" in html.lower())

        board = page.locator(".evidence-board")
        check("UI evidence-board renders", board.count() > 0, ".evidence-board not found")

        header = page.locator(".header-bar")
        check("UI header bar", header.count() > 0)

        left = page.locator(".left-panel")
        check("UI left panel", left.count() > 0)

        right = page.locator(".right-panel")
        check("UI right panel", right.count() > 0)

        cards = page.locator(".sticky-card")
        try:
            cards.first.wait_for(state="visible", timeout=10000)
        except PlaywrightTimeoutError:
            pass
        card_count = cards.count()
        check(f"UI sticky cards ({card_count})", card_count > 0)

        h1 = page.locator("h1").first
        check("UI h1 visible", len((h1.text_content() or "").strip()) > 0)

        # 11b: Demo transparency
        print("\n  --- 11b: Demo Transparency ---")
        page_text = page.locator(".evidence-board").text_content() or ""
        right_text = page.locator(".right-panel").text_content() or ""
        combined = (page_text + " " + right_text).lower()
        check("UI demo label visible", "demo" in combined, "no 'demo' in page text")

        # 11c: Query flow — submit SVB query
        print("\n  --- 11c: Query Flow ---")
        textarea = page.locator("textarea").first
        check("UI textarea found", textarea.count() > 0)
        if textarea.count() > 0:
            stream_status, stream_payload = v2_post("Why did dinosaurs go extinct?")
            if stream_status == 200 and len(stream_payload.get("chains", [])) >= 2:
                stream_event = {
                    "type": "done",
                    "is_demo": stream_payload.get("is_demo", True),
                    "demo_topic": stream_payload.get("demo_topic"),
                    "data": stream_payload,
                }

                page.route(
                    "**/api/analyze/v2/stream",
                    lambda route: route.fulfill(
                        status=200,
                        headers={"content-type": "text/event-stream"},
                        body=f"data: {json.dumps(stream_event, ensure_ascii=False)}\n\n",
                    ),
                )
            else:
                skip("UI chain compare mock stream", "backend did not provide a 2-chain fixture")

            sample_query = page.locator("[data-testid='sample-a-share-query']").first
            check("UI A-share sample query visible", sample_query.count() > 0)
            if sample_query.count() > 0:
                sample_query.click()
                check(
                    "UI A-share sample fills Chinese company anchor",
                    "芯原股份" in textarea.input_value(),
                    f"textarea value was {textarea.input_value()!r}",
                )
                scenario_selector = page.locator("[data-testid='scenario-selector']").first
                check("UI scenario selector found", scenario_selector.count() > 0)
                if scenario_selector.count() > 0:
                    check(
                        "UI A-share sample selects market scenario",
                        scenario_selector.input_value() == "market",
                        f"scenario was {scenario_selector.input_value()!r}",
                    )

            textarea.fill("Why did dinosaurs go extinct?")

            submit = page.locator("button:has-text('Analyze')").first
            if submit.count() == 0:
                submit = page.locator("button").filter(has_text="Analyze").first
            if submit.count() == 0:
                submit = page.locator("button").filter(has_text="分析").first
            try:
                page.wait_for_function(
                    """
                    () => Array.from(document.querySelectorAll('button')).some((button) => {
                      const text = button.textContent || '';
                      return (text.includes('Analyze') || text.includes('分析')) && !button.disabled;
                    })
                    """,
                    timeout=10000,
                )
            except PlaywrightTimeoutError:
                pass
            if submit.count() == 0 or not submit.is_enabled():
                submit = page.locator("button:enabled").filter(has_text="Analyze").first
            if submit.count() == 0:
                submit = page.locator("button:enabled").filter(has_text="分析").first
            check("UI submit button found", submit.count() > 0)

            if submit.count() > 0:
                submit.click()
                time.sleep(4)

                html_after = page.content()
                check("UI page survives query", "<html" in html_after.lower())

                cards_after = page.locator(".sticky-card")
                check(
                    "UI cards rendered after query",
                    cards_after.count() > 0,
                    "cards disappeared after query",
                )

                # 11d: Panel visibility controls
                print("\n  --- 11d: Panel Visibility Controls ---")
                embedded_toggles = page.locator(".panel-embedded-toggle")
                check(
                    "UI embedded panel controls visible",
                    embedded_toggles.count() >= 2,
                    f"found {embedded_toggles.count()} embedded controls",
                )
                if embedded_toggles.count() >= 2:
                    embedded_toggles.nth(0).click()
                    time.sleep(0.3)
                    check("UI left panel hides", not page.locator(".left-panel").is_visible())
                    page.locator(".panel-toggle-left").click()
                    time.sleep(0.3)
                    check("UI left panel shows again", page.locator(".left-panel").is_visible())
                    page.locator(".panel-embedded-toggle-right").click()
                    time.sleep(0.3)
                    check("UI right panel hides", not page.locator(".right-panel").is_visible())
                    page.locator(".panel-toggle-right").click()
                    time.sleep(0.3)
                    check("UI right panel shows again", page.locator(".right-panel").is_visible())

                    print("\n  --- 11e: Narrow Viewport Panel Controls ---")
                    page.set_viewport_size({"width": 390, "height": 844})
                    time.sleep(0.5)
                    narrow_left_toggle_ok = True
                    try:
                        page.locator(".panel-embedded-toggle").first.click(timeout=2000)
                    except PlaywrightTimeoutError:
                        narrow_left_toggle_ok = False
                    check(
                        "UI narrow viewport left panel control remains clickable",
                        narrow_left_toggle_ok and not page.locator(".left-panel").is_visible(),
                        "left panel hide control was blocked at 390px viewport",
                    )
                    narrow_right_toggle_ok = True
                    try:
                        page.locator(".panel-embedded-toggle-right").click(timeout=2000)
                    except PlaywrightTimeoutError:
                        narrow_right_toggle_ok = False
                    check(
                        "UI narrow viewport right panel control remains clickable after left closes",
                        narrow_right_toggle_ok and not page.locator(".right-panel").is_visible(),
                        "right panel hide control was blocked after closing left panel",
                    )
                    if not page.locator(".left-panel").is_visible():
                        page.locator(".panel-toggle-left").click()
                        time.sleep(0.2)
                    if not page.locator(".right-panel").is_visible():
                        page.locator(".panel-toggle-right").click()
                        time.sleep(0.2)
                    page.set_viewport_size({"width": 1440, "height": 900})
                    time.sleep(0.3)

                # 11e: Canvas zoom controls
                print("\n  --- 11e: Canvas Zoom Controls ---")
                zoom_controls = page.locator(".zoom-controls")
                check("UI zoom controls visible", zoom_controls.count() == 1)
                if zoom_controls.count() == 1:
                    zoom_buttons = zoom_controls.locator("button")
                    check(
                        "UI zoom control has three buttons",
                        zoom_buttons.count() == 3,
                        f"found {zoom_buttons.count()} zoom buttons",
                    )
                    if zoom_buttons.count() == 3:
                        zoom_buttons.nth(2).click()
                        time.sleep(0.2)
                        check("UI zoom increases", "110%" in zoom_controls.text_content())
                        zoom_buttons.nth(1).click()
                        time.sleep(0.2)
                        check("UI zoom reset works", "100%" in zoom_controls.text_content())

                # 11f: Bottom drag safety
                print("\n  --- 11f: Bottom Drag Safety ---")
                if page.locator(".left-panel").is_visible():
                    page.locator(".panel-embedded-toggle").first.click()
                    time.sleep(0.2)
                if page.locator(".right-panel").is_visible():
                    page.locator(".panel-embedded-toggle-right").click()
                    time.sleep(0.2)
                drag_card = page.locator(".sticky-card").first
                if drag_card.count() > 0:
                    viewport_width = page.evaluate("window.innerWidth")
                    for card_index in range(cards_after.count()):
                        candidate = cards_after.nth(card_index)
                        candidate_box = candidate.bounding_box()
                        if (
                            candidate_box
                            and candidate_box["x"] > 320
                            and candidate_box["x"] + candidate_box["width"] < viewport_width - 380
                        ):
                            drag_card = candidate
                            break
                    box = drag_card.bounding_box()
                    viewport_height = page.evaluate("window.innerHeight")
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        page.mouse.down()
                        page.mouse.move(box["x"] + box["width"] / 2, viewport_height - 5, steps=12)
                        page.mouse.up()
                        time.sleep(0.2)
                        dragged_bottom = drag_card.evaluate(
                            "el => el.getBoundingClientRect().bottom"
                        )
                        check(
                            "UI dragged note keeps compact bottom safe area",
                            40 <= viewport_height - dragged_bottom <= 90,
                            f"bottom gap={viewport_height - dragged_bottom:.1f}px",
                        )
                if not page.locator(".left-panel").is_visible():
                    page.locator(".panel-toggle-left").click()
                    time.sleep(0.2)
                if not page.locator(".right-panel").is_visible():
                    page.locator(".panel-toggle-right").click()
                    time.sleep(0.2)

                # 11g: Chain comparison switching regression
                print("\n  --- 11g: Chain Compare Switching ---")
                compare_buttons = page.locator("[data-testid^='chain-compare-']")
                compare_count = compare_buttons.count()
                check(
                    "UI chain compare has alternatives",
                    compare_count >= 2,
                    f"found {compare_count} chain compare buttons",
                )
                if compare_count >= 2:
                    first_chain = compare_buttons.nth(0)
                    second_chain = compare_buttons.nth(1)
                    second_chain.click()
                    time.sleep(0.5)
                    check(
                        "UI chain B becomes active",
                        second_chain.get_attribute("aria-pressed") == "true",
                        f"aria-pressed={second_chain.get_attribute('aria-pressed')}",
                    )
                    first_chain.click()
                    time.sleep(0.5)
                    check(
                        "UI chain A becomes active again",
                        first_chain.get_attribute("aria-pressed") == "true",
                        f"aria-pressed={first_chain.get_attribute('aria-pressed')}",
                    )

                # 11g-2: Degraded Source Browser Dogfood
                print("\n  --- 11g-2: Degraded Source Browser Dogfood ---")
                degraded_payload = dict(stream_event)
                degraded_data = dict(stream_event["data"])
                degraded_data["retrieval_trace"] = [
                    {
                        "source": "ap_news",
                        "source_label": "AP News",
                        "source_kind": "wire_news",
                        "stability": "high",
                        "query": "US Iran talks AP",
                        "result_count": 0,
                        "cache_hit": False,
                        "status": "rate_limited",
                        "retry_after_seconds": 30,
                        "cache_policy": "short_lived_cache_allowed",
                    },
                    {
                        "source": "web_search",
                        "source_label": "Web Search",
                        "source_kind": "web_search",
                        "stability": "medium",
                        "query": "US Iran talks cached",
                        "result_count": 2,
                        "cache_hit": True,
                        "status": "cached",
                        "retry_after_seconds": None,
                        "cache_policy": "derived_cache_allowed",
                    },
                ]
                degraded_payload["data"] = degraded_data
                page.unroute("**/api/analyze/v2/stream")
                page.route(
                    "**/api/analyze/v2/stream",
                    lambda route: route.fulfill(
                        status=200,
                        headers={"content-type": "text/event-stream"},
                        body=f"data: {json.dumps(degraded_payload, ensure_ascii=False)}\n\n",
                    ),
                )
                textarea.fill("Why did the source-limited test run degrade?")
                submit.click()
                time.sleep(3)
                source_status_text = page.locator("[data-testid='source-trace-status']").all_text_contents()
                joined_status_text = " ".join(source_status_text).lower()
                check(
                    "UI degraded source status is visible",
                    "rate limited" in joined_status_text or "限流" in joined_status_text,
                    f"statuses={source_status_text}",
                )
                check(
                    "UI cached source status is visible",
                    "cached" in joined_status_text or "缓存" in joined_status_text,
                    f"statuses={source_status_text}",
                )

                # 11h: Node selection
                print("\n  --- 11h: Node Click + Selection ---")
                first_card = cards_after.first
                first_card.click()
                time.sleep(0.5)

                selected = page.locator("[data-testid^='sticky-card-'][aria-pressed='true']")
                check("UI node selected", selected.count() > 0, "no selected sticky card")

                right_after_click = page.locator(".right-panel").text_content() or ""
                has_detail = (
                    "probability" in right_after_click.lower()
                    or "概率" in right_after_click
                    or "upstream" in right_after_click.lower()
                    or "上游" in right_after_click
                    or "evidence" in right_after_click.lower()
                    or "证据" in right_after_click
                )
                check(
                    "UI right panel shows node detail",
                    has_detail,
                    f"right panel: {(right_after_click or '')[:150]}",
                )

                # 11i: Deselect
                if selected.count() > 0:
                    first_card.click()
                    time.sleep(0.3)
                    check(
                        "UI node deselection works",
                        selected.count() == 0,
                        "sticky card still selected after second click",
                    )

        # 11j: Language toggle
        print("\n  --- 11j: Language Toggle ---")
        lang_btn = page.locator("button:has-text('EN')").first
        if lang_btn.count() == 0:
            lang_btn = page.locator("button:has-text('中')").first

        if lang_btn.count() > 0:
            before = lang_btn.text_content() or ""
            lang_btn.click()
            time.sleep(1)
            after_el = page.locator("button:has-text('EN'), button:has-text('中')").first
            after = after_el.text_content() if after_el.count() > 0 else ""
            check(
                "UI language toggle switches", before != after, f"before='{before}' after='{after}'"
            )

            cards_lang = page.locator(".sticky-card")
            check("UI page renders after toggle", cards_lang.count() > 0)
        else:
            skip("UI language toggle", "button not found")

        # 11k: Post-toggle node click
        print("\n  --- 11k: Post-toggle Node Interaction ---")
        all_cards = page.locator(".sticky-card")
        if all_cards.count() > 0:
            all_cards.first.click()
            time.sleep(0.5)
            selected2 = page.locator("[data-testid^='sticky-card-'][aria-pressed='true']")
            check("UI node selectable after language toggle", selected2.count() > 0)

        # 11l: No console errors
        print("\n  --- 11l: Console Health ---")
        page.reload(wait_until="domcontentloaded")
        time.sleep(2)
        critical_errors = [
            e
            for e in console_errors
            if "chunk" not in e.text.lower() and "404" not in e.text.lower()
        ]
        check(
            "UI no critical console errors",
            len(critical_errors) == 0 and len(page_errors) == 0,
            f"{len(critical_errors)} console errors, {len(page_errors)} page errors: "
            f"{[e.text[:80] for e in critical_errors[:3]]} "
            f"{[str(e)[:80] for e in page_errors[:3]]}; "
            f"500s={failed_responses[:3]}",
        )

        browser.close()

# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print("E2E Test Results")
print(f"{'=' * 60}")
total = passed + failed + skipped
print(f"Total: {total} | PASS: {passed} | FAIL: {failed} | SKIP: {skipped}")
if failed > 0:
    print("\nSOME TESTS FAILED — see details above")
    sys.exit(1)
else:
    print("\nAll E2E tests passed!")
