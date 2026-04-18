import type { Dispatch, SetStateAction } from "react";
import type { ApiEvidence } from "@/lib/api-types";
import {
  evidenceCategorySummaryLabel,
  formatEvidenceTierLabel,
  formatFreshnessLabel,
} from "@/lib/evidence-formatting";

export type EvidenceStanceFilter = "all" | "supporting" | "refuting";
export type EvidenceConfidenceFilter = "all" | "strong" | "medium" | "weak";
export type EvidenceQualityFilter =
  | "all"
  | "trusted_fulltext"
  | "fulltext"
  | "store_cache"
  | "fallback"
  | "base";

type HiddenEvidenceBreakdown = {
  fallback: number;
  base: number;
};

type CitationByEvidenceId = Map<string, { quoted_text: string }>;

type EvidenceFilterPanelProps = {
  title: string;
  emptyLabel: string;
  sourceFilterOptions: string[];
  evidenceSourceFilter: string;
  setEvidenceSourceFilter: Dispatch<SetStateAction<string>>;
  evidenceStanceFilter: EvidenceStanceFilter;
  setEvidenceStanceFilter: Dispatch<SetStateAction<EvidenceStanceFilter>>;
  evidenceConfidenceFilter: EvidenceConfidenceFilter;
  setEvidenceConfidenceFilter: Dispatch<SetStateAction<EvidenceConfidenceFilter>>;
  evidenceQualityFilter: EvidenceQualityFilter;
  setEvidenceQualityFilter: Dispatch<SetStateAction<EvidenceQualityFilter>>;
  showAllEvidence: boolean;
  setShowAllEvidence: Dispatch<SetStateAction<boolean>>;
  hiddenEvidenceCount: number;
  hiddenEvidenceBreakdown: HiddenEvidenceBreakdown;
  prioritizedEvidence: ApiEvidence[];
  selectedEvidenceId: string | null;
  selectedNodeCitationByEvidenceId: CitationByEvidenceId;
  locale: "zh" | "en";
  getReliabilityLabel: (reliability: string) => string;
  localizeEvidenceContent: (content: string, locale: "zh" | "en") => string;
  onFocusEvidence: (item: ApiEvidence) => void;
};

function formatEvidenceStanceLabel(item: ApiEvidence, locale: "zh" | "en"): string {
  if (item.stance === "context") {
    return locale === "en" ? "Context" : "\u80cc\u666f";
  }
  if (item.stance === "refuting" || !item.is_supporting) {
    return locale === "en" ? "Challenges" : "\u53cd\u8bc1";
  }
  return locale === "en" ? "Supports" : "\u652f\u6301";
}

export function EvidenceFilterPanel({
  title,
  emptyLabel,
  sourceFilterOptions,
  evidenceSourceFilter,
  setEvidenceSourceFilter,
  evidenceStanceFilter,
  setEvidenceStanceFilter,
  evidenceConfidenceFilter,
  setEvidenceConfidenceFilter,
  evidenceQualityFilter,
  setEvidenceQualityFilter,
  showAllEvidence,
  setShowAllEvidence,
  hiddenEvidenceCount,
  hiddenEvidenceBreakdown,
  prioritizedEvidence,
  selectedEvidenceId,
  selectedNodeCitationByEvidenceId,
  locale,
  getReliabilityLabel,
  localizeEvidenceContent,
  onFocusEvidence,
}: EvidenceFilterPanelProps) {
  return (
    <div className="compact-item" style={{ background: "rgba(255,255,255,0.72)" }}>
      <div className="compact-label">{title}</div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "6px",
          marginBottom: "10px",
        }}
      >
        <select
          value={evidenceSourceFilter}
          onChange={(event) => setEvidenceSourceFilter(event.target.value)}
          style={{
            fontSize: "0.56rem",
            padding: "4px 6px",
            borderRadius: "4px",
            border: "1px solid rgba(160,140,110,0.18)",
            background: "rgba(255,255,255,0.92)",
            color: "#5c4a32",
          }}
        >
          {sourceFilterOptions.map((source) => (
            <option key={source} value={source}>
              {source === "all" ? (locale === "en" ? "All sources" : "\u5168\u90e8\u6765\u6e90") : source}
            </option>
          ))}
        </select>
        <select
          value={evidenceStanceFilter}
          onChange={(event) => setEvidenceStanceFilter(event.target.value as EvidenceStanceFilter)}
          style={{
            fontSize: "0.56rem",
            padding: "4px 6px",
            borderRadius: "4px",
            border: "1px solid rgba(160,140,110,0.18)",
            background: "rgba(255,255,255,0.92)",
            color: "#5c4a32",
          }}
        >
          <option value="all">{locale === "en" ? "All stance" : "\u5168\u90e8\u7acb\u573a"}</option>
          <option value="supporting">{locale === "en" ? "Supporting" : "\u652f\u6301"}</option>
          <option value="refuting">{locale === "en" ? "Refuting" : "\u53cd\u8bc1"}</option>
        </select>
        <select
          value={evidenceConfidenceFilter}
          onChange={(event) =>
            setEvidenceConfidenceFilter(event.target.value as EvidenceConfidenceFilter)
          }
          style={{
            gridColumn: "1 / -1",
            fontSize: "0.56rem",
            padding: "4px 6px",
            borderRadius: "4px",
            border: "1px solid rgba(160,140,110,0.18)",
            background: "rgba(255,255,255,0.92)",
            color: "#5c4a32",
          }}
        >
          <option value="all">{locale === "en" ? "All confidence" : "\u5168\u90e8\u53ef\u4fe1\u5ea6"}</option>
          <option value="strong">{locale === "en" ? "Strong" : "\u5f3a"}</option>
          <option value="medium">{locale === "en" ? "Medium" : "\u4e2d"}</option>
          <option value="weak">{locale === "en" ? "Weak" : "\u5f31"}</option>
        </select>
        <select
          value={evidenceQualityFilter}
          onChange={(event) => setEvidenceQualityFilter(event.target.value as EvidenceQualityFilter)}
          style={{
            gridColumn: "1 / -1",
            fontSize: "0.56rem",
            padding: "4px 6px",
            borderRadius: "4px",
            border: "1px solid rgba(160,140,110,0.18)",
            background: "rgba(255,255,255,0.92)",
            color: "#5c4a32",
          }}
        >
          <option value="all">{locale === "en" ? "All evidence types" : "\u5168\u90e8\u8bc1\u636e\u7c7b\u578b"}</option>
          <option value="trusted_fulltext">{locale === "en" ? "Trusted full text" : "\u53ef\u4fe1\u6b63\u6587"}</option>
          <option value="fulltext">{locale === "en" ? "Full text" : "\u6b63\u6587"}</option>
          <option value="store_cache">{locale === "en" ? "Store cache" : "\u8bc1\u636e\u7f13\u5b58"}</option>
          <option value="fallback">{locale === "en" ? "Fallback summary" : "\u964d\u7ea7\u6458\u8981"}</option>
          <option value="base">{locale === "en" ? "Base / fresh sources" : "\u57fa\u7840 / \u5b9e\u65f6\u6765\u6e90"}</option>
        </select>
      </div>
      {hiddenEvidenceCount > 0 && evidenceQualityFilter === "all" && (
        <div
          style={{
            marginBottom: "10px",
            padding: "8px",
            background: "rgba(255,248,240,0.72)",
            border: "1px dashed rgba(160,140,110,0.2)",
            borderRadius: "6px",
          }}
        >
          <div
            style={{
              fontSize: "0.58rem",
              color: "#6b5a42",
              lineHeight: 1.45,
              marginBottom: "6px",
            }}
          >
            {locale === "en"
              ? `${hiddenEvidenceCount} lower-priority evidence item(s) are hidden by default so stronger evidence appears first.`
              : `\u9ed8\u8ba4\u5df2\u6536\u8d77 ${hiddenEvidenceCount} \u6761\u4f4e\u4f18\u5148\u7ea7\u8bc1\u636e\uff0c\u8ba9\u66f4\u5f3a\u7684\u8bc1\u636e\u5148\u5c55\u793a\u3002`}
          </div>
          <div
            style={{
              fontSize: "0.54rem",
              color: "#8b7355",
              lineHeight: 1.45,
              marginBottom: "6px",
            }}
          >
            {[
              hiddenEvidenceBreakdown.fallback > 0
                ? evidenceCategorySummaryLabel("fallback", hiddenEvidenceBreakdown.fallback, locale)
                : null,
              hiddenEvidenceBreakdown.base > 0
                ? evidenceCategorySummaryLabel("base", hiddenEvidenceBreakdown.base, locale)
                : null,
            ]
              .filter(Boolean)
              .join(locale === "en" ? " · " : "\uff1b")}
          </div>
          <button
            type="button"
            onClick={() => setShowAllEvidence((current) => !current)}
            style={{
              fontSize: "0.56rem",
              color: "#5c4a32",
              background: "rgba(255,255,255,0.92)",
              border: "1px solid rgba(160,140,110,0.18)",
              borderRadius: "999px",
              padding: "3px 8px",
              cursor: "pointer",
            }}
          >
            {showAllEvidence
              ? locale === "en"
                ? "Show prioritized only"
                : "\u53ea\u770b\u9ad8\u4f18\u5148\u7ea7\u8bc1\u636e"
              : locale === "en"
                ? "Show all evidence"
                : "\u663e\u793a\u5168\u90e8\u8bc1\u636e"}
          </button>
        </div>
      )}
      {prioritizedEvidence.length > 0 ? (
        prioritizedEvidence.map((item) => (
          <button
            type="button"
            key={item.id}
            onClick={() => onFocusEvidence(item)}
            style={{
              width: "100%",
              marginBottom: "8px",
              padding: "6px",
              border:
                selectedEvidenceId === item.id
                  ? "1px solid rgba(59,110,165,0.28)"
                  : "1px solid transparent",
              borderRadius: "6px",
              background:
                selectedEvidenceId === item.id ? "rgba(59,110,165,0.08)" : "transparent",
              cursor: "pointer",
              textAlign: "left",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "6px",
                fontSize: "0.56rem",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              <span
                style={{
                  color:
                    item.stance === "refuting" || !item.is_supporting
                      ? "#a0503c"
                      : item.stance === "context"
                        ? "#8b7355"
                        : "#5a7a52",
                }}
              >
                {formatEvidenceStanceLabel(item, locale)}
              </span>
              <span style={{ color: "#8b7355" }}>{getReliabilityLabel(item.reliability)}</span>
            </div>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "4px",
                marginTop: "4px",
                marginBottom: "4px",
              }}
            >
              <span
                style={{
                  fontSize: "0.5rem",
                  color: "#8b7355",
                  background: "rgba(255,255,255,0.72)",
                  border: "1px solid rgba(160,140,110,0.18)",
                  borderRadius: "999px",
                  padding: "1px 6px",
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                }}
              >
                {formatEvidenceTierLabel(item, locale)}
              </span>
              {item.freshness && item.freshness !== "unknown" && (
                <span
                  style={{
                    fontSize: "0.5rem",
                    color: "#8b7355",
                    background: "rgba(255,255,255,0.72)",
                    border: "1px solid rgba(160,140,110,0.18)",
                    borderRadius: "999px",
                    padding: "1px 6px",
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                  }}
                >
                  {formatFreshnessLabel(item.freshness, locale)}
                </span>
              )}
            </div>
            <div style={{ fontSize: "0.65rem", color: "#5c4a32", lineHeight: 1.45 }}>
              {localizeEvidenceContent(item.content, locale)}
            </div>
            {selectedNodeCitationByEvidenceId.get(item.id)?.quoted_text && (
              <div
                style={{
                  fontSize: "0.58rem",
                  color: "#6b5a42",
                  lineHeight: 1.45,
                  marginTop: "4px",
                  fontStyle: "italic",
                }}
              >
                &quot;{selectedNodeCitationByEvidenceId.get(item.id)?.quoted_text}&quot;
              </div>
            )}
            <div style={{ fontSize: "0.56rem", color: "#8b7355", marginTop: "2px" }}>
              {locale === "en" ? "Source" : "\u6765\u6e90"}: {item.source}
              {item.timestamp ? ` - ${item.timestamp}` : ""}
            </div>
          </button>
        ))
      ) : (
        <div style={{ fontSize: "0.65rem", color: "#8b7355", lineHeight: 1.5 }}>{emptyLabel}</div>
      )}
    </div>
  );
}
