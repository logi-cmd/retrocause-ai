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
  const localizedTitle =
    brief.title && brief.title !== brief.scenario_key ? renderText(brief.title) : null;

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
      {localizedTitle && (
        <div style={{ marginTop: "6px", fontSize: "0.55rem", color: "#8b7355", fontWeight: 700 }}>
          {localizedTitle}
        </div>
      )}
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
      {brief.sections.map((section) => (
        <div key={section.kind} style={{ marginTop: "10px" }}>
          <div style={{ fontSize: "0.58rem", color: "#315f83", fontWeight: 800 }}>
            {renderText(section.title)}
          </div>
          {section.items.slice(0, 4).map((item) => (
            <div
              key={`${section.kind}-${item.title}`}
              style={{
                marginTop: "6px",
                fontSize: "0.58rem",
                color: "#5c4a32",
                lineHeight: 1.45,
              }}
            >
              <div style={{ fontWeight: 700 }}>
                {renderText(item.title)}
              </div>
              <div style={{ marginTop: "2px" }}>{renderText(item.summary)}</div>
              {item.evidence_ids.length > 0 && (
                <div style={{ color: "#8b7355", marginTop: "2px" }}>
                  {" "}
                  {locale === "en" ? "Evidence" : "\u8bc1\u636e"}:{" "}
                  {item.evidence_ids.join(", ")}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
      {brief.next_verification_steps.length > 0 && (
        <div
          style={{
            marginTop: "9px",
            paddingTop: "8px",
            borderTop: "1px solid rgba(49, 95, 131, 0.12)",
          }}
        >
          <div style={{ fontSize: "0.58rem", color: "#315f83", fontWeight: 800 }}>
            {locale === "en" ? "Next verification steps" : "\u4e0b\u4e00\u6b65\u6838\u9a8c"}
          </div>
          {brief.next_verification_steps.slice(0, 4).map((step, index) => (
            <div
              key={`verification-step-${index}`}
              style={{ marginTop: "5px", fontSize: "0.56rem", color: "#5c4a32", lineHeight: 1.45 }}
            >
              {index + 1}. {renderText(step)}
            </div>
          ))}
        </div>
      )}
      {brief.limits.length > 0 && (
        <div
          style={{
            marginTop: "9px",
            paddingTop: "8px",
            borderTop: "1px solid rgba(160, 80, 60, 0.12)",
          }}
        >
          <div style={{ fontSize: "0.58rem", color: "#a0503c", fontWeight: 800 }}>
            {locale === "en" ? "Current limits" : "\u5f53\u524d\u9650\u5236"}
          </div>
          {brief.limits.slice(0, 3).map((limit, index) => (
            <div
              key={`production-limit-${index}`}
              style={{ marginTop: "5px", fontSize: "0.56rem", color: "#8b7355", lineHeight: 1.45 }}
            >
              {locale === "en" ? "Limit" : "\u9650\u5236"} {index + 1}: {renderText(limit)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
