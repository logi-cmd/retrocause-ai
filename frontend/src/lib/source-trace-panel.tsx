import type { ApiRetrievalTrace } from "@/lib/api-types";
import {
  formatSourceKindLabel,
  formatSourceStabilityLabel,
  formatSourceStatusLabel,
  isDegradedSourceTrace,
  sourceTraceStatus,
} from "@/lib/source-trace";

type SourceTracePanelProps = {
  locale: "zh" | "en";
  mode: "live" | "partial_live" | "demo";
  retrievalTrace: ApiRetrievalTrace[];
};

export function SourceTracePanel({ locale, mode, retrievalTrace }: SourceTracePanelProps) {
  if (retrievalTrace.length === 0) {
    const isDemo = mode === "demo";
    return (
      <div
        className="retrieval-progress"
        data-testid="source-trace-empty"
        style={{
          marginTop: "10px",
          padding: "7px 8px",
          borderRadius: "8px",
          background: "rgba(255,255,255,0.56)",
          border: "1px solid rgba(160,140,110,0.16)",
          color: "#7a6548",
          fontSize: "0.56rem",
          lineHeight: 1.45,
        }}
      >
        <div
          style={{
            color: "#4a7a9e",
            fontWeight: 800,
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            marginBottom: "4px",
          }}
        >
          {locale === "en" ? "No live retrieval trace" : "\u65e0\u5b9e\u65f6\u68c0\u7d22\u8f68\u8ff9"}
        </div>
        {isDemo
          ? locale === "en"
            ? "Demo output uses bundled sample evidence. Treat it as UI practice, not a live source audit."
            : "\u6f14\u793a\u8f93\u51fa\u4f7f\u7528\u5185\u7f6e\u6837\u4f8b\u8bc1\u636e\uff0c\u53ea\u9002\u5408\u7ec3\u4e60\u68c0\u67e5\u754c\u9762\uff0c\u4e0d\u662f\u5b9e\u65f6\u6765\u6e90\u5ba1\u8ba1\u3002"
          : locale === "en"
            ? "This run returned no retrieval-attempt rows, so source health cannot be audited from this panel."
            : "\u672c\u6b21\u8fd0\u884c\u672a\u8fd4\u56de\u68c0\u7d22\u5c1d\u8bd5\u884c\uff0c\u56e0\u6b64\u65e0\u6cd5\u5728\u6b64\u9762\u677f\u5ba1\u8ba1\u6765\u6e90\u5065\u5eb7\u3002"}
      </div>
    );
  }

  return (
    <div className="retrieval-progress" style={{ marginTop: "10px" }}>
      <div
        style={{
          fontSize: "0.52rem",
          color: "#4a7a9e",
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          marginBottom: "6px",
        }}
      >
        {locale === "en" ? "Source trace" : "\u68c0\u7d22\u6765\u6e90\u8f68\u8ff9"}
      </div>
      <div style={{ display: "grid", gap: "5px" }}>
        {retrievalTrace.slice(0, 6).map((item, index) => (
          <div
            key={`${item.source}-${item.query}-${index}`}
            style={{
              display: "grid",
              gap: "2px",
              padding: "5px 6px",
              borderRadius: "8px",
              background: isDegradedSourceTrace(item)
                ? "rgba(192,57,43,0.08)"
                : "rgba(255,255,255,0.55)",
              border: isDegradedSourceTrace(item)
                ? "1px solid rgba(192,57,43,0.18)"
                : "1px solid rgba(160,140,110,0.14)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "6px",
                fontSize: "0.55rem",
                color: isDegradedSourceTrace(item) ? "#a13b2f" : "#5c4a32",
              }}
            >
              <span>
                {item.source_label || item.source}
                {item.cache_hit ? (locale === "en" ? " cache" : " \u7f13\u5b58") : ""}
              </span>
              <span data-testid="source-trace-status">
                {formatSourceStatusLabel(sourceTraceStatus(item), locale)}
                {item.retry_after_seconds
                  ? ` / ${locale === "en" ? "retry after" : "\u91cd\u8bd5\u7b49\u5f85"} ${
                      item.retry_after_seconds
                    }s`
                  : ""}
              </span>
            </div>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "4px",
                fontSize: "0.5rem",
                color: "#8b7355",
                textTransform: "uppercase",
                letterSpacing: "0.04em",
              }}
            >
              <span>{formatSourceKindLabel(item.source_kind, locale)}</span>
              <span>·</span>
              <span>{formatSourceStabilityLabel(item.stability, locale)}</span>
            </div>
            <div style={{ fontSize: "0.54rem", color: "#8b7355", lineHeight: 1.35 }}>
              {item.query}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
