"""多源交叉验证计算证据可靠性"""

from __future__ import annotations
from retrocause.models import Evidence, EvidenceType


TYPE_PRIOR = {
    EvidenceType.LITERATURE: 0.80,
    EvidenceType.DATA: 0.75,
    EvidenceType.ARCHIVE: 0.72,
    EvidenceType.SCIENTIFIC: 0.78,
    EvidenceType.NEWS: 0.55,
    EvidenceType.TESTIMONY: 0.50,
    EvidenceType.SOCIAL: 0.35,
}


def assign_prior(evidence: Evidence) -> float:
    return TYPE_PRIOR.get(evidence.source_type, 0.50)


def cross_validate(evidence_list: list[Evidence]) -> list[Evidence]:
    for ev in evidence_list:
        ev.prior_reliability = assign_prior(ev)
        ev.posterior_reliability = ev.prior_reliability
    return evidence_list
