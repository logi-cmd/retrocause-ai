import os
import sys, logging, time, traceback

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s", stream=sys.stdout
)

from retrocause.config import RetroCauseConfig
from retrocause.llm import LLMClient
from retrocause.sources.arxiv import ArxivSourceAdapter
from retrocause.sources.semantic_scholar import SemanticScholarAdapter
from retrocause.sources.web import WebSearchAdapter
from retrocause.app.demo_data import run_real_analysis_with_progress

cfg = RetroCauseConfig.from_env()
print(f"config: timeout={cfg.request_timeout_seconds}s, max_sub_queries={cfg.max_sub_queries}")

API_KEY = (
    os.environ.get("OPENROUTER_API_KEY")
    or os.environ.get("RETROCAUSE_OPENROUTER_KEY")
    or ""
).strip()
if not API_KEY:
    raise SystemExit("Set OPENROUTER_API_KEY or RETROCAUSE_OPENROUTER_KEY before running.")

llm = LLMClient(
    api_key=API_KEY,
    model="deepseek/deepseek-chat-v3-0324",
    base_url="https://openrouter.ai/api/v1",
    timeout=cfg.request_timeout_seconds,
)

progress_events = []


def on_progress(step_name, step_index, total, message):
    evt = f"[{step_index + 1}/{total}] {step_name}: {message}"
    progress_events.append(evt)
    print(f"  PROGRESS: {evt}")


t0 = time.time()
try:
    result = run_real_analysis_with_progress(
        "MH370为什么失踪",
        API_KEY,
        "deepseek/deepseek-chat-v3-0324",
        "https://openrouter.ai/api/v1",
        on_progress,
    )
    elapsed = time.time() - t0
    print(f"\n=== RESULT ({elapsed:.1f}s) ===")
    print(f"result type: {type(result)}")
    print(f"result is None: {result is None}")
    if result:
        print(f"hypotheses: {len(result.hypotheses)}")
        print(f"variables: {len(result.variables)}")
        print(f"edges: {len(result.edges)}")
        print(f"evidence: {result.total_evidence_count}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"\n=== EXCEPTION ({elapsed:.1f}s) ===")
    traceback.print_exc()
