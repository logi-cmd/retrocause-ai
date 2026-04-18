import type { RefObject } from "react";

type LocalizedAnalysisBrief = {
  answer: string;
  confidence: number;
  topReasons: string[];
  challengeSummary: string;
  missingEvidence: string[];
  sourceCoverage: string;
};

type SourceTransparencySummary = {
  labels: string[];
  checked: number;
  stable: number;
  successful: number;
  cached: number;
  failed: number;
  hits: number;
  reviewability: string;
};

type ReadableBriefPanelProps = {
  brief: LocalizedAnalysisBrief;
  markdownBrief: string | null;
  markdownCopyStatus: "idle" | "copied" | "failed";
  showManualCopyReport: boolean;
  sourceTransparencySummary: SourceTransparencySummary;
  hasRefutingChallenges: boolean;
  locale: "zh" | "en";
  manualCopyReportRef: RefObject<HTMLTextAreaElement | null>;
  onCopyMarkdown: () => void;
  onSelectManualCopyReport: () => void;
};

export function ReadableBriefPanel({
  brief,
  markdownBrief,
  markdownCopyStatus,
  showManualCopyReport,
  sourceTransparencySummary,
  hasRefutingChallenges,
  locale,
  manualCopyReportRef,
  onCopyMarkdown,
  onSelectManualCopyReport,
}: ReadableBriefPanelProps) {
  return (
    <div
      className="compact-item"
      data-testid="readable-brief"
      style={{ background: "rgba(255,255,255,0.78)" }}
    >
      <div
        style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}
      >
        <div className="compact-label" style={{ marginBottom: 0 }}>
          {locale === "en" ? "Readable brief" : "\u9605\u8bfb\u7248\u7b80\u62a5"}
        </div>
        {markdownBrief && (
          <button
            type="button"
            data-testid="copy-report-button"
            onClick={onCopyMarkdown}
            title={
              locale === "en" ? "Copy the portable Markdown report" : "\u590d\u5236 Markdown \u62a5\u544a"
            }
            style={{
              border: "1px solid rgba(49, 95, 131, 0.22)",
              borderRadius: "8px",
              padding: "4px 7px",
              background:
                markdownCopyStatus === "copied" ? "rgba(118, 166, 119, 0.18)" : "rgba(255,255,255,0.66)",
              color: markdownCopyStatus === "failed" ? "#a0503c" : "#315f83",
              cursor: "pointer",
              fontSize: "0.54rem",
              fontWeight: 800,
              letterSpacing: 0,
              textTransform: "uppercase",
            }}
          >
            {markdownCopyStatus === "copied"
              ? locale === "en"
                ? "Copied"
                : "\u5df2\u590d\u5236"
              : markdownCopyStatus === "failed"
                ? locale === "en"
                  ? "Copy failed"
                  : "\u590d\u5236\u5931\u8d25"
                : locale === "en"
                  ? "Copy report"
                  : "\u590d\u5236\u62a5\u544a"}
          </button>
        )}
      </div>
      <div
        style={{
          marginTop: "7px",
          fontSize: "0.7rem",
          color: "#4d3c28",
          lineHeight: 1.5,
          fontWeight: 700,
        }}
      >
        {brief.answer}
      </div>
      <div style={{ marginTop: "5px", fontSize: "0.58rem", color: "#7a6b55" }}>
        {locale === "en" ? "Confidence signal" : "\u7f6e\u4fe1\u4fe1\u53f7"} {brief.confidence}%
      </div>

      <div style={{ marginTop: "10px" }}>
        <div style={{ fontSize: "0.58rem", color: "#315f83", fontWeight: 800 }}>
          {locale === "en" ? "Top reasons" : "\u5173\u952e\u539f\u56e0"}
        </div>
        {brief.topReasons.slice(0, 3).map((reason, index) => (
          <div
            key={`brief-reason-${index}`}
            style={{
              marginTop: "6px",
              display: "grid",
              gridTemplateColumns: "18px minmax(0, 1fr)",
              gap: "5px",
              fontSize: "0.6rem",
              color: "#5c4a32",
              lineHeight: 1.45,
            }}
          >
            <strong style={{ color: "#315f83" }}>{index + 1}.</strong>
            <span>{reason}</span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "10px" }}>
        <div style={{ fontSize: "0.58rem", color: "#315f83", fontWeight: 800 }}>
          {locale === "en" ? "What to check" : "\u5ba1\u9605\u91cd\u70b9"}
        </div>
        <div
          style={{
            marginTop: "5px",
            fontSize: "0.58rem",
            color: hasRefutingChallenges ? "#a0503c" : "#6b5a42",
            lineHeight: 1.45,
          }}
        >
          {brief.challengeSummary}
        </div>
        {brief.missingEvidence.slice(0, 2).map((item, index) => (
          <div
            key={`brief-gap-${index}`}
            style={{ marginTop: "5px", fontSize: "0.56rem", color: "#8b7355", lineHeight: 1.45 }}
          >
            {locale === "en" ? "Gap: " : "\u7f3a\u53e3\uff1a"}
            {item}
          </div>
        ))}
      </div>

      <div style={{ marginTop: "9px", fontSize: "0.56rem", color: "#7a6b55", lineHeight: 1.45 }}>
        {locale === "en" ? "Evidence coverage: " : "\u8bc1\u636e\u8986\u76d6\uff1a"}
        {brief.sourceCoverage}
      </div>
      {sourceTransparencySummary.checked > 0 && (
        <div
          data-testid="source-health-summary"
          style={{
            marginTop: "9px",
            padding: "7px 8px",
            border: "1px solid rgba(49, 95, 131, 0.14)",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.56)",
            fontSize: "0.55rem",
            color: "#6b5a42",
            lineHeight: 1.45,
          }}
        >
          <div style={{ color: "#315f83", fontWeight: 800 }}>
            {locale === "en" ? "Sources checked" : "\u5df2\u68c0\u7d22\u6765\u6e90"}:{" "}
            {sourceTransparencySummary.labels.join(", ") ||
              (locale === "en" ? "source trace available" : "\u5df2\u8fd4\u56de\u6765\u6e90\u8f68\u8ff9")}
          </div>
          <div style={{ marginTop: "3px" }}>
            {locale === "en" ? "Stable sources" : "\u7a33\u5b9a\u6765\u6e90"}:{" "}
            {sourceTransparencySummary.stable}/{sourceTransparencySummary.checked}
            {" / "}
            {locale === "en" ? "Failed sources" : "\u5931\u8d25\u6765\u6e90"}:{" "}
            {sourceTransparencySummary.failed}
            {" / "}
            {locale === "en" ? "Hits" : "\u547d\u4e2d"}: {sourceTransparencySummary.hits}
          </div>
          <div style={{ marginTop: "3px" }}>
            {locale === "en" ? "Successful sources" : "\u6210\u529f\u6765\u6e90"}:{" "}
            {sourceTransparencySummary.successful}
            {" / "}
            {locale === "en" ? "Cached sources" : "\u7f13\u5b58\u6765\u6e90"}:{" "}
            {sourceTransparencySummary.cached}
            {" / "}
            {locale === "en" ? "Degraded sources" : "\u53d7\u9650\u6765\u6e90"}:{" "}
            {sourceTransparencySummary.failed}
          </div>
          <div style={{ marginTop: "3px", fontWeight: 800 }}>
            {locale === "en" ? "Reviewability" : "\u53ef\u5ba1\u9605\u6027"}:{" "}
            {sourceTransparencySummary.reviewability}
          </div>
        </div>
      )}
      {markdownBrief && showManualCopyReport && (
        <div style={{ marginTop: "10px" }}>
          <div style={{ fontSize: "0.58rem", color: "#a0503c", fontWeight: 800 }}>
            {locale === "en" ? "Manual copy" : "\u624b\u52a8\u590d\u5236"}
          </div>
          <div style={{ marginTop: "4px", fontSize: "0.55rem", color: "#7a6b55", lineHeight: 1.45 }}>
            {locale === "en"
              ? "Clipboard permission was blocked. Select the report text below and copy it manually."
              : "\u6d4f\u89c8\u5668\u62e6\u622a\u4e86\u526a\u8d34\u677f\u6743\u9650\u3002\u9009\u4e2d\u4e0b\u65b9\u62a5\u544a\u6587\u672c\u540e\u624b\u52a8\u590d\u5236\u3002"}
          </div>
          <button
            type="button"
            onClick={onSelectManualCopyReport}
            style={{
              marginTop: "6px",
              border: "1px solid rgba(49, 95, 131, 0.22)",
              borderRadius: "8px",
              padding: "5px 8px",
              background: "rgba(255,255,255,0.66)",
              color: "#315f83",
              cursor: "pointer",
              fontSize: "0.54rem",
              fontWeight: 800,
            }}
          >
            {locale === "en" ? "Select report text" : "\u9009\u4e2d\u62a5\u544a\u6587\u672c"}
          </button>
          <textarea
            ref={manualCopyReportRef}
            data-testid="manual-copy-report"
            readOnly
            value={markdownBrief}
            onFocus={onSelectManualCopyReport}
            style={{
              marginTop: "6px",
              width: "100%",
              minHeight: "132px",
              maxHeight: "220px",
              resize: "vertical",
              border: "1px solid rgba(160, 80, 60, 0.20)",
              borderRadius: "8px",
              padding: "8px",
              background: "rgba(255,255,255,0.72)",
              color: "#4d3c28",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
              fontSize: "0.56rem",
              lineHeight: 1.5,
              whiteSpace: "pre-wrap",
            }}
          />
        </div>
      )}
    </div>
  );
}
