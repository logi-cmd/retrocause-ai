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
