from __future__ import annotations

from retrocause.sources.ap_news import _url_rank


def test_ap_news_url_rank_does_not_hardcode_iran_boost_for_unrelated_queries():
    query_tokens = {"united", "states", "semiconductor", "export", "controls"}

    semiconductor_score, _ = _url_rank(
        "https://apnews.com/article/semiconductor-export-controls", query_tokens
    )
    iran_score, _ = _url_rank(
        "https://apnews.com/article/turkey-foreign-minister-iran", query_tokens
    )

    assert semiconductor_score > iran_score
