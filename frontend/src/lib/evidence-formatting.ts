import type { AnalysisUiState, ApiEvidence } from "@/lib/api-types";

export function formatRefutationStatusLabel(
  status: string | null | undefined,
  locale: "zh" | "en"
): string {
  switch (status) {
    case "has_refutation":
      return locale === "en" ? "challenge found" : "\u53d1\u73b0\u53cd\u8bc1";
    case "checked_no_refuting_claims":
      return locale === "en"
        ? "checked, no explicit challenge"
        : "\u5df2\u68c0\u67e5\uff0c\u672a\u89c1\u660e\u786e\u53cd\u8bc1";
    case "checked_context_only":
      return locale === "en"
        ? "checked, context only"
        : "\u5df2\u68c0\u67e5\uff0c\u4ec5\u6709\u80cc\u666f\u8bc1\u636e";
    case "checked_no_results":
      return locale === "en"
        ? "checked, no source results"
        : "\u5df2\u68c0\u67e5\uff0c\u4f46\u672a\u53d6\u56de\u6765\u6e90\u7ed3\u679c";
    case "no_refutation_in_retrieved_evidence":
      return locale === "en"
        ? "no challenge in retrieved evidence"
        : "\u5df2\u68c0\u7d22\u8bc1\u636e\u4e2d\u672a\u89c1\u53cd\u8bc1";
    default:
      return locale === "en"
        ? "challenge coverage not checked"
        : "\u53cd\u8bc1\u8986\u76d6\u672a\u68c0\u9a8c";
  }
}

export function formatEvidenceTierLabel(
  item: ApiEvidence,
  locale: "zh" | "en"
): string {
  if (item.source_tier === "fresh") {
    return locale === "en" ? "Fresh source" : "实时来源";
  }
  if (item.extraction_method === "llm_fulltext_trusted") {
    return locale === "en" ? "Trusted full text" : "可信正文";
  }
  if (item.extraction_method === "llm_fulltext") {
    return locale === "en" ? "Full text" : "正文";
  }
  if (item.extraction_method === "store_cache") {
    return locale === "en" ? "Store cache" : "证据缓存";
  }
  if (item.extraction_method === "fallback_summary") {
    return locale === "en" ? "Fallback summary" : "降级摘要";
  }
  if (item.source_tier === "base") {
    return locale === "en" ? "Base source" : "基础来源";
  }
  return locale === "en" ? "Derived evidence" : "衍生证据";
}

export function evidenceQualityCategory(
  item: ApiEvidence
): "trusted_fulltext" | "fulltext" | "store_cache" | "fallback" | "base" | "other" {
  if (item.extraction_method === "llm_fulltext_trusted") return "trusted_fulltext";
  if (item.extraction_method === "llm_fulltext") return "fulltext";
  if (item.extraction_method === "store_cache") return "store_cache";
  if (item.extraction_method === "fallback_summary") return "fallback";
  if (item.source_tier === "base" || item.source_tier === "fresh") return "base";
  return "other";
}

export function evidenceSortWeight(item: ApiEvidence): number {
  switch (evidenceQualityCategory(item)) {
    case "trusted_fulltext":
      return 0;
    case "fulltext":
      return 1;
    case "store_cache":
      return 2;
    case "base":
      return 3;
    case "fallback":
      return 4;
    default:
      return 5;
  }
}

export function evidenceCategorySummaryLabel(
  category: "fallback" | "base",
  count: number,
  locale: "zh" | "en"
): string {
  if (locale === "en") {
    return category === "fallback"
      ? `${count} fallback summary`
      : `${count} base or fresh source`;
  }
  return category === "fallback"
    ? `${count} 条降级摘要`
    : `${count} 条基础或实时来源`;
}

export function formatTimeRangeLabel(
  timeRange: string | null | undefined,
  locale: "zh" | "en"
): string | null {
  if (!timeRange) return null;

  const labels: Record<string, { en: string; zh: string }> = {
    today: { en: "Today", zh: "今天" },
    yesterday: { en: "Yesterday", zh: "昨天" },
    last_24h: { en: "Last 24h", zh: "最近 24 小时" },
    last_7d: { en: "Last 7 days", zh: "最近 7 天" },
    trading_day: { en: "Current trading day", zh: "当前交易日" },
    evergreen: { en: "Evergreen background", zh: "长期背景" },
  };

  const normalized = labels[timeRange];
  if (normalized) {
    return locale === "en" ? normalized.en : normalized.zh;
  }

  return timeRange.replaceAll("_", " ");
}

export function formatFreshnessLabel(
  freshnessStatus: string | null | undefined,
  locale: "zh" | "en"
): string {
  switch (freshnessStatus) {
    case "fresh":
      return locale === "en" ? "Fresh evidence" : "新鲜证据";
    case "mixed":
      return locale === "en" ? "Mixed freshness" : "新鲜度混合";
    case "stable":
      return locale === "en" ? "Mostly stable evidence" : "以稳定证据为主";
    case "stale":
      return locale === "en" ? "Stale evidence" : "证据偏旧";
    default:
      return locale === "en" ? "Freshness unknown" : "新鲜度未知";
  }
}

export function formatAnalysisBadge(mode: AnalysisUiState["mode"], locale: "zh" | "en"): string {
  if (mode === "demo") {
    return locale === "en" ? "Demo" : "Demo";
  }
  if (mode === "partial_live") {
    return locale === "en" ? "Partial Live" : "部分 Live";
  }
  return locale === "en" ? "Live" : "Live";
}
