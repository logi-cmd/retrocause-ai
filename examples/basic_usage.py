"""完整示例 — 构建因果图 + 生成假说链 + 辩论"""

from retrocause.models import (
    Evidence,
    EvidenceType,
    CausalVariable,
    CausalEdge,
)
from retrocause.collector import EvidenceCollector
from retrocause.reliability import cross_validate
from retrocause.graph import CausalGraphBuilder
from retrocause.hypothesis import HypothesisGenerator
from retrocause.debate import DebateOrchestrator
from retrocause.formatter import ReportFormatter
from retrocause.models import AnalysisResult


def main():
    collector = EvidenceCollector()
    ev1 = collector.add_evidence(
        "化石记录显示K-Pg界线铱异常浓度异常高",
        EvidenceType.SCIENTIFIC,
        linked_variables=["asteroid_impact", "ir_anomaly"],
    )
    ev2 = collector.add_evidence(
        "印度德干暗色岩火山活动在6600万年前显著增强",
        EvidenceType.LITERATURE,
        linked_variables=["deccan_volcanism", "co2_release"],
    )
    ev3 = collector.add_evidence(
        "花粉化石显示白垩纪末期植被急剧变化",
        EvidenceType.SCIENTIFIC,
        linked_variables=["ecosystem_collapse"],
    )
    ev4 = collector.add_evidence(
        "海洋沉积物碳同位素数据显示海洋酸化事件",
        EvidenceType.DATA,
        linked_variables=["ocean_acidification", "co2_release"],
    )

    cross_validate(collector.get_evidence())

    graph = CausalGraphBuilder()
    variables = [
        CausalVariable(name="asteroid_impact", description="小行星撞击", evidence_ids=[ev1.id]),
        CausalVariable(name="ir_anomaly", description="铱异常", evidence_ids=[ev1.id]),
        CausalVariable(name="deccan_volcanism", description="德干火山活动", evidence_ids=[ev2.id]),
        CausalVariable(name="co2_release", description="CO2释放", evidence_ids=[ev2.id, ev4.id]),
        CausalVariable(name="ocean_acidification", description="海洋酸化", evidence_ids=[ev4.id]),
        CausalVariable(
            name="ecosystem_collapse", description="生态系统崩溃", evidence_ids=[ev3.id]
        ),
        CausalVariable(name="result", description="恐龙灭绝", evidence_ids=[]),
    ]
    for v in variables:
        graph.add_variable(v)

    edges = [
        CausalEdge(source="asteroid_impact", target="ir_anomaly", conditional_prob=0.9),
        CausalEdge(source="ir_anomaly", target="ecosystem_collapse", conditional_prob=0.7),
        CausalEdge(source="ecosystem_collapse", target="result", conditional_prob=0.85),
        CausalEdge(source="deccan_volcanism", target="co2_release", conditional_prob=0.8),
        CausalEdge(source="co2_release", target="ocean_acidification", conditional_prob=0.6),
        CausalEdge(source="co2_release", target="ecosystem_collapse", conditional_prob=0.5),
        CausalEdge(source="ocean_acidification", target="result", conditional_prob=0.4),
    ]
    for e in edges:
        graph.add_edge(e)

    print(f"DAG 有效: {graph.validate_dag()}")

    gen = HypothesisGenerator()
    chains = gen.generate_from_graph(graph, "result", variables, edges)
    print(f"生成假说链: {len(chains)} 条")

    debate = DebateOrchestrator(max_rounds=2)
    chains = debate.run_debate(chains)

    result = AnalysisResult(
        query="恐龙为什么灭绝？",
        domain="paleontology",
        variables=variables,
        edges=edges,
        hypotheses=chains,
        total_evidence_count=len(collector.get_evidence()),
    )

    print(ReportFormatter().format(result))


if __name__ == "__main__":
    main()
