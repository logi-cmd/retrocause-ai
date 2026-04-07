"""CLI 入口"""

from __future__ import annotations

import sys

from retrocause.app.demo_data import topic_aware_demo_result
from retrocause.config import RetroCauseConfig
from retrocause.engine import analyze
from retrocause.formatter import ReportFormatter
from retrocause.llm import LLMClient
from retrocause.sources.arxiv import ArxivSourceAdapter
from retrocause.sources.semantic_scholar import SemanticScholarAdapter
from retrocause.sources.web import WebSearchAdapter


def _format_demo_notice(query: str) -> str:
    result = topic_aware_demo_result(query)
    formatted = ReportFormatter().format(result)
    return (
        "[demo fallback] No OPENAI_API_KEY or OPENROUTER_API_KEY was found. "
        "Showing topic-matched demo output instead of real analysis.\n\n"
        f"{formatted}"
    )


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "恐龙为什么灭绝？"
    config = RetroCauseConfig.from_env()

    if not config.llm_api_key:
        print(_format_demo_notice(query))
        return

    llm = LLMClient(api_key=config.llm_api_key, model=config.llm_model)
    sources = [ArxivSourceAdapter(), SemanticScholarAdapter(), WebSearchAdapter()]
    result = analyze(query, llm_client=llm, source_adapters=sources, config=config)

    if not result.variables and not result.edges and not result.hypotheses:
        print(_format_demo_notice(query))
        return

    print(ReportFormatter().format(result))


if __name__ == "__main__":
    main()
