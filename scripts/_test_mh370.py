import sys, logging

sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s: %(message)s")

from retrocause.config import RetroCauseConfig
from retrocause.llm import LLMClient
from retrocause.sources.arxiv import ArxivSourceAdapter
from retrocause.sources.semantic_scholar import SemanticScholarAdapter
from retrocause.sources.web import WebSearchAdapter
from retrocause.engine import analyze

cfg = RetroCauseConfig.from_env()
print(f"config timeout={cfg.request_timeout_seconds}s, debate_rounds={cfg.debate_max_rounds}")

llm = LLMClient(
    api_key="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",
    model="deepseek/deepseek-chat-v3-0324",
    base_url="https://openrouter.ai/api/v1",
    timeout=cfg.request_timeout_seconds,
)


def on_progress(step_name, step_index, total, message):
    print(f"  [{step_index + 1}/{total}] {step_name}: {message}")


import time

t0 = time.time()
result = analyze(
    "MH370为什么失踪",
    llm_client=llm,
    source_adapters=[ArxivSourceAdapter(), SemanticScholarAdapter(), WebSearchAdapter()],
    config=cfg,
    on_progress=on_progress,
)
elapsed = time.time() - t0

print(f"\n=== RESULT ({elapsed:.1f}s) ===")
print(f"is_demo would be: {len(result.hypotheses) == 0}")
print(f"hypotheses: {len(result.hypotheses)}")
print(f"variables: {len(result.variables)}")
print(f"edges: {len(result.edges)}")
print(f"evidence: {result.total_evidence_count}")
print(f"step_errors: {result.recommended_next_steps}")
for i, h in enumerate(result.hypotheses):
    print(f"  h{i}: {h.chain_id} prob={h.probability} nodes={len(h.nodes)} edges={len(h.edges)}")
