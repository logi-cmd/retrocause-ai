from __future__ import annotations

from retrocause.models import (
    CausalEdge,
    CausalVariable,
    EvidenceConflictType,
    UncertaintyType,
)
from retrocause.uncertainty import (
    UncertaintyAssessmentStep,
    assess_edge_uncertainty,
    assess_variable_uncertainty,
    build_uncertainty_report,
    detect_evidence_conflict,
)
from retrocause.collector import EvidenceCollector
from retrocause.pipeline import PipelineContext


def test_assess_variable_no_evidence():
    var = CausalVariable(name="test_var", description="a test variable")
    assessment = assess_variable_uncertainty(var, evidence_count=0, total_evidence=10)
    assert UncertaintyType.THIN_EVIDENCE in assessment.uncertainty_types
    assert assessment.overall_score > 0.3


def test_assess_variable_well_supported():
    var = CausalVariable(name="test_var", description="a test variable", posterior_support=0.8)
    assessment = assess_variable_uncertainty(var, evidence_count=5, total_evidence=10)
    assert UncertaintyType.THIN_EVIDENCE not in assessment.uncertainty_types
    assert assessment.overall_score < 0.5


def test_assess_edge_no_evidence():
    edge = CausalEdge(source="a", target="b", conditional_prob=0.5)
    assessment = assess_edge_uncertainty(edge, {})
    assert UncertaintyType.THIN_EVIDENCE in assessment.uncertainty_types


def test_assess_edge_conflicting():
    edge = CausalEdge(
        source="a",
        target="b",
        conditional_prob=0.5,
        supporting_evidence_ids=["ev-1", "ev-2", "ev-3"],
        refuting_evidence_ids=["ev-4", "ev-5"],
    )
    assessment = assess_edge_uncertainty(edge, {})
    assert UncertaintyType.CONFLICTING_EVIDENCE in assessment.uncertainty_types


def test_assess_edge_wide_ci():
    edge = CausalEdge(source="a", target="b", conditional_prob=0.5, confidence_interval=(0.1, 0.9))
    assessment = assess_edge_uncertainty(edge, {})
    assert UncertaintyType.EPISTEMIC in assessment.uncertainty_types


def test_detect_no_conflict():
    edge = CausalEdge(
        source="a",
        target="b",
        conditional_prob=0.5,
        supporting_evidence_ids=["ev-1"],
        refuting_evidence_ids=[],
    )
    assert detect_evidence_conflict(edge) == EvidenceConflictType.NONE


def test_detect_direct_conflict():
    edge = CausalEdge(
        source="a",
        target="b",
        conditional_prob=0.5,
        supporting_evidence_ids=["ev-1"],
        refuting_evidence_ids=["ev-2", "ev-3"],
    )
    assert detect_evidence_conflict(edge) == EvidenceConflictType.DIRECT


def test_detect_partial_conflict():
    edge = CausalEdge(
        source="a",
        target="b",
        conditional_prob=0.5,
        supporting_evidence_ids=["ev-1", "ev-2", "ev-3"],
        refuting_evidence_ids=["ev-4"],
    )
    assert detect_evidence_conflict(edge) == EvidenceConflictType.PARTIAL


def test_build_uncertainty_report():
    var1 = CausalVariable(name="a", description="var a")
    var2 = CausalVariable(name="b", description="var b", evidence_ids=["ev-1"])
    edge1 = CausalEdge(source="a", target="b", conditional_prob=0.6)
    edge2 = CausalEdge(
        source="b",
        target="c",
        conditional_prob=0.7,
        supporting_evidence_ids=["ev-1"],
        refuting_evidence_ids=["ev-2"],
    )

    report = build_uncertainty_report(
        variables=[var1, var2],
        edges=[edge1, edge2],
        chains=[],
        evidence_by_var={"a": [], "b": ["ev-1"]},
        total_evidence=2,
    )

    assert "a" in report.per_node
    assert "b" in report.per_node
    assert "a→b" in report.per_edge
    assert "b→c" in report.per_edge
    assert len(report.evidence_conflicts) >= 1
    assert 0.0 <= report.overall_uncertainty <= 1.0
    assert isinstance(report.summary, str)
    assert var1.uncertainty is not None
    assert edge1.uncertainty is not None


def test_uncertainty_step():
    from retrocause.models import EvidenceType

    collector = EvidenceCollector()
    collector.add_evidence(
        "test evidence about asteroid", EvidenceType.SCIENTIFIC, linked_variables=["asteroid"]
    )
    step = UncertaintyAssessmentStep(collector)
    ctx = PipelineContext(query="test", domain="general")
    ctx.variables = [CausalVariable(name="asteroid", description="asteroid impact")]
    ctx.edges = [CausalEdge(source="asteroid", target="extinction", conditional_prob=0.8)]
    ctx.total_evidence_count = 1
    ctx = step.execute(ctx)
    assert "uncertainty_report" in ctx.extra
    assert ctx.total_uncertainty >= 0
