import type { ApiProductionBrief, ApiProductionHarness } from "@/lib/api-types";

type ProductionBriefPanelProps = {
  brief: ApiProductionBrief;
  harness: ApiProductionHarness | null;
  locale: "zh" | "en";
  localizeText: (text: string, locale: "zh" | "en") => string;
};

export function ProductionBriefPanel({
  brief,
  harness,
  locale,
  localizeText,
}: ProductionBriefPanelProps) {
  const renderText = (text: string) => (locale === "en" ? text : localizeText(text, locale));

  return (
    <div
      className="compact-item"
      data-testid="production-brief"
      style={{ background: "rgba(255,255,255,0.80)" }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "8px",
        }}
      >
        <div className="compact-label" style={{ marginBottom: 0 }}>
          {locale === "en" ? "Production brief" : "\u751f\u4ea7\u7ea7\u7b80\u62a5"}
        </div>
        {harness && (
          <span
            style={{
              fontSize: "0.54rem",
              color: harness.status === "ready_for_brief" ? "#526f44" : "#a0503c",
              fontWeight: 800,
              textTransform: "uppercase",
              letterSpacing: "0.04em",
            }}
          >
            {harness.status.replaceAll("_", " ")}
          </span>
        )}
      </div>
      <div
        style={{
          marginTop: "7px",
          fontSize: "0.66rem",
          color: "#4d3c28",
          lineHeight: 1.5,
          fontWeight: 700,
        }}
      >
        {renderText(brief.executive_summary)}
      </div>
      {brief.sections.slice(0, 3).map((section) => (
        <div key={section.kind} style={{ marginTop: "10px" }}>
          <div style={{ fontSize: "0.58rem", color: "#315f83", fontWeight: 800 }}>
            {renderText(section.title)}
          </div>
          {section.items.slice(0, 3).map((item) => (
            <div
              key={`${section.kind}-${item.title}`}
              style={{
                marginTop: "6px",
                fontSize: "0.58rem",
                color: "#5c4a32",
                lineHeight: 1.45,
              }}
            >
              {renderText(item.summary)}
              {item.evidence_ids.length > 0 && (
                <span style={{ color: "#8b7355" }}>
                  {" "}
                  {locale === "en" ? "Evidence" : "\u8bc1\u636e"}:{" "}
                  {item.evidence_ids.join(", ")}
                </span>
              )}
            </div>
          ))}
        </div>
      ))}
      {brief.limits.length > 0 && (
        <div
          style={{
            marginTop: "9px",
            fontSize: "0.56rem",
            color: "#8b7355",
            lineHeight: 1.45,
          }}
        >
          {locale === "en" ? "Limit: " : "\u9650\u5236\uff1a"}
          {renderText(brief.limits[0])}
        </div>
      )}
    </div>
  );
}
