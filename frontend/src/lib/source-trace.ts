import type { ApiRetrievalTrace } from "@/lib/api-types";

export function formatSourceKindLabel(kind: string | null | undefined, locale: "zh" | "en"): string {
  const labels: Record<string, { en: string; zh: string }> = {
    wire_news: { en: "wire news", zh: "\u901a\u8baf\u793e\u65b0\u95fb" },
    news_index: { en: "news index", zh: "\u65b0\u95fb\u7d22\u5f15" },
    web_search: { en: "web search", zh: "\u7f51\u9875\u68c0\u7d22" },
    official_record: { en: "official record", zh: "\u5b98\u65b9\u8bb0\u5f55" },
    academic_index: { en: "academic index", zh: "\u5b66\u672f\u7d22\u5f15" },
    unknown: { en: "unknown source", zh: "\u672a\u77e5\u6765\u6e90" },
  };
  const label = labels[kind ?? "unknown"] ?? labels.unknown;
  return locale === "en" ? label.en : label.zh;
}

export function formatSourceStabilityLabel(
  stability: string | null | undefined,
  locale: "zh" | "en"
): string {
  switch (stability) {
    case "high":
      return locale === "en" ? "stable" : "\u7a33\u5b9a";
    case "medium":
      return locale === "en" ? "best-effort" : "\u5c3d\u529b\u7a33\u5b9a";
    case "low":
      return locale === "en" ? "fragile" : "\u4e0d\u7a33\u5b9a";
    default:
      return locale === "en" ? "unknown" : "\u672a\u77e5";
  }
}

export function sourceTraceStatus(item: ApiRetrievalTrace): string {
  if (item.status) return item.status;
  if (item.cache_hit) return "cached";
  if (item.error) return item.error;
  return "ok";
}

export function formatSourceStatusLabel(
  status: string | null | undefined,
  locale: "zh" | "en"
): string {
  switch (status) {
    case "ok":
      return locale === "en" ? "Ready" : "\u53ef\u7528";
    case "recovered":
      return locale === "en" ? "Recovered" : "\u5df2\u6062\u590d";
    case "empty":
      return locale === "en" ? "No hits" : "\u65e0\u547d\u4e2d";
    case "stale_filtered":
      return locale === "en" ? "Stale filtered" : "\u5df2\u8fc7\u671f";
    case "cached":
      return locale === "en" ? "Cached" : "\u7f13\u5b58";
    case "source_limited":
      return locale === "en" ? "Source limited" : "\u6765\u6e90\u53d7\u9650";
    case "rate_limited":
      return locale === "en" ? "Rate limited" : "\u9650\u6d41";
    case "forbidden":
      return locale === "en" ? "Forbidden" : "\u65e0\u6743\u9650";
    case "timeout":
      return locale === "en" ? "Timed out" : "\u8d85\u65f6";
    case "source_error":
      return locale === "en" ? "Source error" : "\u6765\u6e90\u9519\u8bef";
    default:
      return locale === "en" ? "Source error" : "\u6765\u6e90\u9519\u8bef";
  }
}

export function isDegradedSourceTrace(item: ApiRetrievalTrace): boolean {
  return [
    "source_limited",
    "rate_limited",
    "forbidden",
    "timeout",
    "source_error",
    "stale_filtered",
  ].includes(sourceTraceStatus(item));
}
