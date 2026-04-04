"""输出格式化"""

from __future__ import annotations
from retrocause.models import AnalysisResult


class ReportFormatter:
    def format(self, result: AnalysisResult) -> str:
        lines = []
        lines.append(f"Query: {result.query}")
        lines.append(f"Domain: {result.domain}")
        lines.append(f"Evidence collected: {result.total_evidence_count}")
        lines.append(f"Variables: {len(result.variables)}")
        lines.append(f"Hypothesis chains: {len(result.hypotheses)}")
        lines.append("")
        for h in result.hypotheses:
            ci = h.confidence_interval
            lines.append(
                f"  [{h.status.value}] {h.name}  "
                f"P={h.posterior_probability:.3f}  "
                f"CI=[{ci[0]:.3f}, {ci[1]:.3f}]"
            )
            lines.append(f"    {h.description}")
            lines.append("")
        return "\n".join(lines)
