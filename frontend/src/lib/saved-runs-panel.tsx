import type { ApiSavedRunSummary } from "@/lib/api-types";

type SavedRunsPanelProps = {
  runs: ApiSavedRunSummary[];
  status: string;
  locale: "zh" | "en";
  onRefresh: () => void;
  onOpenRun: (runId: string) => void;
};

export function SavedRunsPanel({
  runs,
  status,
  locale,
  onRefresh,
  onOpenRun,
}: SavedRunsPanelProps) {
  return (
    <div className="compact-item" data-testid="saved-runs-panel">
      <div className="compact-label">
        {locale === "en" ? "Saved runs" : "\u5386\u53f2\u8fd0\u884c"}
      </div>
      <button
        type="button"
        onClick={onRefresh}
        style={{
          width: "100%",
          padding: "7px 9px",
          borderRadius: "8px",
          border: "1px solid rgba(49, 95, 131, 0.22)",
          background: "rgba(255,255,255,0.66)",
          color: "#315f83",
          cursor: "pointer",
          fontSize: "0.56rem",
          fontWeight: 800,
        }}
      >
        {locale === "en" ? "Refresh saved runs" : "\u5237\u65b0\u5386\u53f2\u8fd0\u884c"}
      </button>
      {runs.slice(0, 3).map((run) => (
        <button
          type="button"
          key={run.run_id}
          onClick={() => onOpenRun(run.run_id)}
          style={{
            width: "100%",
            marginTop: "7px",
            padding: "7px 8px",
            borderRadius: "8px",
            border: "1px solid rgba(160,140,110,0.14)",
            background: "rgba(255,255,255,0.48)",
            color: "#5c4a32",
            cursor: "pointer",
            textAlign: "left",
            fontSize: "0.56rem",
            lineHeight: 1.35,
          }}
        >
          <strong>{run.run_status}</strong> / {run.analysis_mode}
          <br />
          {run.query}
        </button>
      ))}
      {status && (
        <div
          style={{
            marginTop: "6px",
            fontSize: "0.54rem",
            color: "#7a6b55",
            lineHeight: 1.4,
          }}
        >
          {status}
        </div>
      )}
    </div>
  );
}
