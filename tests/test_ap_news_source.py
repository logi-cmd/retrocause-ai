from __future__ import annotations

from retrocause.sources.ap_news import APNewsAdapter, _url_rank


def test_ap_news_url_rank_does_not_hardcode_iran_boost_for_unrelated_queries():
    query_tokens = {"united", "states", "semiconductor", "export", "controls"}

    semiconductor_score, _ = _url_rank(
        "https://apnews.com/article/semiconductor-export-controls", query_tokens
    )
    iran_score, _ = _url_rank(
        "https://apnews.com/article/turkey-foreign-minister-iran", query_tokens
    )

    assert semiconductor_score > iran_score


def test_ap_news_extracts_published_date_from_article_metadata(monkeypatch):
    search_html = 'https://apnews.com/article/bitcoin-selloff-april-12-2026'
    article_body = " ".join(
        [
            "Bitcoin fell during the April 12, 2026 session after liquidations.",
            "ETF outflows and macro risk also weighed on crypto prices.",
            "Liquidations amplified the move across derivatives venues.",
        ]
        * 8
    )
    article_html = f"""
    <html>
      <head>
        <meta property="og:title" content="Bitcoin selloff April 12, 2026">
        <meta property="article:published_time" content="2026-04-12T08:30:00Z">
      </head>
      <body><article><p>{article_body}</p></article></body>
    </html>
    """

    class _Response:
        def __init__(self, text: str):
            self.text = text

        def raise_for_status(self) -> None:
            return None

    def fake_get(url, **kwargs):
        if "search" in url:
            return _Response(search_html)
        return _Response(article_html)

    monkeypatch.setattr("retrocause.sources.ap_news.httpx.get", fake_get)

    results = APNewsAdapter().search("Bitcoin selloff April 12 2026", max_results=1)

    assert len(results) == 1
    assert results[0].metadata["published"] == "2026-04-12"
