from retrocause.app.demo_data import topic_aware_demo_result


def test_topic_aware_demo_result_for_svb_query():
    result = topic_aware_demo_result("Why did SVB collapse?")

    assert result.query == "Why did SVB collapse?"
    assert result.domain == "finance"
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].id == "demo_svb_primary"
    assert "SVB" in result.hypotheses[0].name
    assert any(var.name == "svb_collapse" for var in result.variables)


def test_topic_aware_demo_result_for_stock_query():
    result = topic_aware_demo_result("为什么某股票暴跌？")

    assert result.query == "为什么某股票暴跌？"
    assert result.domain == "finance"
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].id == "demo_stock_primary"
    assert any(var.name == "stock_selloff" for var in result.variables)


def test_topic_aware_demo_result_falls_back_to_default_demo():
    result = topic_aware_demo_result("Why did dinosaurs go extinct?")

    assert result.query == "Why did dinosaurs go extinct?"
    assert result.domain == "paleontology"
    assert len(result.hypotheses) >= 1
    assert result.hypotheses[0].id == "h1"
