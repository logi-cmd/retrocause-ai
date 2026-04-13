from __future__ import annotations

from retrocause.api.main import _result_to_v2
from retrocause.models import AnalysisResult


def test_v2_response_exposes_evidence_access_trace():
    result = AnalysisResult(
        query="Why did bitcoin fall today?",
        domain="finance",
        variables=[],
        edges=[],
        hypotheses=[],
    )
    result.retrieval_trace = [
        {
            "source": "ap_news",
            "query": "bitcoin price selloff today",
            "result_count": 2,
            "cache_hit": False,
            "error": None,
        },
        {
            "source": "gdelt",
            "query": "bitcoin price selloff today",
            "result_count": 0,
            "cache_hit": False,
            "error": "TimeoutException",
        },
    ]

    response = _result_to_v2(result, is_demo=False)

    assert [item.source for item in response.retrieval_trace] == ["ap_news", "gdelt"]
    assert response.retrieval_trace[0].result_count == 2
    assert response.retrieval_trace[1].error == "TimeoutException"


def test_v2_response_exposes_human_readable_source_trace_metadata():
    result = AnalysisResult(
        query="Why did US Iran talks in Islamabad end without agreement?",
        domain="geopolitics",
        variables=[],
        edges=[],
        hypotheses=[],
    )
    result.retrieval_trace = [
        {
            "source": "ap_news",
            "query": "US Iran Islamabad talks no agreement",
            "result_count": 1,
            "cache_hit": False,
            "error": None,
        },
        {
            "source": "web",
            "query": "US Iran Islamabad talks no agreement",
            "result_count": 3,
            "cache_hit": True,
            "error": None,
        },
    ]

    response = _result_to_v2(result, is_demo=False)

    assert response.retrieval_trace[0].source_label == "AP News"
    assert response.retrieval_trace[0].source_kind == "wire_news"
    assert response.retrieval_trace[0].stability == "high"
    assert response.retrieval_trace[1].source_label == "Trusted web search"
    assert response.retrieval_trace[1].source_kind == "web_search"
    assert response.retrieval_trace[1].stability == "medium"
