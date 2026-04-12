"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { Caveat } from "next/font/google";
import { useI18n, type TranslationKey } from "@/lib/i18n";
import {
  getLocalizedMockData,
  type CausalChain,
  type ChainNode,
  type ChainEdge,
  type CausalNodeType,
  type EdgeStrength,
  type EvidenceReliability,
} from "@/data/mockData";

type ApiNode = {
  id: string;
  label: string;
  description: string;
  probability: number;
  type: string;
  depth: number;
  upstream_ids: string[];
  supporting_evidence_ids: string[];
  refuting_evidence_ids: string[];
  uncertainty?: {
    uncertainty_types: string[];
    overall_score: number;
    data_uncertainty: number;
    model_uncertainty: number;
    explanation: string;
  } | null;
};

type ApiEdge = {
  id: string;
  source: string;
  target: string;
  strength: number;
  type: string;
  supporting_evidence_ids: string[];
  refuting_evidence_ids: string[];
  citation_spans?: Array<{
    evidence_id: string;
    start_char: number;
    end_char: number;
    quoted_text: string;
    relevance_score: number;
  }>;
  evidence_conflict?: string;
};

type ApiEvidence = {
  id: string;
  content: string;
  source: string;
  reliability: string;
  is_supporting: boolean;
  source_tier?: string;
  freshness?: string;
  timestamp?: string | null;
  extraction_method?: string;
};

type ApiChain = {
  chain_id: string;
  label: string;
  description: string;
  probability: number;
  depth: number;
  nodes: ApiNode[];
  edges: ApiEdge[];
  supporting_evidence_ids: string[];
  refuting_evidence_ids: string[];
};

type AnalyzeResponseV2 = {
  query: string;
  is_demo: boolean;
  demo_topic: string | null;
  analysis_mode: "live" | "partial_live" | "demo";
  freshness_status: string;
  time_range?: string | null;
  partial_live_reasons?: string[];
  recommended_chain_id: string | null;
  evidences: ApiEvidence[];
  chains: ApiChain[];
  evaluation?: {
    evidence_sufficiency: number;
    probability_coherence: number;
    chain_diversity: number;
    overall_confidence: number;
    weaknesses: string[];
    recommended_actions: string[];
  } | null;
  uncertainty_report?: {
    per_node: Record<
      string,
      {
        uncertainty_types: string[];
        overall_score: number;
        data_uncertainty: number;
        model_uncertainty: number;
        explanation: string;
      }
    >;
    per_edge: Record<
      string,
      {
        uncertainty_types: string[];
        overall_score: number;
        data_uncertainty: number;
        model_uncertainty: number;
        explanation: string;
      }
    >;
    evidence_conflicts: Record<string, string>;
    overall_uncertainty: number;
    dominant_uncertainty_type: string | null;
    summary: string;
  } | null;
  error?: string | null;
};

type AnalysisUiState = {
  isDemo: boolean;
  demoTopic: string | null;
  loading: boolean;
  mode: "live" | "partial_live" | "demo";
  freshnessStatus: string;
  timeRange: string | null;
  partialLiveReasons: string[];
};

function formatEvidenceTierLabel(
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

function evidenceQualityCategory(
  item: ApiEvidence
): "trusted_fulltext" | "fulltext" | "store_cache" | "fallback" | "base" | "other" {
  if (item.extraction_method === "llm_fulltext_trusted") return "trusted_fulltext";
  if (item.extraction_method === "llm_fulltext") return "fulltext";
  if (item.extraction_method === "store_cache") return "store_cache";
  if (item.extraction_method === "fallback_summary") return "fallback";
  if (item.source_tier === "base" || item.source_tier === "fresh") return "base";
  return "other";
}

function evidenceSortWeight(item: ApiEvidence): number {
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

function evidenceCategorySummaryLabel(
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

function formatTimeRangeLabel(
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

function formatFreshnessLabel(
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

function formatAnalysisBadge(mode: AnalysisUiState["mode"], locale: "zh" | "en"): string {
  if (mode === "demo") {
    return locale === "en" ? "Demo" : "Demo";
  }
  if (mode === "partial_live") {
    return locale === "en" ? "Partial Live" : "部分 Live";
  }
  return locale === "en" ? "Live" : "Live";
}

const progressStageOrder = [
  "EvidenceCollectionStep",
  "GraphBuildingStep",
  "HypothesisGenerationStep",
  "EvidenceAnchoringStep",
  "CausalRAGStep",
  "CounterfactualVerificationStep",
  "UncertaintyAssessmentStep",
  "EvaluationStep",
];

function progressStageLabel(step: string, locale: "zh" | "en"): string {
  const labels: Record<string, { en: string; zh: string }> = {
    EvidenceCollectionStep: { en: "Finding and reading evidence", zh: "检索并读取证据" },
    GraphBuildingStep: { en: "Building the causal map", zh: "构建因果图" },
    HypothesisGenerationStep: { en: "Comparing explanation chains", zh: "生成解释链" },
    EvidenceAnchoringStep: { en: "Linking evidence to edges", zh: "绑定证据链" },
    CausalRAGStep: { en: "Filling weak coverage", zh: "补充薄弱证据" },
    CounterfactualVerificationStep: { en: "Checking what-if signals", zh: "校验反事实信号" },
    DebateRefinementStep: { en: "Refining claims", zh: "精炼结论" },
    UncertaintyAssessmentStep: { en: "Estimating uncertainty", zh: "评估不确定性" },
    EvaluationStep: { en: "Scoring result quality", zh: "评估结果质量" },
  };
  const label = labels[step];
  if (label) return locale === "en" ? label.en : label.zh;
  return step.replace(/([a-z])([A-Z])/g, "$1 $2");
}

function buildAnalysisStatusNote(
  payload: AnalyzeResponseV2,
  locale: "zh" | "en"
): string {
  const timeLabel = formatTimeRangeLabel(payload.time_range, locale);
  const freshnessLabel = formatFreshnessLabel(payload.freshness_status, locale);
  const firstAction = payload.evaluation?.recommended_actions?.[0];

  if (payload.is_demo) {
    if (payload.error) {
      return locale === "en"
        ? `Analysis failed (${payload.error}). Showing demo fallback.`
        : `分析失败（${payload.error}），当前显示 demo 回退结果。`;
    }
    return locale === "en"
      ? "Backend returned demo fallback data. Treat this as a structured example, not validated analysis."
      : "后端返回了 demo fallback 数据。请将其视为结构化示例，而非已验证分析。";
  }

  if (payload.analysis_mode === "partial_live") {
    const detail = firstAction
      ? locale === "en"
        ? ` Next best action: ${firstAction}`
        : ` 建议优先动作：${firstAction}`
      : "";
    const errorDetail = payload.error
      ? locale === "en"
        ? ` Error: ${payload.error}`
        : ` 错误：${payload.error}`
      : "";
    if (timeLabel) {
      return locale === "en"
        ? `Partial live analysis for ${timeLabel}. ${freshnessLabel}.${detail}${errorDetail}`
        : `这是针对${timeLabel}的部分 live 分析。${freshnessLabel}。${detail}${errorDetail}`;
    }
    return locale === "en"
      ? `Partial live analysis returned. ${freshnessLabel}.${detail}${errorDetail}`
      : `当前返回的是部分 live 分析。${freshnessLabel}。${detail}${errorDetail}`;
  }

  if (timeLabel) {
    return locale === "en"
      ? `Live analysis returned for ${timeLabel}. ${freshnessLabel}. Review evidence coverage before trusting it.`
      : `已返回针对${timeLabel}的 live 分析。${freshnessLabel}。请先检查证据覆盖，再决定是否信任结果。`;
  }

  return locale === "en"
    ? `Live analysis returned. ${freshnessLabel}. Review evidence coverage before trusting it.`
    : `已返回 live 分析。${freshnessLabel}。请先检查证据覆盖，再决定是否信任结果。`;
}

const ZH_CAUSAL_LABELS: Array<[RegExp, string]> = [
  [/evidence-wide causal map/gi, "证据全图"],
  [/supported dag context/gi, "证据支撑的 DAG 上下文"],
  [/single root-to-outcome path/gi, "单条根因到结果路径"],
  [/bitcoin|btc/gi, "比特币"],
  [/cryptocurrenc(?:y|ies)|crypto assets?|crypto/gi, "加密货币"],
  [/price drop|price decline|sell-?off|market drop|crash/gi, "价格跳水"],
  [/bitcoin price/gi, "比特币价格"],
  [/spot etfs?|etf flows?|exchange-traded funds?/gi, "现货 ETF 资金流"],
  [/liquidations?|leveraged liquidations?/gi, "杠杆清算"],
  [/leverage|leveraged positions?/gi, "杠杆仓位"],
  [/risk sentiment|risk appetite|market sentiment/gi, "风险情绪"],
  [/political uncertainty/gi, "政治不确定性"],
  [/sentiment/gi, "情绪"],
  [/overall/gi, "整体"],
  [/among/gi, "中的"],
  [/speculative assets?/gi, "投机资产"],
  [/investors? pulling out of/gi, "投资者撤出"],
  [/investors?/gi, "投资者"],
  [/pulling out of/gi, "撤出"],
  [/digital currencies/gi, "数字货币"],
  [/gold/gi, "黄金"],
  [/silver/gi, "白银"],
  [/macro(?:economic)? pressure|macro factors?|interest rates?|rate expectations/gi, "宏观压力"],
  [/dollar strength|u\.s\. dollar/gi, "美元走强"],
  [/profit taking/gi, "获利了结"],
  [/regulatory concerns?|regulatory pressure/gi, "监管压力"],
  [/heightened concerns about potential/gi, "市场对潜在"],
  [/concerns about potential/gi, "对潜在"],
  [/potential/gi, "潜在"],
  [/concerns?/gi, "担忧"],
  [/washington/gi, "华盛顿"],
  [/stablecoin regulation stalled/gi, "稳定币监管停滞"],
  [/stablecoins?/gi, "稳定币"],
  [/regulation/gi, "监管"],
  [/regulating/gi, "监管"],
  [/government discussions?|policy discussions?|talks?/gi, "政策讨论"],
  [/government/gi, "政府"],
  [/trump administration/gi, "特朗普政府"],
  [/trump/gi, "特朗普"],
  [/administration/gi, "政府"],
  [/expectations?/gi, "预期"],
  [/favorable/gi, "利好"],
  [/friendly/gi, "友好"],
  [/of a more/gi, "更加"],
  [/investors'/gi, "投资者的"],
  [/policies/gi, "政策"],
  [/lack of progress/gi, "进展不足"],
  [/bill in congress|congress(?:ional)? bill/gi, "国会法案"],
  [/congress/gi, "国会"],
  [/bill/gi, "法案"],
  [/stalled/gi, "停滞"],
  [/institutional flows?|fund flows?|capital flows?/gi, "资金流向"],
  [/institutional selling/gi, "机构卖出"],
  [/large financial institutions?/gi, "大型金融机构"],
  [/financial institutions?/gi, "金融机构"],
  [/holdings?/gi, "持仓"],
  [/reducing their/gi, "减少其"],
  [/selling/gi, "卖出"],
  [/market volatility|volatility/gi, "市场波动"],
  [/trading volume|volume/gi, "成交量"],
  [/velocity/gi, "流通速度"],
  [/speed of/gi, "速度"],
  [/circulation/gi, "流通"],
  [/economy/gi, "经济"],
  [/economic activity/gi, "经济活动"],
  [/mining difficulty|hashrate|hash rate/gi, "挖矿难度与算力"],
  [/on-chain activity|onchain activity/gi, "链上活动"],
  [/exchange inflows?|exchange outflows?/gi, "交易所资金流"],
  [/whale activity|large holders?/gi, "大户活动"],
  [/futures open interest|open interest/gi, "期货未平仓合约"],
  [/funding rates?/gi, "资金费率"],
  [/bureau of industry and security|bis/gi, "美国工业与安全局"],
  [/export administration regulations|ear/gi, "出口管理条例"],
  [/export controls?/gi, "出口管制"],
  [/export restrictions?/gi, "出口限制"],
  [/semiconductor manufacturing items?/gi, "半导体制造项目"],
  [/semiconductor chips?|semiconductors?/gi, "半导体芯片"],
  [/advanced computing integrated circuits?|advanced computing items?/gi, "先进计算芯片"],
  [/national security concerns?/gi, "国家安全担忧"],
  [/military modernization/gi, "军事现代化"],
  [/china'?s access/gi, "中国获取能力"],
  [/critical technolog(?:y|ies)/gi, "关键技术"],
  [/supply chains?/gi, "供应链"],
  [/policy rationale/gi, "政策理由"],
  [/commerce department/gi, "美国商务部"],
  [/official statements?/gi, "官方声明"],
  [/taiwan/gi, "台湾"],
  [/huawei/gi, "华为"],
  [/smic/gi, "中芯国际"],
  [/nexperia/gi, "安世半导体"],
  [/united states|u\.s\.|us\b/gi, "美国"],
  [/china/gi, "中国"],
];

function localizeCausalText(text: string, locale: "zh" | "en"): string {
  if (locale === "en") return text;

  let localized = text.replaceAll("_", " ");
  for (const [pattern, replacement] of ZH_CAUSAL_LABELS) {
    localized = localized.replace(pattern, replacement);
  }

  return localized
    .replace(/\bcontrols\b/gi, "管制")
    .replace(/\brestrictions\b/gi, "限制")
    .replace(/\brules\b/gi, "规则")
    .replace(/\bpolicy\b/gi, "政策")
    .replace(/\breasons\b/gi, "原因")
    .replace(/\bmarket\b/gi, "市场")
    .replace(/\bprice\b/gi, "价格")
    .replace(/\bdrop\b/gi, "下跌")
    .replace(/\btoday\b/gi, "今日")
    .replace(/\bspeed\b/gi, "速度")
    .replace(/\bfactors?\b/gi, "因素")
    .replace(/\bcauses?\b/gi, "原因")
    .replace(/\bin\b/gi, "在")
    .replace(/\s+/g, " ")
    .trim();
}

function hasUnlocalizedEnglish(text: string): boolean {
  const tokens = text.match(/[A-Za-z]{4,}/g) ?? [];
  return tokens.length > 2;
}

function hasUnlocalizedEnglishLabel(text: string): boolean {
  const tokens = text.match(/[A-Za-z]{4,}/g) ?? [];
  return tokens.length > 1;
}

function localizeCausalLabel(text: string, locale: "zh" | "en"): string {
  const localized = localizeCausalText(text, locale);
  if (locale === "zh" && hasUnlocalizedEnglishLabel(localized)) {
    return "市场影响因素";
  }
  return localized;
}

function localizeCausalDescription(text: string, label: string, locale: "zh" | "en"): string {
  const localized = localizeCausalText(text, locale);
  if (locale === "zh" && hasUnlocalizedEnglish(localized)) {
    return `与${label}相关的证据支撑因素`;
  }
  return localized;
}

function toLocalChain(
  chain: ApiChain,
  locale: "zh" | "en",
  evidencePool: ApiEvidence[]
): CausalChain {
  const mapNodeType = (type: string): CausalNodeType => {
    if (type === "cause") return "factor";
    if (type === "effect") return "outcome";
    return "intermediate";
  };

  const mapEdgeStrength = (strength: number): EdgeStrength => {
    if (strength >= 0.7) return "strong";
    if (strength >= 0.4) return "weak";
    return "uncertain";
  };

  const mapReliability = (reliability: string): EvidenceReliability => {
    if (reliability === "0.50") return "medium";
    if (reliability === "0.00") return "weak";

    const score = Number(reliability);
    if (Number.isNaN(score)) return "medium";
    if (score >= 0.75) return "strong";
    if (score >= 0.5) return "medium";
    return "weak";
  };

  return {
    metadata: {
      id: chain.chain_id,
      title: localizeCausalText(chain.label, locale),
      outcomeLabel: localizeCausalText(
        chain.nodes[chain.nodes.length - 1]?.label ?? chain.label,
        locale
      ),
      totalNodes: chain.nodes.length,
      totalEdges: chain.edges.length,
      maxDepth: chain.depth,
      confidence: chain.probability,
      primaryEvidenceCount: chain.supporting_evidence_ids.length,
      counterfactualSummary: {
        intervention: locale === "en" ? "Counterfactual details remain limited in the OSS evidence board" : "当前 OSS 证据墙中的反事实详情仍然有限",
        outcomeChange: locale === "en" ? "Detailed counterfactual summary not yet rendered on homepage" : "首页暂未完整渲染反事实摘要",
        probabilityShift: 0,
        description: locale === "en" ? "This homepage currently renders the selected causal chain and labels whether the result is live or demo." : "当前首页会渲染所选因果链，并标注结果来自 real analysis 还是 demo。",
      },
    },
    nodes: chain.nodes.map((node) => ({
      id: node.id,
      label: localizeCausalLabel(node.label, locale),
      type: mapNodeType(node.type),
      probability: Math.round(node.probability * 100),
      depth: node.depth,
      description: {
        brief: localizeCausalDescription(
          node.description,
          localizeCausalLabel(node.label, locale),
          locale
        ),
        detail: localizeCausalDescription(
          node.description,
          localizeCausalLabel(node.label, locale),
          locale
        ),
      },
      upstreamIds: node.upstream_ids,
      evidenceIds: [...node.supporting_evidence_ids, ...node.refuting_evidence_ids],
    })),
    edges: chain.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      strength: edge.strength,
      type: mapEdgeStrength(edge.strength),
      evidence: evidencePool
        .filter((item) => edge.supporting_evidence_ids.includes(item.id) || edge.refuting_evidence_ids.includes(item.id))
        .map((item) => ({
          evidenceId: item.id,
          content: item.content,
          reliability: mapReliability(item.reliability),
          causalWeight: Number(item.reliability) || 0.5,
        })),
    })),
    upstreamMap: Object.fromEntries(
      chain.nodes.map((node) => [
        node.id,
        chain.nodes
          .filter((candidate) => node.upstream_ids.includes(candidate.id))
          .map((candidate) => ({
            id: candidate.id,
            label: localizeCausalText(candidate.label, locale),
            probability: Math.round(candidate.probability * 100),
            depth: candidate.depth,
            type: mapNodeType(candidate.type),
          })),
      ])
    ),
  };
}

function makePlaceholderChain(query: string, locale: "zh" | "en"): CausalChain {
  return {
    metadata: {
      id: "EMPTY-CHAIN",
      title: locale === "en" ? "No causal chain available" : "暂无可展示的因果链",
      outcomeLabel: query,
      totalNodes: 0,
      totalEdges: 0,
      maxDepth: 0,
      confidence: 0,
      primaryEvidenceCount: 0,
      counterfactualSummary: {
        intervention:
          locale === "en" ? "No counterfactual summary available" : "暂无反事实摘要",
        outcomeChange:
          locale === "en" ? "Live analysis did not produce a usable chain" : "本次 live 分析未产出可用链路",
        probabilityShift: 0,
        description:
          locale === "en"
            ? "Inspect the status note and error details before retrying."
            : "请先查看状态说明和错误信息，再决定是否重试。",
      },
    },
    nodes: [],
    edges: [],
    upstreamMap: {},
  };
}

const caveat = Caveat({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-caveat",
  display: "swap",
});

// Color palette for different node types
const STICKY_COLORS = [
  "sticky-yellow",
  "sticky-cream",
  "sticky-blue",
  "sticky-pink",
  "sticky-mint",
  "sticky-lavender",
] as const;

type StickyColor = (typeof STICKY_COLORS)[number];

// Note dimensions (width, height) for anchor calculation
const NOTE_DIMS: Record<StickyColor, [number, number]> = {
  "sticky-yellow": [180, 130],
  "sticky-cream": [170, 125],
  "sticky-blue": [165, 122],
  "sticky-pink": [160, 120],
  "sticky-mint": [170, 125],
  "sticky-lavender": [155, 118],
};

// Derived sticky note from ChainNode
interface StickyNote {
  id: string;
  title: string;
  depth: number;
  detail: string;
  tag: string;
  tagClass: string;
  color: StickyColor;
  top: number;
  left: number;
  rotate: number;
  // Geometry for anchor calculation
  width: number;
  height: number;
}

interface DragState {
  id: string;
  pointerX: number;
  pointerY: number;
  left: number;
  top: number;
}

interface CausalStringPath {
  id: string;
  source: string;
  target: string;
  d: string;
  opacity: number;
  width: number;
}

// Map node type to tag class
function getTagClass(type: ChainNode["type"]): string {
  switch (type) {
    case "outcome":
      return "tag-effect";
    case "factor":
      return "tag-cause";
    case "intermediate":
      return "tag-mediator";
    default:
      return "tag-cause";
  }
}

function getTagLabel(type: ChainNode["type"], t: (key: TranslationKey) => string): string {
  switch (type) {
    case "outcome":
      return t("graph.type.outcome");
    case "factor":
      return t("graph.type.factor");
    case "intermediate":
      return t("graph.type.intermediate");
    default:
      return type;
  }
}

// Get sticky color based on node properties for visual variety
function getStickyColor(index: number, depth: number): StickyColor {
  // Rotate through colors based on index and depth for variety
  const combined = (index * 3 + depth * 2) % STICKY_COLORS.length;
  return STICKY_COLORS[combined];
}

function computeLayout(
  nodes: ChainNode[],
  boardWidth: number,
  boardHeight: number,
  headerHeight: number,
  getLabel: (type: ChainNode["type"]) => string
): StickyNote[] {
  if (nodes.length === 0) return [];

  const leftMargin = 220;
  const rightMargin = 220;
  const topMargin = headerHeight + 50;
  const bottomMargin = 60;
  const usableWidth = boardWidth - leftMargin - rightMargin;
  const usableHeight = boardHeight - topMargin - bottomMargin;

  const rotations = [-3, -1.5, 0.5, 2, -2, 1.5, -0.5, 3, -2.5, 1];

  const maxDepth = Math.max(...nodes.map(n => n.depth));
  const n = nodes.length;

  const sortedNodes = [...nodes].sort((a, b) => a.depth - b.depth);

  // Distribute nodes in a staggered grid-like pattern across the canvas.
  // Each node gets a unique cell so they never start on top of each other.
  const cols = Math.min(n, Math.max(2, Math.ceil(Math.sqrt(n * (usableWidth / usableHeight)))));
  const rows = Math.ceil(n / cols);

  const cellW = usableWidth / cols;
  const cellH = usableHeight / rows;

  const prelimPositions: { node: ChainNode; x: number; y: number }[] = [];

  sortedNodes.forEach((node, i) => {
    // Fill in a zigzag pattern: even rows left-to-right, odd rows right-to-left
    const row = Math.floor(i / cols);
    const colInRow = i % cols;
    const col = row % 2 === 0 ? colInRow : (cols - 1 - colInRow);

    const cx = leftMargin + col * cellW + cellW / 2;
    const cy = topMargin + row * cellH + cellH / 2;

    // Small deterministic offset within cell for organic feel
    const ox = ((i * 37) % 17 - 8) * 2;
    const oy = ((i * 23) % 13 - 6) * 2;

    prelimPositions.push({ node, x: cx + ox, y: cy + oy });
  });

  // Collision avoidance — generous minimum gap + more passes
  const minGapX = 210;
  const minGapY = 170;

  for (let pass = 0; pass < 10; pass++) {
    for (let i = 0; i < prelimPositions.length; i++) {
      for (let j = i + 1; j < prelimPositions.length; j++) {
        const a = prelimPositions[i];
        const b = prelimPositions[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const overlapX = minGapX - Math.abs(dx);
        const overlapY = minGapY - Math.abs(dy);

        if (overlapX > 0 && overlapY > 0) {
          const pushX = overlapX / 2 + 8;
          const pushY = overlapY / 2 + 8;
          if (overlapX < overlapY) {
            a.x -= Math.sign(dx || 1) * pushX;
            b.x += Math.sign(dx || 1) * pushX;
          } else {
            a.y -= Math.sign(dy || 1) * pushY;
            b.y += Math.sign(dy || 1) * pushY;
          }
        }
      }
    }
  }

  return prelimPositions.map((pos, i) => {
    const color = getStickyColor(i, pos.node.depth);
    const [width, height] = NOTE_DIMS[color];
    const left = Math.max(leftMargin, Math.min(pos.x, boardWidth - rightMargin - width));
    const top = Math.max(topMargin, Math.min(pos.y, boardHeight - bottomMargin - height));

    return {
      id: pos.node.id,
      title: pos.node.label,
      depth: pos.node.depth,
      detail: pos.node.description.brief,
      tag: getLabel(pos.node.type),
      tagClass: getTagClass(pos.node.type),
      color,
      top,
      left,
      rotate: rotations[i % rotations.length],
      width,
      height,
    };
  });
}

// Compute pushpin anchor from note geometry
// Pushpin SVG: 22x22, positioned top:-10px left:50% transform:translateX(-50%)
// Circle center in SVG: cx=12, cy=8
// Anchor is at card_width/2 horizontally, card_top-2 vertically
function getPushpinAnchor(note: StickyNote): [number, number] {
  return [note.left + note.width / 2, note.top - 2];
}

// Build a causal edge path between two notes with natural catenary sag
function buildEdgePath(
  sx: number,
  sy: number,
  tx: number,
  ty: number,
  strength: number
): { d: string; opacity: number; width: number } {
  const dx = tx - sx;
  const dy = ty - sy;
  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);
  const dist = Math.sqrt(dx * dx + dy * dy);

  // Control point offset based on distance and direction
  const cpOffset = Math.min(Math.max(absDx, absDy) * 0.4, 120);

  // Natural gravity sag — string droops in the middle
  const sag = Math.min(dist * 0.15, 40) * Math.sign(dy === 0 ? 1 : dy);

  // Choose control point configuration based on dominant direction
  let c1x: number, c1y: number, c2x: number, c2y: number;

  if (absDy > absDx * 1.5) {
    // Primarily vertical: s-curve with sag
    c1x = sx;
    c1y = sy + cpOffset * Math.sign(dy) + sag * 0.3;
    c2x = tx;
    c2y = ty - cpOffset * Math.sign(dy) + sag * 0.3;
  } else if (absDx > absDy * 1.5) {
    // Primarily horizontal: arc with natural droop
    c1x = sx + cpOffset * Math.sign(dx);
    c1y = sy + sag * 0.4;
    c2x = tx - cpOffset * Math.sign(dx);
    c2y = ty + sag * 0.4;
  } else {
    // Diagonal: balanced curve with sag
    c1x = sx + cpOffset * 0.7 * Math.sign(dx);
    c1y = sy + cpOffset * 0.3 * Math.sign(dy) + sag * 0.5;
    c2x = tx - cpOffset * 0.7 * Math.sign(dx);
    c2y = ty - cpOffset * 0.3 * Math.sign(dy) + sag * 0.5;
  }

  const opacity = 0.35 + strength * 0.35; // 0.35-0.70
  const width = 1 + strength * 1.5; // 1.5-2.5

  return {
    d: `M ${sx} ${sy} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${tx} ${ty}`,
    opacity,
    width,
  };
}

// Compute RED_STRINGS from chain edges using pushpin anchors
function computeCausalStrings(
  notes: StickyNote[],
  edges: ChainEdge[]
): CausalStringPath[] {
  const noteMap = new Map(notes.map((n) => [n.id, n]));
  const paths: CausalStringPath[] = [];

  for (const edge of edges) {
    const source = noteMap.get(edge.source);
    const target = noteMap.get(edge.target);
    if (!source || !target) continue;

    const [sx, sy] = getPushpinAnchor(source);
    const [tx, ty] = getPushpinAnchor(target);

    paths.push({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      ...buildEdgePath(sx, sy, tx, ty, edge.strength),
    });
  }

  return paths;
}



function Pushpin() {
  return (
    <svg
      className="absolute pointer-events-none"
      style={{
        top: "-10px",
        left: "50%",
        transform: "translateX(-50%)",
        width: "22px",
        height: "22px",
        filter: "drop-shadow(1px 2px 3px rgba(60, 40, 20, 0.35))",
        zIndex: 20,
      }}
      viewBox="0 0 24 24"
    >
      <defs>
        <linearGradient id="pinRed" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: "#e05555" }} />
          <stop offset="45%" style={{ stopColor: "#c03535" }} />
          <stop offset="100%" style={{ stopColor: "#8a2020" }} />
        </linearGradient>
        <radialGradient id="pinHead3D" cx="35%" cy="30%" r="65%">
          <stop offset="0%" style={{ stopColor: "#f07070" }} />
          <stop offset="50%" style={{ stopColor: "#b83030" }} />
          <stop offset="100%" style={{ stopColor: "#701818" }} />
        </radialGradient>
        <linearGradient id="pinMetal" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: "#d4c4a4" }} />
          <stop offset="40%" style={{ stopColor: "#f0e0c0" }} />
          <stop offset="60%" style={{ stopColor: "#c8b898" }} />
          <stop offset="100%" style={{ stopColor: "#a89878" }} />
        </linearGradient>
      </defs>
      <circle cx="12" cy="8" r="7" fill="url(#pinHead3D)" />
      <ellipse cx="9.5" cy="5.5" rx="2.5" ry="1.8" fill="rgba(255,255,255,0.45)" />
      <circle cx="14" cy="10.5" r="1.2" fill="rgba(0,0,0,0.15)" />
      <rect x="11.2" y="14" width="1.6" height="7" rx="0.8" fill="url(#pinMetal)" />
    </svg>
  );
}

function StickyCard({
  note,
  isSelected,
  isDragging,
  depthLabel,
  onClick,
  onMouseDown,
}: {
  note: StickyNote;
  isSelected: boolean;
  isDragging: boolean;
  depthLabel: string;
  onClick: () => void;
  onMouseDown: (event: React.MouseEvent<HTMLDivElement>) => void;
}) {
  return (
    <div
      className={`sticky-card ${note.color} ${isSelected ? "ring-2 ring-[#a0503c]/40" : ""}`}
      style={{
        position: "absolute",
        top: note.top,
        left: note.left,
        width: `${note.width}px`,
        padding: "22px 14px 14px",
        rotate: `${note.rotate}deg`,
        cursor: isDragging ? "grabbing" : "grab",
        transition: isDragging ? "none" : "box-shadow 0.18s ease, transform 0.18s ease",
        zIndex: isDragging ? 40 : isSelected ? 28 : 18,
        transform: isDragging ? "scale(1.02)" : undefined,
        willChange: isDragging ? "top, left, transform" : undefined,
      }}
      onClick={onClick}
      onMouseDown={onMouseDown}
    >
      <Pushpin />
      <div className="tape-strip tape-left" />
      <div className="tape-strip tape-right" />
      <div
        className="paper-texture"
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "2px",
          pointerEvents: "none",
          overflow: "hidden",
        }}
      />
      <div style={{ transform: `rotate(${-note.rotate}deg)`, position: "relative", zIndex: 1 }}>
        <div className="card-title">{note.title}</div>
        <div className="card-subtitle">{depthLabel} {note.depth}</div>
        <div className="card-detail">
          {note.detail}
        </div>
        <span className={`card-tag ${note.tagClass}`}>{note.tag}</span>
      </div>
    </div>
  );
}

export default function Home() {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedFocusEdgeId, setSelectedFocusEdgeId] = useState<string | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const { locale, setLocale, t } = useI18n();
  const localizedDemo = useMemo(() => getLocalizedMockData(locale), [locale]);
  const [activeChain, setActiveChain] = useState(localizedDemo.primaryChain);
  const [currentQuery, setCurrentQuery] = useState("");
  const [lastQuery, setLastQuery] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [selectedModel, setSelectedModel] = useState("openrouter");
  const [selectedExplicitModel, setSelectedExplicitModel] = useState("");
  const [availableModels, setAvailableModels] = useState<Record<string, string>>({});
  const [statusNote, setStatusNote] = useState("");
  const [availableChains, setAvailableChains] = useState<AnalyzeResponseV2["chains"]>([]);
  const [recommendedChainId, setRecommendedChainId] = useState<string | null>(null);
  const [evidencePool, setEvidencePool] = useState<AnalyzeResponseV2["evidences"]>([]);
  const [pipelineEval, setPipelineEval] = useState<AnalyzeResponseV2["evaluation"]>(null);
  const [uncertaintyReport, setUncertaintyReport] = useState<AnalyzeResponseV2["uncertainty_report"]>(null);
  const [evidenceSourceFilter, setEvidenceSourceFilter] = useState<string>("all");
  const [evidenceStanceFilter, setEvidenceStanceFilter] = useState<"all" | "supporting" | "refuting">("all");
  const [evidenceConfidenceFilter, setEvidenceConfidenceFilter] = useState<"all" | "strong" | "medium" | "weak">("all");
  const [evidenceQualityFilter, setEvidenceQualityFilter] = useState<
    "all" | "trusted_fulltext" | "fulltext" | "store_cache" | "fallback" | "base"
  >("all");
  const [showAllEvidence, setShowAllEvidence] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<AnalysisUiState>({
    isDemo: true,
    demoTopic: null,
    loading: false,
    mode: "demo",
    freshnessStatus: "unknown",
    timeRange: null,
    partialLiveReasons: [],
  });
  const [pipelineProgress, setPipelineProgress] = useState<{
    step: string;
    stepIndex: number;
    totalSteps: number;
    message: string;
  } | null>(null);
  const activeRequestIdRef = useRef(0);

  const mockPrimaryChain = activeChain;
  
  // Board drag/pan state
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [draggingNoteId, setDraggingNoteId] = useState<string | null>(null);
  const boardRef = useRef<HTMLDivElement>(null);
  const noteDragRef = useRef<DragState | null>(null);

  // SSR-safe: compute layout only on client via useEffect
  const [notes, setNotes] = useState<StickyNote[]>([]);
  const [boardReady, setBoardReady] = useState(false);

  useEffect(() => {
    if (availableChains.length > 0) {
      const currentApiChain =
        availableChains.find((chain) => chain.chain_id === activeChain.metadata.id) ??
        availableChains.find((chain) => chain.chain_id === recommendedChainId) ??
        availableChains[0];
      setActiveChain(toLocalChain(currentApiChain, locale, evidencePool));
      return;
    }

    if (analysisMode.loading) {
      setActiveChain(makePlaceholderChain(currentQuery || lastQuery, locale));
      return;
    }

    if (analysisMode.isDemo) {
      setActiveChain(localizedDemo.primaryChain);
    }
  }, [
    activeChain.metadata.id,
    analysisMode.isDemo,
    analysisMode.loading,
    availableChains,
    currentQuery,
    evidencePool,
    lastQuery,
    locale,
    localizedDemo.primaryChain,
    recommendedChainId,
  ]);

  useEffect(() => {
    let cancelled = false;
    fetch("http://localhost:8000/api/providers")
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        const models = data?.providers?.[selectedModel]?.models ?? {};
        setAvailableModels(models);
        const keys = Object.keys(models);
        setSelectedExplicitModel(keys[0] ?? "");
      })
      .catch(() => {
        if (!cancelled) {
          setAvailableModels({});
          setSelectedExplicitModel("");
        }
      });
    return () => { cancelled = true; };
  }, [selectedModel]);

  useEffect(() => {
    setBoardReady(false);
    const width = window.innerWidth;
    const height = window.innerHeight;
    const headerHeight = 52;

    const computedNotes = computeLayout(
      mockPrimaryChain.nodes,
      width,
      height,
      headerHeight,
      (type) => getTagLabel(type, t)
    );

    setNotes(computedNotes);
    setBoardReady(true);
  }, [mockPrimaryChain, locale, t]);

  const causalStrings = computeCausalStrings(notes, mockPrimaryChain.edges);
  const primaryChainTitle = mockPrimaryChain.metadata.title;
  const activeApiChain = useMemo(
    () => availableChains.find((chain) => chain.chain_id === mockPrimaryChain.metadata.id) ?? null,
    [availableChains, mockPrimaryChain.metadata.id]
  );
  const selectedEvidenceEdgeIds = useMemo(
    () =>
      selectedEvidenceId
        ? new Set(
            mockPrimaryChain.edges
              .filter((edge) => edge.evidence.some((item) => item.evidenceId === selectedEvidenceId))
              .map((edge) => edge.id)
          )
        : new Set<string>(),
    [mockPrimaryChain.edges, selectedEvidenceId]
  );
  const connectedNodeIds = useMemo(() => {
    const next = new Set<string>();
    if (selectedNodeId) {
      next.add(selectedNodeId);
    }
    for (const edge of mockPrimaryChain.edges) {
      const linkedToSelectedNode = selectedNodeId && (edge.source === selectedNodeId || edge.target === selectedNodeId);
      const linkedToFocusEdge = selectedFocusEdgeId === edge.id;
      const linkedToEvidence = selectedEvidenceEdgeIds.has(edge.id);
      if (linkedToSelectedNode || linkedToFocusEdge || linkedToEvidence) {
        next.add(edge.source);
        next.add(edge.target);
      }
    }
    return next;
  }, [mockPrimaryChain.edges, selectedEvidenceEdgeIds, selectedFocusEdgeId, selectedNodeId]);
  const selectedApiNode = activeApiChain?.nodes.find((node) => node.id === selectedNodeId) ?? null;
  const selectedApiEdges = useMemo(
    () =>
      activeApiChain?.edges.filter(
        (edge) =>
          edge.source === selectedNodeId ||
          edge.target === selectedNodeId ||
          edge.id === selectedFocusEdgeId ||
          (!!selectedEvidenceId &&
            [...edge.supporting_evidence_ids, ...edge.refuting_evidence_ids].includes(selectedEvidenceId))
      ) ?? [],
    [activeApiChain, selectedEvidenceId, selectedFocusEdgeId, selectedNodeId]
  );
  const nodeTypeCounts = mockPrimaryChain.nodes.reduce(
    (acc, node) => {
      acc[node.type] += 1;
      return acc;
    },
    { outcome: 0, factor: 0, intermediate: 0 }
  );
  const totalEvidenceItems = Math.max(
    mockPrimaryChain.edges.reduce((sum, edge) => sum + edge.evidence.length, 0),
    evidencePool.length
  );
  const selectedNodeData = mockPrimaryChain.nodes.find((node) => node.id === selectedNodeId);
  const selectedNodeSupportingCount = mockPrimaryChain.edges.reduce(
    (sum, edge) =>
      edge.source === selectedNodeId || edge.target === selectedNodeId
        ? sum + edge.evidence.filter((item) => item.reliability !== "weak").length
        : sum,
    0
  );
  const selectedNodeUncertainty = selectedNodeData
    ? Math.round(
        ((selectedApiNode?.uncertainty?.overall_score ??
          uncertaintyReport?.per_node?.[selectedNodeData.id]?.overall_score ??
          Math.max(0, 1 - selectedNodeData.probability / 100)) * 100)
      )
    : Math.max(0, 100 - Math.round(mockPrimaryChain.metadata.confidence * 100));
  const selectedEdgeIds = useMemo(() => {
    const next = new Set<string>(selectedEvidenceEdgeIds);
    if (selectedFocusEdgeId) {
      next.add(selectedFocusEdgeId);
    }
    if (selectedNodeId) {
      for (const edge of mockPrimaryChain.edges) {
        if (edge.source === selectedNodeId || edge.target === selectedNodeId) {
          next.add(edge.id);
        }
      }
    }
    return next;
  }, [mockPrimaryChain.edges, selectedEvidenceEdgeIds, selectedFocusEdgeId, selectedNodeId]);
  const chainProbabilityItems = availableChains.slice(0, 3);
  const activeChainIsRecommended = !recommendedChainId || mockPrimaryChain.metadata.id === recommendedChainId;
  const activeChainConfidence = Math.round(mockPrimaryChain.metadata.confidence * 100);
  const hasLowConfidence = activeChainConfidence < 50;
  const hasLowEvidenceCoverage = mockPrimaryChain.metadata.primaryEvidenceCount < 3;
  const hasHighUncertainty = selectedNodeUncertainty > 60;
  const selectedNodeEvidenceIds = selectedNodeData?.evidenceIds ?? [];
  const activeChainEvidenceIds = new Set(
    mockPrimaryChain.edges.flatMap((edge) => edge.evidence.map((item) => item.evidenceId))
  );
  const selectedNodeCitationByEvidenceId = useMemo(() => {
    const entries = selectedApiEdges.flatMap((edge) =>
      (edge.citation_spans ?? []).map((span) => [span.evidence_id, span] as const)
    );
    return new Map(entries);
  }, [selectedApiEdges]);
  const sourceFilterOptions = useMemo(
    () => ["all", ...Array.from(new Set(evidencePool.map((item) => item.source))).sort()],
    [evidencePool]
  );
  const relatedEvidence = evidencePool.filter((item) => {
    if (selectedEvidenceId) {
      return item.id === selectedEvidenceId;
    }

    if (selectedNodeEvidenceIds.length > 0) {
      return selectedNodeEvidenceIds.includes(item.id);
    }

    if (activeChainEvidenceIds.size > 0) {
      return activeChainEvidenceIds.has(item.id);
    }

    return false;
  });
  const evidenceBase = relatedEvidence.length > 0 ? relatedEvidence : evidencePool;
  const getReliabilityLabel = useCallback((reliability: string) => {
    const score = Number(reliability);
    if (Number.isNaN(score)) {
      return t("home.evidence.medium");
    }
    if (score >= 0.75) {
      return t("home.evidence.strong");
    }
    if (score >= 0.5) {
      return t("home.evidence.medium");
    }
    return t("home.evidence.weak");
  }, [t]);
  const visibleEvidence = useMemo(() => {
    return [...evidenceBase]
      .filter((item) => {
        if (evidenceSourceFilter !== "all" && item.source !== evidenceSourceFilter) {
          return false;
        }
        if (evidenceStanceFilter === "supporting" && !item.is_supporting) {
          return false;
        }
        if (evidenceStanceFilter === "refuting" && item.is_supporting) {
          return false;
        }

        const label = getReliabilityLabel(item.reliability);
        if (evidenceConfidenceFilter === "strong" && label !== t("home.evidence.strong")) {
          return false;
        }
        if (evidenceConfidenceFilter === "medium" && label !== t("home.evidence.medium")) {
          return false;
        }
        if (evidenceConfidenceFilter === "weak" && label !== t("home.evidence.weak")) {
          return false;
        }
        if (evidenceQualityFilter !== "all") {
          const category = evidenceQualityCategory(item);
          if (category !== evidenceQualityFilter) {
            return false;
          }
        }

        return true;
      })
      .sort((left, right) => {
        const weightDelta = evidenceSortWeight(left) - evidenceSortWeight(right);
        if (weightDelta !== 0) {
          return weightDelta;
        }

        const leftReliability = Number(left.reliability);
        const rightReliability = Number(right.reliability);
        const normalizedLeft = Number.isNaN(leftReliability) ? 0.0 : leftReliability;
        const normalizedRight = Number.isNaN(rightReliability) ? 0.0 : rightReliability;
        if (normalizedLeft !== normalizedRight) {
          return normalizedRight - normalizedLeft;
        }

        return left.id.localeCompare(right.id);
      });
  }, [
    evidenceBase,
    evidenceSourceFilter,
    evidenceStanceFilter,
    evidenceConfidenceFilter,
    evidenceQualityFilter,
    getReliabilityLabel,
    t,
  ]);
  const prioritizedEvidence = useMemo(() => {
    if (evidenceQualityFilter !== "all") {
      return visibleEvidence;
    }

    if (showAllEvidence) {
      return visibleEvidence;
    }

    const prioritized = visibleEvidence.filter(
      (item) => !["fallback", "base"].includes(evidenceQualityCategory(item))
    );
    return prioritized.length > 0 ? prioritized : visibleEvidence;
  }, [visibleEvidence, evidenceQualityFilter, showAllEvidence]);
  const hiddenEvidenceCount = Math.max(0, visibleEvidence.length - prioritizedEvidence.length);
  const hiddenEvidenceBreakdown = useMemo(() => {
    const hidden = visibleEvidence.filter(
      (item) => !prioritizedEvidence.some((candidate) => candidate.id === item.id)
    );
    return {
      fallback: hidden.filter((item) => evidenceQualityCategory(item) === "fallback").length,
      base: hidden.filter((item) => evidenceQualityCategory(item) === "base").length,
    };
  }, [prioritizedEvidence, visibleEvidence]);
  const chainCompareItems = useMemo(
    () =>
      availableChains.slice(0, 4).map((chain) => ({
        chain_id: chain.chain_id,
        label: localizeCausalText(chain.label, locale),
        probability: Math.round(chain.probability * 100),
        supportCount: chain.supporting_evidence_ids.length,
        refuteCount: chain.refuting_evidence_ids.length,
        edgeCount: chain.edges.length,
        nodeCount: chain.nodes.length,
      })),
    [availableChains, locale]
  );
  const analysisBadgeLabel = formatAnalysisBadge(analysisMode.mode, locale);
  const freshnessLabel = formatFreshnessLabel(analysisMode.freshnessStatus, locale);
  const timeRangeLabel = formatTimeRangeLabel(analysisMode.timeRange, locale);
  const activeProgressIndex = pipelineProgress
    ? Math.max(progressStageOrder.indexOf(pipelineProgress.step), Math.max(0, pipelineProgress.stepIndex - 1))
    : -1;

  // Background drag handlers
  const handleBoardMouseDown = useCallback((e: React.MouseEvent) => {
    // Only start drag if clicking on the board background (not on notes)
    if ((e.target as HTMLElement).closest(".sticky-card, .string-canvas, .left-panel, .right-panel, .header-bar")) {
      return;
    }
    setIsDragging(true);
    setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
  }, [panOffset]);

  const handleBoardMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;
    setPanOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  }, [isDragging, dragStart]);

  const handleBoardMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleNoteMouseDown = useCallback((note: StickyNote, event: React.MouseEvent<HTMLDivElement>) => {
    event.stopPropagation();
    noteDragRef.current = {
      id: note.id,
      pointerX: event.clientX,
      pointerY: event.clientY,
      left: note.left,
      top: note.top,
    };
    setDraggingNoteId(note.id);
  }, []);

  // Add document-level mouse up listener to catch drag end outside board
  useEffect(() => {
    const handleDocMouseUp = () => {
      setIsDragging(false);
      setDraggingNoteId(null);
      noteDragRef.current = null;
    };
    document.addEventListener("mouseup", handleDocMouseUp);
    return () => document.removeEventListener("mouseup", handleDocMouseUp);
  }, []);

  useEffect(() => {
    if (!draggingNoteId) {
      return;
    }

    const handleMouseMove = (event: MouseEvent) => {
      const drag = noteDragRef.current;
      if (!drag) {
        return;
      }

      const nextLeft = drag.left + (event.clientX - drag.pointerX);
      const nextTop = drag.top + (event.clientY - drag.pointerY);

      setNotes((currentNotes) =>
        currentNotes.map((note) => {
          if (note.id !== drag.id) {
            return note;
          }

          return {
            ...note,
            left: Math.max(196, Math.min(nextLeft, window.innerWidth - 196 - note.width)),
            top: Math.max(70, Math.min(nextTop, window.innerHeight - 60 - note.height)),
          };
        })
      );
    };

    const handleMouseUp = () => {
      setDraggingNoteId(null);
      noteDragRef.current = null;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [draggingNoteId]);

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId));
    setSelectedFocusEdgeId(null);
    setSelectedEvidenceId(null);
  }, []);

  const focusEdge = useCallback((edge: Pick<ApiEdge, "id" | "source" | "target" | "supporting_evidence_ids" | "refuting_evidence_ids">) => {
    setSelectedFocusEdgeId(edge.id);
    setSelectedNodeId(edge.target);
    setSelectedEvidenceId(edge.supporting_evidence_ids[0] ?? edge.refuting_evidence_ids[0] ?? null);
  }, []);

  const focusEvidence = useCallback((item: ApiEvidence) => {
    const matchingEdge =
      activeApiChain?.edges.find((edge) =>
        [...edge.supporting_evidence_ids, ...edge.refuting_evidence_ids].includes(item.id)
      ) ??
      mockPrimaryChain.edges.find((edge) => edge.evidence.some((candidate) => candidate.evidenceId === item.id));

    setSelectedEvidenceId(item.id);
    setSelectedFocusEdgeId(matchingEdge?.id ?? null);
    setSelectedNodeId(matchingEdge?.target ?? null);
  }, [activeApiChain, mockPrimaryChain.edges]);

  const selectedNote = notes.find((n) => n.id === selectedNodeId);

  const runAnalysis = useCallback(async () => {
    const query = currentQuery.trim();
    if (!query) return;

    const requestId = activeRequestIdRef.current + 1;
    activeRequestIdRef.current = requestId;
    setActiveChain(makePlaceholderChain(query, locale));
    setAvailableChains([]);
    setRecommendedChainId(null);
    setEvidencePool([]);
    setPipelineEval(null);
    setUncertaintyReport(null);
    setSelectedNodeId(null);
    setSelectedFocusEdgeId(null);
    setSelectedEvidenceId(null);
    setShowAllEvidence(false);
    setAnalysisMode({
      isDemo: false,
      demoTopic: null,
      loading: true,
      mode: "partial_live",
      freshnessStatus: "unknown",
      timeRange: null,
      partialLiveReasons: [],
    });
    setPipelineProgress(null);
    setStatusNote(locale === "en" ? "Running live analysis…" : "正在执行真实分析…");
    setLastQuery(query);

    const body: Record<string, unknown> = { query, model: selectedModel, api_key: apiKey };
    if (selectedExplicitModel) body.explicit_model = selectedExplicitModel;

    // Helper to process a successful payload (shared between SSE done and fallback)
    const processPayload = (payload: AnalyzeResponseV2) => {
      if (activeRequestIdRef.current !== requestId) return;
      if (payload.chains.length === 0) {
        setAvailableChains([]);
        setRecommendedChainId(null);
        setEvidencePool(payload.evidences);
        setPipelineEval(payload.evaluation ?? null);
        setUncertaintyReport(payload.uncertainty_report ?? null);
        setActiveChain(makePlaceholderChain(payload.query, locale));
        setEvidenceSourceFilter("all");
        setEvidenceStanceFilter("all");
        setEvidenceConfidenceFilter("all");
        setEvidenceQualityFilter("all");
        setShowAllEvidence(false);
        setAnalysisMode({
          isDemo: payload.is_demo,
          demoTopic: payload.demo_topic,
          loading: false,
          mode: payload.analysis_mode,
          freshnessStatus: payload.freshness_status,
          timeRange: payload.time_range ?? null,
          partialLiveReasons: payload.partial_live_reasons ?? [],
        });
        setSelectedNodeId(null);
        setSelectedFocusEdgeId(null);
        setSelectedEvidenceId(null);
        setPanOffset({ x: 0, y: 0 });
        setStatusNote(buildAnalysisStatusNote(payload, locale));
        return;
      }

      const recommended = payload.chains.find((chain) => chain.chain_id === payload.recommended_chain_id) ?? payload.chains[0];
      if (!recommended) throw new Error("No chains returned");

      setAvailableChains(payload.chains);
      setRecommendedChainId(payload.recommended_chain_id);
      setEvidencePool(payload.evidences);
      setPipelineEval(payload.evaluation ?? null);
      setUncertaintyReport(payload.uncertainty_report ?? null);
      setActiveChain(toLocalChain(recommended, locale, payload.evidences));
      setEvidenceSourceFilter("all");
      setEvidenceStanceFilter("all");
      setEvidenceConfidenceFilter("all");
      setEvidenceQualityFilter("all");
      setShowAllEvidence(false);

      setAnalysisMode({
        isDemo: payload.is_demo,
        demoTopic: payload.demo_topic,
        loading: false,
        mode: payload.analysis_mode,
        freshnessStatus: payload.freshness_status,
        timeRange: payload.time_range ?? null,
        partialLiveReasons: payload.partial_live_reasons ?? [],
      });
      setSelectedNodeId(null);
      setSelectedFocusEdgeId(null);
      setSelectedEvidenceId(null);
      setPanOffset({ x: 0, y: 0 });
      setStatusNote(buildAnalysisStatusNote(payload, locale));
      if (false && payload.is_demo && payload.error) {
        setStatusNote(
          locale === "en"
            ? `Analysis failed (${payload.error}). Showing demo fallback.`
            : `分析失败（${payload.error}），当前显示 demo 回退数据。`
        );
      } else if (payload.is_demo) {
        setStatusNote(
          locale === "en"
            ? "Backend returned demo fallback data. Treat this as a structured example, not validated analysis."
            : "后端返回了 demo fallback 数据。请将其视为结构化示例，而非已验证分析。"
        );
      } else {
        setStatusNote(
          locale === "en"
            ? "Live analysis returned a recommended causal chain. Review evidence coverage before trusting it."
            : "真实分析已返回推荐因果链。请先检查证据覆盖，再决定是否相信结果。"
        );
      }
    };

    // Helper for fallback on error
    const fallbackToDemo = () => {
      if (activeRequestIdRef.current !== requestId) return;
      setActiveChain(localizedDemo.primaryChain);
      setAvailableChains([]);
      setRecommendedChainId(null);
      setEvidencePool([]);
      setPipelineEval(null);
      setUncertaintyReport(null);
      setEvidenceQualityFilter("all");
      setShowAllEvidence(false);
      setAnalysisMode({
        isDemo: true,
        demoTopic: null,
        loading: false,
        mode: "demo",
        freshnessStatus: "unknown",
        timeRange: null,
        partialLiveReasons: [],
      });
      setSelectedNodeId(null);
      setSelectedFocusEdgeId(null);
      setSelectedEvidenceId(null);
      setPanOffset({ x: 0, y: 0 });
      setStatusNote(
        locale === "en"
          ? "Live analysis failed; showing local demo board instead."
          : "真实分析失败，当前回退到本地 demo 证据墙。"
      );
    };

    try {
      // Try SSE streaming endpoint first
      const response = await fetch("http://localhost:8000/api/analyze/v2/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const contentType = response.headers.get("content-type") ?? "";

      // If the response is SSE (text/event-stream), consume the stream
      if (contentType.includes("text/event-stream") && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let streamCompleted = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE lines: "data: {...}\n\n"
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? ""; // keep incomplete chunk in buffer

          for (const part of parts) {
            const dataLine = part.trim();
            if (!dataLine.startsWith("data: ")) continue;

            try {
              const event = JSON.parse(dataLine.slice(6));

              if (event.type === "progress") {
                if (activeRequestIdRef.current !== requestId) continue;
                setPipelineProgress({
                  step: event.step ?? "",
                  stepIndex: event.step_index ?? 0,
                  totalSteps: event.total_steps ?? 0,
                  message: event.message ?? "",
                });
                setStatusNote(event.message ?? "");
              } else if (event.type === "done") {
                if (activeRequestIdRef.current !== requestId) continue;
                setPipelineProgress(null);
                const payload = (event.data ?? event) as AnalyzeResponseV2;
                processPayload(payload);
                streamCompleted = true;
              } else if (event.type === "error") {
                if (activeRequestIdRef.current !== requestId) continue;
                setPipelineProgress(null);
                setAnalysisMode({
                  isDemo: true,
                  demoTopic: null,
                  loading: false,
                  mode: "demo",
                  freshnessStatus: "unknown",
                  timeRange: null,
                  partialLiveReasons: [],
                });
                setShowAllEvidence(false);
                setStatusNote(
                  locale === "en"
                    ? `Analysis error: ${event.error}. Showing demo fallback.`
                    : `分析错误：${event.error}，当前显示 demo 回退数据。`
                );
                // Load demo data as fallback
                fallbackToDemo();
                streamCompleted = true;
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }

        // If we exhausted the stream without a "done" event, fall back
        setPipelineProgress(null);
        if (!streamCompleted && activeRequestIdRef.current === requestId) {
          fallbackToDemo();
        }
      } else {
        // Non-SSE response (fallback) — treat as regular JSON
        const payload = (await response.json()) as AnalyzeResponseV2;
        processPayload(payload);
      }
    } catch {
      setPipelineProgress(null);
      fallbackToDemo();
    }
  }, [currentQuery, selectedModel, selectedExplicitModel, apiKey, locale, localizedDemo.primaryChain]);

  return (
    <div
      ref={boardRef}
      className={`${caveat.variable} font-caveat evidence-board no-select`}
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: `
          /* Cork board texture - warm grain */
          repeating-linear-gradient(
            90deg,
            transparent 0px,
            rgba(180, 155, 110, 0.04) 1px,
            transparent 2px,
            transparent 6px
          ),
          repeating-linear-gradient(
            0deg,
            transparent 0px,
            rgba(160, 130, 90, 0.03) 1px,
            transparent 2px,
            transparent 8px
          ),
          radial-gradient(ellipse at 20% 30%, rgba(180, 160, 130, 0.18) 0%, transparent 40%),
          radial-gradient(ellipse at 80% 70%, rgba(200, 180, 150, 0.15) 0%, transparent 40%),
          radial-gradient(ellipse at 50% 50%, rgba(220, 200, 170, 0.08) 0%, transparent 60%),
          linear-gradient(180deg, #f8f4eb 0%, #f0e8d8 50%, #e8dfc8 100%)
        `,
        fontFamily: "var(--font-mono), 'IBM Plex Mono', monospace",
        cursor: isDragging ? "grabbing" : "default",
        userSelect: "none",
      }}
      onMouseDown={handleBoardMouseDown}
      onMouseMove={handleBoardMouseMove}
      onMouseUp={handleBoardMouseUp}
    >
      <svg
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
          zIndex: 1,
          opacity: 0.035,
        }}
        viewBox="0 0 400 400"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <filter id="boardNoise">
            <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="4" stitchTiles="stitch" />
          </filter>
        </defs>
        <rect width="100%" height="100%" filter="url(#boardNoise)" />
      </svg>
      <header
        className="header-bar"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "52px",
          background: "rgba(250, 246, 238, 0.92)",
          backdropFilter: "blur(8px)",
          borderBottom: "1px solid rgba(160, 140, 110, 0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 20px",
          zIndex: 100,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              background: "rgba(180, 80, 60, 0.1)",
              border: "1px solid rgba(180, 80, 60, 0.2)",
              borderRadius: "5px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#a0503c"
              strokeWidth="2"
            >
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1
            className="font-caveat"
            style={{
              fontFamily: "var(--font-caveat), Caveat, cursive",
              color: "#5c4a32",
              fontSize: "1.5rem",
              fontWeight: 500,
              letterSpacing: "0.02em",
              margin: 0,
            }}
          >
            {t("header.title")}
          </h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <span
            className="case-badge"
            style={{
              background: "rgba(180, 80, 60, 0.1)",
              border: "1px solid rgba(180, 80, 60, 0.25)",
              color: "#a0503c",
              padding: "4px 12px",
              borderRadius: "4px",
              fontSize: "0.65rem",
              fontWeight: 500,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
            >
              {t("home.badge.question")}
            </span>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              color: "#8b7355",
              fontSize: "0.65rem",
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                background: "#7cb87c",
                borderRadius: "50%",
                animation: "pulse 2s infinite",
              }}
            />
            <span>
              {analysisMode.loading
                ? t("header.status.processing")
                : analysisBadgeLabel}
            </span>
          </div>
          {pipelineProgress && analysisMode.loading && (
            <div style={{ display: "flex", alignItems: "center", gap: "4px", flex: 1, minWidth: 0 }}>
              <div
                style={{
                  flex: 1,
                  height: "3px",
                  background: "rgba(139, 115, 85, 0.15)",
                  borderRadius: "2px",
                  overflow: "hidden",
                  minWidth: 0,
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${pipelineProgress.totalSteps > 0 ? (pipelineProgress.stepIndex / pipelineProgress.totalSteps) * 100 : 0}%`,
                    background: "linear-gradient(90deg, #7cb87c, #5a9e5a)",
                    borderRadius: "2px",
                    transition: "width 0.4s ease",
                  }}
                />
              </div>
              <span style={{ fontSize: "0.55rem", color: "#8b7355", whiteSpace: "nowrap" }}>
                {pipelineProgress.stepIndex}/{pipelineProgress.totalSteps}
              </span>
            </div>
          )}
          <button
            onClick={() => setLocale(locale === "en" ? "zh" : "en")}
            style={{
              background: "transparent",
              border: "1px solid rgba(160, 140, 110, 0.2)",
              borderRadius: "4px",
              padding: "4px 8px",
              fontSize: "0.6rem",
              color: "#8b7355",
              cursor: "pointer",
            }}
          >
            {locale === "en" ? "EN" : "中"}
          </button>
        </div>
      </header>

      <aside
        className="left-panel"
        style={{
          position: "absolute",
          top: "52px",
          left: 0,
          width: "180px",
          bottom: 0,
          padding: "16px 12px",
          background: "rgba(250, 246, 238, 0.7)",
          backdropFilter: "blur(4px)",
          borderRight: "1px solid rgba(160, 140, 110, 0.15)",
          zIndex: 50,
          overflowY: "auto",
        }}
      >
        <div className="compact-item" style={{ marginBottom: "12px", background: "rgba(255,255,255,0.72)" }}>
          <div className="compact-label">{t("query.label")}</div>
          <textarea
            value={currentQuery}
            onChange={(event) => setCurrentQuery(event.target.value)}
            placeholder={t("query.placeholderExample")}
            style={{
              width: "100%",
              minHeight: "72px",
              resize: "none",
              border: "1px solid rgba(160, 140, 110, 0.18)",
              borderRadius: "6px",
              padding: "8px 10px",
              background: "rgba(255,255,255,0.82)",
              color: "#5c4a32",
              fontSize: "0.68rem",
              lineHeight: 1.5,
              outline: "none",
            }}
          />
          <div className="compact-label" style={{ marginTop: "8px" }}>{t("query.model")}</div>
          <select
            value={selectedModel}
            onChange={(event) => setSelectedModel(event.target.value)}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid rgba(160, 140, 110, 0.18)",
              borderRadius: "6px",
              background: "rgba(255,255,255,0.82)",
              color: "#5c4a32",
              fontSize: "0.65rem",
              outline: "none",
              marginTop: "4px",
            }}
          >
            <option value="openrouter">OpenRouter</option>
            <option value="openai">OpenAI</option>
            <option value="dashscope">DashScope / 阿里百炼</option>
            <option value="zhipu">Zhipu / 智谱</option>
            <option value="moonshot">Moonshot / Kimi</option>
            <option value="deepseek">DeepSeek</option>
          </select>
          {Object.keys(availableModels).length > 0 && (
            <select
              value={selectedExplicitModel}
              onChange={(event) => setSelectedExplicitModel(event.target.value)}
              style={{
                width: "100%",
                padding: "6px 8px",
                border: "1px solid rgba(160, 140, 110, 0.18)",
                borderRadius: "6px",
                background: "rgba(255,255,255,0.82)",
                color: "#5c4a32",
                fontSize: "0.65rem",
                outline: "none",
                marginTop: "4px",
              }}
            >
              {Object.entries(availableModels).map(([id, label]) => (
                <option key={id} value={id}>{label}</option>
              ))}
            </select>
          )}
          <div className="compact-label" style={{ marginTop: "8px" }}>{t("query.apiKey")}</div>
          <input
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder={t("query.apiKeyPlaceholder")}
            style={{
              width: "100%",
              padding: "6px 8px",
              border: "1px solid rgba(160, 140, 110, 0.18)",
              borderRadius: "6px",
              background: "rgba(255,255,255,0.82)",
              color: "#5c4a32",
              fontSize: "0.65rem",
              outline: "none",
              marginTop: "4px",
              boxSizing: "border-box",
            }}
          />
          <div style={{ fontSize: "0.55rem", color: "#8b7355", marginTop: "4px", lineHeight: 1.4 }}>
            {locale === "en"
              ? "Key stored only in your browser — not sent to any third-party server beyond your chosen model provider."
              : "密钥仅存储在本地浏览器中，不会发送至您所选模型提供商以外的任何第三方服务器。"}
          </div>
          <button
            onClick={runAnalysis}
            disabled={analysisMode.loading || !currentQuery.trim()}
            style={{
              marginTop: "8px",
              width: "100%",
              padding: "8px 10px",
              borderRadius: "6px",
              border: "1px solid rgba(59, 110, 165, 0.2)",
              background: analysisMode.loading ? "rgba(59,110,165,0.08)" : "rgba(59,110,165,0.12)",
              color: "#4a7a9e",
              fontSize: "0.68rem",
              fontWeight: 600,
              cursor: analysisMode.loading ? "wait" : "pointer",
            }}
          >
            {analysisMode.loading ? t("header.status.processing") : t("query.submit")}
          </button>
        </div>

        <h2 className="panel-title">{t("panel.hypotheses")}</h2>

        <div className="compact-item">
          <div className="compact-label">{t("home.chain.primary")}</div>
          <div>{primaryChainTitle}</div>
          <div style={{ marginTop: "4px", fontSize: "0.6rem", color: "#7a6b55" }}>
            {t("graph.confidence")} = {activeChainConfidence}%
          </div>
          {activeChainIsRecommended && availableChains.length > 0 && (
            <div style={{ marginTop: "6px", fontSize: "0.56rem", color: "#4a7a9e", letterSpacing: "0.04em", textTransform: "uppercase" }}>
              {locale === "en" ? "Recommended chain" : "推荐链路"}
            </div>
          )}
          {hasLowConfidence && (
            <div style={{ marginTop: "6px", fontSize: "0.58rem", color: "#a0503c", lineHeight: 1.5 }}>
              {locale === "en" ? "Low confidence. Treat this chain as a tentative explanation." : "当前链路置信偏低，请将其视为暂定解释。"}
            </div>
          )}
          {hasLowEvidenceCoverage && (
            <div style={{ marginTop: "4px", fontSize: "0.58rem", color: "#a0503c", lineHeight: 1.5 }}>
              {locale === "en" ? "Evidence coverage is thin. Inspect sources before trusting the result." : "当前证据覆盖偏薄，信任结果前请先检查来源。"}
            </div>
          )}
        </div>

        {chainProbabilityItems.length > 0 && (
          <div className="compact-item">
            <div className="compact-label">{t("home.chain.alternative")}</div>
            {chainProbabilityItems.map((chain) => (
              <button
                key={chain.chain_id}
                onClick={() => {
                  setSelectedNodeId(null);
                  setSelectedFocusEdgeId(null);
                  setSelectedEvidenceId(null);
                  setPanOffset({ x: 0, y: 0 });
                  setActiveChain(toLocalChain(chain, locale, evidencePool));
                }}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  marginTop: "6px",
                  padding: "6px 8px",
                  borderRadius: "4px",
                  border: chain.chain_id === mockPrimaryChain.metadata.id ? "1px solid rgba(59,110,165,0.28)" : "1px solid rgba(160,140,110,0.12)",
                  background: chain.chain_id === mockPrimaryChain.metadata.id ? "rgba(59,110,165,0.08)" : "rgba(255,255,255,0.55)",
                  color: "#5c4a32",
                  fontSize: "0.62rem",
                  cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px" }}>
                  <span>{localizeCausalText(chain.label, locale)}</span>
                  {chain.chain_id === recommendedChainId && (
                    <span style={{ fontSize: "0.5rem", color: "#4a7a9e", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      {locale === "en" ? "Rec" : "推荐"}
                    </span>
                  )}
                </div>
                <div style={{ color: "#8b7355", marginTop: "2px" }}>{t("graph.confidence")} {Math.round(chain.probability * 100)}%</div>
              </button>
            ))}
          </div>
        )}

        {chainCompareItems.length > 1 && (
          <div className="compact-item">
            <div className="compact-label">{locale === "en" ? "Chain compare" : "链路比较"}</div>
            {chainCompareItems.map((chain) => (
              <button
                type="button"
                key={`${chain.chain_id}-compare`}
                onClick={() => {
                  const nextChain = availableChains.find((candidate) => candidate.chain_id === chain.chain_id);
                  if (!nextChain) return;
                  setSelectedNodeId(null);
                  setSelectedFocusEdgeId(null);
                  setSelectedEvidenceId(null);
                  setPanOffset({ x: 0, y: 0 });
                  setActiveChain(toLocalChain(nextChain, locale, evidencePool));
                }}
                style={{
                  width: "100%",
                  marginTop: "6px",
                  padding: "6px 4px",
                  borderWidth: chain.chain_id === mockPrimaryChain.metadata.id ? "1px" : "0",
                  borderStyle: chain.chain_id === mockPrimaryChain.metadata.id ? "solid" : "none",
                  borderColor: chain.chain_id === mockPrimaryChain.metadata.id ? "rgba(59,110,165,0.22)" : "transparent",
                  borderTopWidth: "1px",
                  borderTopStyle: "dashed",
                  borderTopColor: "rgba(160,140,110,0.18)",
                  borderRadius: "4px",
                  background: chain.chain_id === mockPrimaryChain.metadata.id
                    ? "rgba(59,110,165,0.08)"
                    : "transparent",
                  cursor: "pointer",
                  textAlign: "left",
                  paddingTop: "6px",
                  fontSize: "0.58rem",
                  color: "#6b5a42",
                  lineHeight: 1.5,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                  <strong style={{ color: chain.chain_id === mockPrimaryChain.metadata.id ? "#3b6ea5" : "#5c4a32" }}>{chain.label}</strong>
                  <span>{chain.probability}%</span>
                </div>
                <div>
                  {locale === "en"
                    ? `${chain.supportCount} support · ${chain.refuteCount} refute · ${chain.nodeCount} nodes`
                    : `${chain.supportCount} 支撑 · ${chain.refuteCount} 反驳 · ${chain.nodeCount} 节点`}
                </div>
              </button>
            ))}
          </div>
        )}

        <div className="compact-item">
          <div className="compact-label">{t("home.summary.structure")}</div>
          <div>
            {mockPrimaryChain.metadata.totalNodes} {t("graph.nodes")} · {mockPrimaryChain.metadata.totalEdges} {t("graph.edges")}
          </div>
          <div style={{ marginTop: "4px", fontSize: "0.6rem", color: "#7a6b55" }}>
            {t("graph.depth")} {mockPrimaryChain.metadata.maxDepth}
          </div>
        </div>

        <div className="compact-item">
          <div className="compact-label">{t("home.summary.nodeMix")}</div>
          <div>
            {nodeTypeCounts.factor} {t("graph.type.factor")} · {nodeTypeCounts.intermediate} {t("graph.type.intermediate")} · {nodeTypeCounts.outcome} {t("graph.type.outcome")}
          </div>
          <div style={{ marginTop: "4px", fontSize: "0.6rem", color: "#7a6b55" }}>
            {t("home.summary.dragHint")}
          </div>
        </div>

        <h2 className="panel-title" style={{ marginTop: "16px" }}>
          {t("home.stats.title")}
        </h2>
        <div className="compact-item">
          <div style={{ fontSize: "1.2rem", fontWeight: 600, color: "#5c4a32" }}>
            {totalEvidenceItems}
          </div>
          <div style={{ color: "#8b7355" }}>{t("home.stats.evidenceItems")}</div>
        </div>
        <div className="compact-item">
          <div style={{ fontSize: "1.2rem", fontWeight: 600, color: "#5c4a32" }}>
            {mockPrimaryChain.metadata.totalEdges}
          </div>
          <div style={{ color: "#8b7355" }}>{t("home.stats.connections")}</div>
        </div>
        <div className="compact-item">
          <div style={{ fontSize: "1.2rem", fontWeight: 600, color: "#5c4a32" }}>
            {mockPrimaryChain.metadata.primaryEvidenceCount}
          </div>
          <div style={{ color: "#8b7355" }}>{t("home.stats.primaryEvidence")}</div>
        </div>
        <div className="compact-item">
          <div style={{ fontSize: "1.2rem", fontWeight: 600, color: selectedNodeUncertainty > 45 ? "#a0503c" : "#5c4a32" }}>
            {selectedNodeUncertainty}%
          </div>
          <div style={{ color: "#8b7355" }}>{t("home.stats.uncertainty")}</div>
          {hasHighUncertainty && (
            <div style={{ marginTop: "4px", fontSize: "0.56rem", color: "#a0503c", lineHeight: 1.5 }}>
              {locale === "en" ? "High uncertainty. Review upstream assumptions and evidence quality." : "当前不确定性较高，请重点检查上游假设与证据质量。"}
            </div>
          )}
        </div>

        {pipelineEval && (
          <>
            <h2 className="panel-title" style={{ marginTop: "16px" }}>
              {t("home.evaluation.title")}
            </h2>
            <div className="compact-item">
              <div style={{ color: "#8b7355" }}>{t("home.evaluation.confidence")}</div>
              <div style={{ 
                fontSize: "1.2rem", 
                fontWeight: 600, 
                color: pipelineEval.overall_confidence >= 0.7 
                  ? "#5a8a5a" 
                  : pipelineEval.overall_confidence >= 0.4 
                    ? "#a08040" 
                    : "#a0503c"
              }}>
                {Math.round(pipelineEval.overall_confidence * 100)}%
              </div>
            </div>
            {pipelineEval.weaknesses.length > 0 && (
              <div className="compact-item">
                <div style={{ color: "#8b7355", marginBottom: "4px" }}>{t("home.evaluation.weaknesses")}</div>
                {pipelineEval.weaknesses.slice(0, 3).map((weakness, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      fontSize: "0.6rem", 
                      color: "#a0503c", 
                      lineHeight: 1.4,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      marginBottom: "2px"
                    }}
                  >
                    {weakness}
                  </div>
                ))}
              </div>
            )}
            {pipelineEval.recommended_actions.length > 0 && (
              <div className="compact-item">
                <div style={{ color: "#8b7355", marginBottom: "4px" }}>{t("home.evaluation.actions")}</div>
                {pipelineEval.recommended_actions.slice(0, 2).map((action, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      fontSize: "0.58rem", 
                      color: "#5c4a32", 
                      fontStyle: "italic",
                      lineHeight: 1.4,
                      marginBottom: "2px"
                    }}
                  >
                    {action}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </aside>

      <aside
        className="right-panel"
        style={{
          position: "absolute",
          top: "52px",
          right: 0,
          width: "180px",
          bottom: 0,
          padding: "16px 12px",
          background: "rgba(250, 246, 238, 0.7)",
          backdropFilter: "blur(4px)",
          borderLeft: "1px solid rgba(160, 140, 110, 0.15)",
          zIndex: 50,
          overflowY: "auto",
        }}
      >
        <h2 className="panel-title">{t("home.selected.title")}</h2>

        {selectedNote ? (
          <div
            className="compact-item"
            style={{ background: "rgba(255, 250, 240, 0.8)" }}
          >
            <div
              style={{
                fontFamily: "var(--font-caveat), Caveat, cursive",
                fontSize: "1.1rem",
                color: "#3d3225",
                marginBottom: "4px",
              }}
            >
              {selectedNote.title}
            </div>
            <div style={{ color: "#8b7355", fontSize: "0.65rem" }}>
              {t("graph.depth")} {selectedNote.depth}
            </div>
            <div style={{ color: "#8b7355", fontSize: "0.62rem", marginTop: "6px", lineHeight: 1.5 }}>
              {t("home.stats.primaryEvidence")}: {selectedNodeSupportingCount}
              <br />{t("home.stats.uncertainty")}: {selectedNodeUncertainty}%
            </div>
            {(selectedApiNode?.uncertainty?.explanation || uncertaintyReport?.per_node?.[selectedNote.id]?.explanation) && (
              <div style={{ color: "#6b5a42", fontSize: "0.58rem", marginTop: "8px", lineHeight: 1.5 }}>
                {selectedApiNode?.uncertainty?.explanation ?? uncertaintyReport?.per_node?.[selectedNote.id]?.explanation}
              </div>
            )}
          </div>
        ) : (
          <div
            className="compact-item"
            style={{ background: "rgba(255, 250, 240, 0.8)" }}
          >
            <div
              style={{
                fontFamily: "var(--font-caveat), Caveat, cursive",
                fontSize: "1.1rem",
                color: "#3d3225",
                marginBottom: "4px",
              }}
            >
              {t("home.selected.emptyTitle")}
            </div>
            <div style={{ color: "#8b7355", fontSize: "0.65rem" }}>
              {t("home.selected.emptyDetail")}
            </div>
          </div>
        )}

        <div className="compact-item" style={{ background: analysisMode.isDemo ? "rgba(255,248,240,0.9)" : analysisMode.mode === "partial_live" ? "rgba(255,248,235,0.92)" : "rgba(240,248,244,0.9)" }}>
          <div className="compact-label">{analysisBadgeLabel}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginBottom: "8px" }}>
            <span style={{ fontSize: "0.52rem", letterSpacing: "0.05em", textTransform: "uppercase", color: "#8b7355", background: "rgba(255,255,255,0.72)", border: "1px solid rgba(160,140,110,0.18)", borderRadius: "999px", padding: "2px 6px" }}>
              {freshnessLabel}
            </span>
            {timeRangeLabel && (
              <span style={{ fontSize: "0.52rem", letterSpacing: "0.05em", textTransform: "uppercase", color: "#8b7355", background: "rgba(255,255,255,0.72)", border: "1px solid rgba(160,140,110,0.18)", borderRadius: "999px", padding: "2px 6px" }}>
                {timeRangeLabel}
              </span>
            )}
          </div>
          <div
            style={{
              fontSize: "0.65rem",
              lineHeight: 1.5,
              color: (statusNote && (statusNote.includes("失败") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "#c0392b" : undefined,
              background: (statusNote && (statusNote.includes("失败") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "rgba(192, 57, 43, 0.08)" : undefined,
              borderLeft: (statusNote && (statusNote.includes("失败") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "2px solid #c0392b" : undefined,
              padding: (statusNote && (statusNote.includes("失败") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "2px 6px" : undefined,
            }}
          >
            {statusNote || (analysisMode.isDemo ? t("demo.banner") : t("status.liveAnalysis"))}
          </div>
          {analysisMode.loading && pipelineProgress && (
            <div className="retrieval-progress" style={{ marginTop: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", marginBottom: "8px" }}>
                <span style={{ fontSize: "0.52rem", color: "#4a7a9e", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  {locale === "en" ? "Retrieval trace" : "检索轨迹"}
                </span>
                <span style={{ fontSize: "0.52rem", color: "#8b7355" }}>
                  {pipelineProgress.stepIndex}/{pipelineProgress.totalSteps}
                </span>
              </div>
              <div style={{ display: "grid", gap: "4px" }}>
                {progressStageOrder.map((step, index) => {
                  const isActive = index === activeProgressIndex;
                  const isDone = index < activeProgressIndex;
                  return (
                    <div
                      key={step}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "0.55rem",
                        color: isActive ? "#3b6ea5" : isDone ? "#5a7a52" : "#8b7355",
                        opacity: isActive || isDone ? 1 : 0.58,
                      }}
                    >
                      <span
                        style={{
                          width: "7px",
                          height: "7px",
                          borderRadius: "999px",
                          background: isActive ? "#3b6ea5" : isDone ? "#5a7a52" : "rgba(160,140,110,0.28)",
                          boxShadow: isActive ? "0 0 0 4px rgba(59,110,165,0.12)" : undefined,
                          flex: "0 0 auto",
                        }}
                      />
                      <span>{progressStageLabel(step, locale)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {analysisMode.mode === "partial_live" && analysisMode.partialLiveReasons.length > 0 && (
            <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px dashed rgba(160,140,110,0.18)" }}>
              <div style={{ fontSize: "0.52rem", color: "#8b7355", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "4px" }}>
                {locale === "en" ? "Why partial live" : "部分 live 原因"}
              </div>
              {analysisMode.partialLiveReasons.slice(0, 3).map((reason, index) => (
                <div key={`${reason}-${index}`} style={{ fontSize: "0.58rem", color: "#6b5a42", lineHeight: 1.45, marginBottom: "3px" }}>
                  {locale === "en" ? "- " : "· "}{reason}
                </div>
              ))}
            </div>
          )}
        </div>

        {uncertaintyReport && !analysisMode.isDemo && (
          <div className="compact-item" style={{ background: "rgba(255,255,255,0.72)" }}>
            <div className="compact-label">{locale === "en" ? "Uncertainty report" : "不确定性报告"}</div>
            <div style={{ fontSize: "0.65rem", color: "#5c4a32", lineHeight: 1.5 }}>
              {Math.round(uncertaintyReport.overall_uncertainty * 100)}% · {uncertaintyReport.summary}
            </div>
            {uncertaintyReport.dominant_uncertainty_type && (
              <div style={{ fontSize: "0.56rem", color: "#8b7355", marginTop: "4px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {locale === "en" ? "Dominant" : "主导类型"}: {uncertaintyReport.dominant_uncertainty_type}
              </div>
            )}
          </div>
        )}

        {selectedApiEdges.length > 0 && (
          <div className="compact-item" style={{ background: "rgba(255,255,255,0.72)" }}>
            <div className="compact-label">{locale === "en" ? "Connected edges" : "关联边"}</div>
            {selectedApiEdges.slice(0, 3).map((edge) => (
              <button
                type="button"
                key={`${edge.id}-edge`}
                onClick={() => focusEdge(edge)}
                style={{
                  width: "100%",
                  marginBottom: "10px",
                  padding: "0 0 10px",
                  border: "0",
                  borderBottom: "1px dashed rgba(160,140,110,0.18)",
                  background: selectedFocusEdgeId === edge.id ? "rgba(59,110,165,0.08)" : "transparent",
                  borderRadius: "4px",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <div style={{ fontSize: "0.62rem", color: "#5c4a32", lineHeight: 1.4 }}>
                  <strong>{localizeCausalText(edge.source, locale)}</strong> → <strong>{localizeCausalText(edge.target, locale)}</strong>
                </div>
                <div style={{ fontSize: "0.56rem", color: edge.evidence_conflict && edge.evidence_conflict !== "none" ? "#a0503c" : "#8b7355", marginTop: "3px" }}>
                  {locale === "en" ? "Conflict" : "冲突"}: {edge.evidence_conflict ?? "none"}
                </div>
                {(edge.citation_spans?.[0]?.quoted_text) && (
                  <div style={{ fontSize: "0.58rem", color: "#6b5a42", marginTop: "6px", lineHeight: 1.5, fontStyle: "italic" }}>
                    “{edge.citation_spans[0].quoted_text}”
                  </div>
                )}
              </button>
            ))}
          </div>
        )}

        <div className="compact-item" style={{ background: "rgba(255,255,255,0.72)" }}>
          <div className="compact-label">{t("home.evidence.related")}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", marginBottom: "10px" }}>
            <select
              value={evidenceSourceFilter}
              onChange={(event) => setEvidenceSourceFilter(event.target.value)}
              style={{ fontSize: "0.56rem", padding: "4px 6px", borderRadius: "4px", border: "1px solid rgba(160,140,110,0.18)", background: "rgba(255,255,255,0.92)", color: "#5c4a32" }}
            >
              {sourceFilterOptions.map((source) => (
                <option key={source} value={source}>
                  {source === "all" ? (locale === "en" ? "All sources" : "全部来源") : source}
                </option>
              ))}
            </select>
            <select
              value={evidenceStanceFilter}
              onChange={(event) => setEvidenceStanceFilter(event.target.value as "all" | "supporting" | "refuting")}
              style={{ fontSize: "0.56rem", padding: "4px 6px", borderRadius: "4px", border: "1px solid rgba(160,140,110,0.18)", background: "rgba(255,255,255,0.92)", color: "#5c4a32" }}
            >
              <option value="all">{locale === "en" ? "All stance" : "全部立场"}</option>
              <option value="supporting">{locale === "en" ? "Supporting" : "支撑"}</option>
              <option value="refuting">{locale === "en" ? "Refuting" : "反驳"}</option>
            </select>
            <select
              value={evidenceConfidenceFilter}
              onChange={(event) => setEvidenceConfidenceFilter(event.target.value as "all" | "strong" | "medium" | "weak")}
              style={{ gridColumn: "1 / -1", fontSize: "0.56rem", padding: "4px 6px", borderRadius: "4px", border: "1px solid rgba(160,140,110,0.18)", background: "rgba(255,255,255,0.92)", color: "#5c4a32" }}
            >
              <option value="all">{locale === "en" ? "All confidence" : "全部可信度"}</option>
              <option value="strong">{t("home.evidence.strong")}</option>
              <option value="medium">{t("home.evidence.medium")}</option>
              <option value="weak">{t("home.evidence.weak")}</option>
            </select>
            <select
              value={evidenceQualityFilter}
              onChange={(event) =>
                setEvidenceQualityFilter(
                  event.target.value as
                    | "all"
                    | "trusted_fulltext"
                    | "fulltext"
                    | "store_cache"
                    | "fallback"
                    | "base"
                )
              }
              style={{ gridColumn: "1 / -1", fontSize: "0.56rem", padding: "4px 6px", borderRadius: "4px", border: "1px solid rgba(160,140,110,0.18)", background: "rgba(255,255,255,0.92)", color: "#5c4a32" }}
            >
              <option value="all">{locale === "en" ? "All evidence types" : "全部证据类型"}</option>
              <option value="trusted_fulltext">{locale === "en" ? "Trusted full text" : "可信正文"}</option>
              <option value="fulltext">{locale === "en" ? "Full text" : "正文"}</option>
              <option value="store_cache">{locale === "en" ? "Store cache" : "证据缓存"}</option>
              <option value="fallback">{locale === "en" ? "Fallback summary" : "降级摘要"}</option>
              <option value="base">{locale === "en" ? "Base / fresh sources" : "基础 / 实时来源"}</option>
            </select>
          </div>
          {hiddenEvidenceCount > 0 && evidenceQualityFilter === "all" && (
            <div style={{ marginBottom: "10px", padding: "8px", background: "rgba(255,248,240,0.72)", border: "1px dashed rgba(160,140,110,0.2)", borderRadius: "6px" }}>
              <div style={{ fontSize: "0.58rem", color: "#6b5a42", lineHeight: 1.45, marginBottom: "6px" }}>
                {locale === "en"
                  ? `${hiddenEvidenceCount} lower-priority evidence item(s) are hidden by default so stronger evidence appears first.`
                  : `默认已收起 ${hiddenEvidenceCount} 条低优先级证据，让更强的证据先展示。`}
              </div>
              <div style={{ fontSize: "0.54rem", color: "#8b7355", lineHeight: 1.45, marginBottom: "6px" }}>
                {[
                  hiddenEvidenceBreakdown.fallback > 0
                    ? evidenceCategorySummaryLabel("fallback", hiddenEvidenceBreakdown.fallback, locale)
                    : null,
                  hiddenEvidenceBreakdown.base > 0
                    ? evidenceCategorySummaryLabel("base", hiddenEvidenceBreakdown.base, locale)
                    : null,
                ]
                  .filter(Boolean)
                  .join(locale === "en" ? " · " : "，")}
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
                  ? (locale === "en" ? "Show prioritized only" : "只看高优先级证据")
                  : (locale === "en" ? "Show all evidence" : "显示全部证据")}
              </button>
            </div>
          )}
          {prioritizedEvidence.length > 0 ? (
            prioritizedEvidence.map((item) => (
              <button
                type="button"
                key={item.id}
                onClick={() => focusEvidence(item)}
                style={{
                  width: "100%",
                  marginBottom: "8px",
                  padding: "6px",
                  border: selectedEvidenceId === item.id
                    ? "1px solid rgba(59,110,165,0.28)"
                    : "1px solid transparent",
                  borderRadius: "6px",
                  background: selectedEvidenceId === item.id ? "rgba(59,110,165,0.08)" : "transparent",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px", fontSize: "0.56rem", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  <span style={{ color: item.is_supporting ? "#5a7a52" : "#a0503c" }}>
                    {item.is_supporting ? t("home.evidence.supporting") : t("home.evidence.refuting")}
                  </span>
                  <span style={{ color: "#8b7355" }}>{getReliabilityLabel(item.reliability)}</span>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "4px", marginBottom: "4px" }}>
                  <span style={{ fontSize: "0.5rem", color: "#8b7355", background: "rgba(255,255,255,0.72)", border: "1px solid rgba(160,140,110,0.18)", borderRadius: "999px", padding: "1px 6px", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    {formatEvidenceTierLabel(item, locale)}
                  </span>
                  {item.freshness && item.freshness !== "unknown" && (
                    <span style={{ fontSize: "0.5rem", color: "#8b7355", background: "rgba(255,255,255,0.72)", border: "1px solid rgba(160,140,110,0.18)", borderRadius: "999px", padding: "1px 6px", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {formatFreshnessLabel(item.freshness, locale)}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: "0.65rem", color: "#5c4a32", lineHeight: 1.45 }}>{item.content}</div>
                {selectedNodeCitationByEvidenceId.get(item.id)?.quoted_text && (
                  <div style={{ fontSize: "0.58rem", color: "#6b5a42", lineHeight: 1.45, marginTop: "4px", fontStyle: "italic" }}>
                    “{selectedNodeCitationByEvidenceId.get(item.id)?.quoted_text}”
                  </div>
                )}
                <div style={{ fontSize: "0.56rem", color: "#8b7355", marginTop: "2px" }}>
                  {item.source}
                  {item.timestamp ? ` · ${item.timestamp}` : ""}
                </div>
              </button>
            ))
          ) : (
            <div style={{ fontSize: "0.65rem", color: "#8b7355", lineHeight: 1.5 }}>{t("home.evidence.empty")}</div>
          )}
        </div>

        <h2 className="panel-title" style={{ marginTop: "16px" }}>
          {t("home.legend.title")}
        </h2>
        <div className="compact-item" style={{ padding: "6px 10px" }}>
          <div
            style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}
          >
            <span
              style={{
                width: "10px",
                height: "10px",
                background: "rgba(196, 69, 54, 0.4)",
                borderRadius: "2px",
              }}
            />
            <span style={{ fontSize: "0.6rem" }}>{t("graph.legend.cause")}</span>
          </div>
          <div
            style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}
          >
            <span
              style={{
                width: "10px",
                height: "10px",
                background: "rgba(70, 130, 180, 0.4)",
                borderRadius: "2px",
              }}
            />
            <span style={{ fontSize: "0.6rem" }}>{t("home.legend.effect")}</span>
          </div>
          <div
            style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}
          >
            <span
              style={{
                width: "10px",
                height: "10px",
                background: "rgba(180, 140, 80, 0.4)",
                borderRadius: "2px",
              }}
            />
            <span style={{ fontSize: "0.6rem" }}>{t("graph.legend.mediator")}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                width: "10px",
                height: "10px",
                background: "rgba(100, 140, 90, 0.4)",
                borderRadius: "2px",
              }}
            />
            <span style={{ fontSize: "0.6rem" }}>{t("panel.evidence")}</span>
          </div>
        </div>

        <div
          className="compact-item"
          style={{ marginTop: "16px", background: "rgba(255, 248, 240, 0.8)" }}
        >
          <div
            style={{
              fontSize: "0.6rem",
              color: "#8b7355",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "4px",
            }}
          >
            {t("home.actions.title")}
          </div>
          <div
            style={{
              fontSize: "0.65rem",
              color: "#5c4a32",
              lineHeight: 1.6,
            }}
          >
            • {t("home.actions.traceUpstream")}
            <br />• {t("home.actions.compareChains")}
            <br />• {t("home.actions.viewCounterfactuals")}
            <br />• {t("home.actions.dragNotes")}
          </div>
        </div>
      </aside>

      <div
        className="main-canvas"
        style={{
          position: "absolute",
          top: "52px",
          left: 0,
          right: 0,
          bottom: 0,
          overflow: "hidden",
          transform: `translate(${panOffset.x}px, ${panOffset.y}px)`,
          transition: isDragging ? "none" : "transform 0.1s ease-out",
        }}
      >
        <svg
          className="string-canvas"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            pointerEvents: "none",
            zIndex: 10,
          }}
        >
          <defs>
            <filter id="stringTexture">
              <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" result="noise" />
              <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.5" xChannelSelector="R" yChannelSelector="G" />
            </filter>
          </defs>
          {causalStrings.map((path, i) => (
            <g key={i} filter="url(#stringTexture)">
              <path
                pathLength={1}
                d={path.d}
                stroke="#8a1a10"
                strokeWidth={path.width * 0.5}
                fill="none"
                strokeLinecap="round"
                opacity={selectedEdgeIds.size === 0 ? path.opacity * 0.25 : selectedEdgeIds.has(path.id) ? path.opacity * 0.35 : 0.08}
                style={{ animation: boardReady ? `drawString 0.8s ease-out ${i * 0.08}s both` : undefined }}
              />
              <path
                pathLength={1}
                d={path.d}
                stroke={selectedEdgeIds.size === 0 || selectedEdgeIds.has(path.id) ? "#c44536" : "#bfa59b"}
                strokeWidth={selectedEdgeIds.size === 0 ? path.width : selectedEdgeIds.has(path.id) ? path.width * 1.35 : path.width * 0.8}
                fill="none"
                strokeLinecap="round"
                opacity={selectedEdgeIds.size === 0 ? path.opacity : selectedEdgeIds.has(path.id) ? Math.min(0.95, path.opacity + 0.2) : 0.14}
                style={{ animation: boardReady ? `drawString 0.8s ease-out ${i * 0.08}s both` : undefined }}
              />
              <path
                pathLength={1}
                d={path.d}
                stroke="#e87060"
                strokeWidth={path.width * 0.3}
                fill="none"
                strokeLinecap="round"
                opacity={selectedEdgeIds.size === 0 ? path.opacity * 0.2 : selectedEdgeIds.has(path.id) ? path.opacity * 0.32 : 0.06}
                style={{ animation: boardReady ? `drawString 0.8s ease-out ${i * 0.08}s both` : undefined }}
              />
            </g>
          ))}
        </svg>

        <div
          style={{
            position: "absolute",
            left: "50%",
            bottom: 18,
            transform: "translateX(-50%)",
            padding: "6px 12px",
            borderRadius: 999,
            background: "rgba(250, 246, 238, 0.78)",
            border: "1px solid rgba(160, 140, 110, 0.18)",
            color: "#7a6b55",
            fontSize: "0.62rem",
            letterSpacing: "0.04em",
            zIndex: 14,
            backdropFilter: "blur(6px)",
          }}
        >
          {t("home.canvasHint")}
        </div>

        {notes.map((note) => (
          <StickyCard
            key={note.id}
            note={note}
            isSelected={selectedNodeId === note.id || connectedNodeIds.has(note.id)}
            isDragging={draggingNoteId === note.id}
            depthLabel={t("graph.depth")}
            onClick={() => handleNodeClick(note.id)}
            onMouseDown={(event) => handleNoteMouseDown(note, event)}
          />
        ))}
      </div>

      <style jsx global>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        @keyframes noteIn {
          0% { opacity: 0; transform: translateY(14px) scale(0.96); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes drawString {
          0% { stroke-dasharray: 1; stroke-dashoffset: 1; }
          100% { stroke-dasharray: 1; stroke-dashoffset: 0; }
        }

        .red-string {
          stroke: #c44536;
          stroke-width: 2.5px;
          fill: none;
          stroke-linecap: round;
          opacity: 0.7;
        }

        .sticky-card {
          position: absolute;
          padding: 22px 14px 14px;
          border-radius: 2px;
          box-shadow:
            0 1px 2px rgba(80, 60, 40, 0.08),
            0 3px 6px rgba(80, 60, 40, 0.12),
            0 8px 20px rgba(80, 60, 40, 0.1),
            4px 4px 0px rgba(60, 40, 20, 0.04),
            inset 0 1px 0 rgba(255, 255, 255, 0.6),
            inset -1px -1px 0 rgba(0, 0, 0, 0.03);
          transform-origin: center top;
          animation: noteIn 0.42s ease-out both;
        }

        .sticky-card:hover {
          box-shadow:
            0 2px 4px rgba(80, 60, 40, 0.12),
            0 8px 18px rgba(80, 60, 40, 0.18),
            0 16px 32px rgba(80, 60, 40, 0.12),
            6px 6px 0px rgba(60, 40, 20, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.65),
            inset -1px -1px 0 rgba(0, 0, 0, 0.04);
        }

        .sticky-card:active {
          box-shadow:
            0 2px 4px rgba(80, 60, 40, 0.1),
            0 4px 10px rgba(80, 60, 40, 0.12),
            0 8px 18px rgba(80, 60, 40, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.55);
        }

        .sticky-card::after {
          content: '';
          position: absolute;
          right: 0;
          bottom: 0;
          width: 22px;
          height: 22px;
          background: linear-gradient(135deg, rgba(120, 100, 70, 0.14) 0%, rgba(255, 255, 255, 0.15) 55%, transparent 56%);
          clip-path: polygon(100% 0, 0 100%, 100% 100%);
          opacity: 0.85;
          pointer-events: none;
        }

        .paper-texture::before {
          content: '';
          position: absolute;
          inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 160 120' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
          opacity: 0.045;
          pointer-events: none;
          border-radius: inherit;
          mix-blend-mode: multiply;
        }

        .tape-strip {
          position: absolute;
          top: 4px;
          width: 32px;
          height: 10px;
          background: linear-gradient(
            135deg,
            rgba(240, 228, 200, 0.75) 0%,
            rgba(225, 210, 180, 0.65) 40%,
            rgba(210, 195, 165, 0.55) 100%
          );
          box-shadow: 0 1px 2px rgba(80, 60, 40, 0.12);
          z-index: 5;
        }

        .tape-left {
          left: 12px;
          transform: rotate(-4deg);
        }

        .tape-right {
          right: 12px;
          transform: rotate(3deg);
        }

        .card-title {
          font-family: var(--font-caveat), Caveat, cursive;
          font-size: 1.22rem;
          color: #3d3225;
          margin-bottom: 4px;
          line-height: 1.15;
          font-weight: 600;
          text-shadow: 0 1px 0 rgba(255, 255, 255, 0.3);
        }

        .card-subtitle {
          font-size: 0.6rem;
          color: #7a6b55;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          margin-bottom: 8px;
        }

        .card-detail {
          font-size: 0.68rem;
          color: #5c4a32;
          line-height: 1.5;
        }

        .card-tag {
          display: inline-block;
          padding: 2px 7px;
          border-radius: 2px;
          font-size: 0.55rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          margin-top: 6px;
        }

        .sticky-yellow {
          background: linear-gradient(145deg, #fef9e7 0%, #f9e8c8 60%, #f0d8b0 100%);
          border-bottom: 3px solid rgba(180, 160, 120, 0.35);
        }

        .sticky-cream {
          background: linear-gradient(145deg, #fefcf5 0%, #f5edd8 60%, #ede0c8 100%);
          border-bottom: 3px solid rgba(170, 150, 110, 0.35);
        }

        .sticky-pink {
          background: linear-gradient(145deg, #fef0f3 0%, #f8dce4 60%, #f0c8d8 100%);
          border-bottom: 3px solid rgba(200, 150, 170, 0.35);
        }

        .sticky-blue {
          background: linear-gradient(145deg, #eef5fa 0%, #dce8f2 60%, #c8d8e8 100%);
          border-bottom: 3px solid rgba(140, 170, 200, 0.35);
        }

        .sticky-mint {
          background: linear-gradient(145deg, #eef8f3 0%, #d8efe2 60%, #c0e0d0 100%);
          border-bottom: 3px solid rgba(140, 190, 160, 0.35);
        }

        .sticky-lavender {
          background: linear-gradient(145deg, #f3f0f8 0%, #e4dff0 60%, #d4cce0 100%);
          border-bottom: 3px solid rgba(170, 150, 200, 0.35);
        }

        .tag-cause { background: rgba(196, 69, 54, 0.15); color: #943d30; }
        .tag-effect { background: rgba(70, 130, 180, 0.15); color: #4a7a9e; }
        .tag-evidence { background: rgba(100, 140, 90, 0.15); color: #5a7a52; }
        .tag-mediator { background: rgba(180, 140, 80, 0.15); color: #8a6a40; }
        .tag-factor { background: rgba(140, 100, 160, 0.15); color: #6a5080; }

        .compact-item {
          padding: 8px 10px;
          background: rgba(255, 255, 255, 0.5);
          border: 1px solid rgba(160, 140, 110, 0.1);
          border-radius: 4px;
          margin-bottom: 8px;
          font-size: 0.65rem;
          color: #5c4a32;
          line-height: 1.4;
        }

        .compact-item:hover {
          background: rgba(255, 255, 255, 0.8);
          border-color: rgba(180, 80, 60, 0.2);
        }

        .compact-label {
          font-size: 0.55rem;
          color: #8b7355;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 3px;
        }

        .panel-title {
          font-family: var(--font-caveat), Caveat, cursive;
          color: #6b5a42;
          font-size: 1rem;
          font-weight: 500;
          letter-spacing: 0.05em;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(160, 140, 110, 0.15);
        }

        ::-webkit-scrollbar {
          width: 4px;
        }

        ::-webkit-scrollbar-track {
          background: transparent;
        }

        ::-webkit-scrollbar-thumb {
          background: rgba(160, 140, 110, 0.2);
          border-radius: 2px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: rgba(160, 140, 110, 0.4);
        }
      `}</style>
    </div>
  );
}
