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
  retrievalTrace: ApiRetrievalTrace[];
};

export function SourceTracePanel({ locale, retrievalTrace }: SourceTracePanelProps) {
  if (retrievalTrace.length === 0) return null;

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
