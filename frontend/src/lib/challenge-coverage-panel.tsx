import type { ApiChallengeCheck, ApiEdge } from "@/lib/api-types";
import { formatRefutationStatusLabel } from "@/lib/evidence-formatting";

type ChallengeCheckSummary = {
  checked: number;
  refuting: number;
  contextOnly: number;
};

type ChallengeCoveragePanelProps = {
  challengeChecks: ApiChallengeCheck[];
  challengeCheckSummary: ChallengeCheckSummary;
  activeEdges: ApiEdge[];
  locale: "zh" | "en";
  localizeText: (text: string, locale: "zh" | "en") => string;
  onFocusEdge: (edge: ApiEdge) => void;
};

export function ChallengeCoveragePanel({
  challengeChecks,
  challengeCheckSummary,
  activeEdges,
  locale,
  localizeText,
  onFocusEdge,
}: ChallengeCoveragePanelProps) {
  if (challengeChecks.length === 0) return null;

  return (
    <div className="compact-item" style={{ background: "rgba(255,255,255,0.72)" }}>
      <div className="compact-label">
        {locale === "en" ? "Challenge coverage" : "\u53cd\u8bc1\u8986\u76d6"}
      </div>
      <div
        style={{
          fontSize: "0.6rem",
          color: "#6b5a42",
          lineHeight: 1.45,
          marginBottom: "8px",
        }}
      >
        {locale === "en"
          ? `${challengeCheckSummary.checked} edge(s) checked · ${challengeCheckSummary.refuting} challenge item(s)`
          : `\u5df2\u68c0\u67e5 ${challengeCheckSummary.checked} \u6761\u8fb9 · ${challengeCheckSummary.refuting} \u6761\u53cd\u8bc1`}
      </div>
      {challengeChecks.slice(0, 3).map((check) => (
        <button
          type="button"
          key={`${check.edge_id}-challenge`}
          onClick={() => {
            const edge = activeEdges.find(
              (item) => item.source === check.source && item.target === check.target
            );
            if (edge) onFocusEdge(edge);
          }}
          style={{
            width: "100%",
            marginBottom: "8px",
            padding: "7px 8px",
            borderRadius: "6px",
            border: "1px solid rgba(160,140,110,0.14)",
            background:
              check.refuting_count > 0 ? "rgba(160,80,60,0.08)" : "rgba(255,255,255,0.50)",
            color: "#5c4a32",
            cursor: "pointer",
            textAlign: "left",
          }}
        >
          <div style={{ fontSize: "0.58rem", lineHeight: 1.4 }}>
            <strong>{localizeText(check.source, locale)}</strong>
            {" -> "}
            <strong>{localizeText(check.target, locale)}</strong>
          </div>
          <div
            style={{
              marginTop: "3px",
              fontSize: "0.52rem",
              color: check.refuting_count > 0 ? "#a0503c" : "#8b7355",
              lineHeight: 1.35,
            }}
          >
            {formatRefutationStatusLabel(check.status, locale)}
            {` · ${check.result_count} ${locale === "en" ? "result(s)" : "\u6761\u7ed3\u679c"}`}
          </div>
        </button>
      ))}
    </div>
  );
}
