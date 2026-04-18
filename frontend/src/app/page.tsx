"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useI18n, type TranslationKey } from "@/lib/i18n";
import {
  getLocalizedMockData,
  type CausalChain,
  type ChainNode,
  type CausalNodeType,
  type EdgeStrength,
  type EvidenceReliability,
} from "@/data/mockData";
import type {
  AnalysisUiState,
  AnalyzeResponseV2,
  ApiAnalysisBrief,
  ApiChallengeCheck,
  ApiChain,
  ApiEdge,
  ApiEvidence,
  ApiProductionBrief,
  ApiProductionHarness,
  ApiProductHarness,
  ApiProviderPreflight,
  ApiRetrievalTrace,
  ApiRunStep,
  ApiSavedRunSummary,
  ApiScenario,
  ApiUsageLedgerItem,
} from "@/lib/api-types";
import {
  evidenceQualityCategory,
  evidenceSortWeight,
  formatAnalysisBadge,
  formatFreshnessLabel,
  formatRefutationStatusLabel,
  formatTimeRangeLabel,
} from "@/lib/evidence-formatting";
import {
  formatSourceKindLabel,
  isDegradedSourceTrace,
  sourceTraceStatus,
} from "@/lib/source-trace";
import { SourceProgressPanel } from "@/lib/source-progress-panel";
import { SourceTracePanel } from "@/lib/source-trace-panel";
import { ReadableBriefPanel } from "@/lib/readable-brief-panel";
import { ProductionBriefPanel } from "@/lib/production-brief-panel";
import { SavedRunsPanel } from "@/lib/saved-runs-panel";
import { UploadedEvidencePanel } from "@/lib/uploaded-evidence-panel";
import { ChallengeCoveragePanel } from "@/lib/challenge-coverage-panel";
import {
  EvidenceFilterPanel,
  type EvidenceConfidenceFilter,
  type EvidenceQualityFilter,
  type EvidenceStanceFilter,
} from "@/lib/evidence-filter-panel";
import { StickyCard } from "@/lib/sticky-card";
import {
  CANVAS_HEADER_HEIGHT,
  NOTE_BOTTOM_SAFE_PX,
  NOTE_TOP_SAFE_PX,
  NOTE_VISUAL_HEIGHT_BUFFER,
  PANEL_SAFE_CLOSED,
  PANEL_SAFE_LEFT_OPEN,
  PANEL_SAFE_RIGHT_OPEN,
  computeCausalStrings,
  computeLayout,
  type StickyNote,
} from "@/lib/sticky-graph-layout";

const API_BASE = process.env.NEXT_PUBLIC_RETROCAUSE_API_BASE ?? "http://localhost:8000";

function localizeBriefText(text: string, locale: "zh" | "en"): string {
  if (locale === "en") return text;
  return localizeCausalText(text, locale)
    .replace(/Most likely explanation:/gi, "\u6700\u53ef\u80fd\u89e3\u91ca\uff1a")
    .replace(/confidence signal/gi, "缃俊淇″彿")
    .replace(/Found/gi, "鍙戠幇")
    .replace(/challenge evidence item\(s\)/gi, "\u6761\u53cd\u8bc1\u8bc1\u636e")
    .replace(/Checked/gi, "\u5df2\u68c0\u67e5")
    .replace(/key edge\(s\)/gi, "鏉″叧閿洜鏋滆竟")
    .replace(/source type\(s\)/gi, "\u7c7b\u6765\u6e90")
    .replace(/high-quality evidence item\(s\)/gi, "鏉￠珮璐ㄩ噺璇佹嵁")
    .replace(/total evidence item\(s\)/gi, "\u6761\u603b\u8bc1\u636e");
}

function localizeEvidenceContent(content: string, locale: "zh" | "en"): string {
  if (locale === "en") return content;
  return localizeCausalText(content, locale);
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
        : `\u5206\u6790\u5931\u8d25\uff08${payload.error}\uff09\uff0c\u5f53\u524d\u663e\u793a demo \u56de\u9000\u7ed3\u679c\u3002`;
    }
    return locale === "en"
      ? "Backend returned demo fallback data. Treat this as a structured example, not validated analysis."
      : "\u540e\u7aef\u8fd4\u56de\u4e86 demo fallback \u6570\u636e\u3002\u8bf7\u5c06\u5176\u89c6\u4e3a\u7ed3\u6784\u5316\u793a\u4f8b\uff0c\u800c\u975e\u5df2\u9a8c\u8bc1\u5206\u6790\u3002";
  }

  if (payload.analysis_mode === "partial_live") {
    const detail = firstAction
      ? locale === "en"
        ? ` Next best action: ${firstAction}`
        : ` \u5efa\u8bae\u4f18\u5148\u52a8\u4f5c\uff1a${firstAction}`
      : "";
    const errorDetail = payload.error
      ? locale === "en"
        ? ` Error: ${payload.error}`
        : ` \u9519\u8bef\uff1a${payload.error}`
      : "";
    if (timeLabel) {
      return locale === "en"
        ? `Partial live analysis for ${timeLabel}. ${freshnessLabel}.${detail}${errorDetail}`
        : `\u8fd9\u662f\u9488\u5bf9${timeLabel}\u7684\u90e8\u5206 live \u5206\u6790\u3002${freshnessLabel}\u3002${detail}${errorDetail}`;
    }
    return locale === "en"
      ? `Partial live analysis returned. ${freshnessLabel}.${detail}${errorDetail}`
      : `\u5f53\u524d\u8fd4\u56de\u7684\u662f\u90e8\u5206 live \u5206\u6790\u3002${freshnessLabel}\u3002${detail}${errorDetail}`;
  }

  if (timeLabel) {
    return locale === "en"
      ? `Live analysis returned for ${timeLabel}. ${freshnessLabel}. Review evidence coverage before trusting it.`
      : `\u5df2\u8fd4\u56de\u9488\u5bf9${timeLabel}\u7684 live \u5206\u6790\u3002${freshnessLabel}\u3002\u8bf7\u5148\u68c0\u67e5\u8bc1\u636e\u8986\u76d6\uff0c\u518d\u51b3\u5b9a\u662f\u5426\u4fe1\u4efb\u7ed3\u679c\u3002`;
  }

  return locale === "en"
    ? `Live analysis returned. ${freshnessLabel}. Review evidence coverage before trusting it.`
    : `\u5df2\u8fd4\u56de live \u5206\u6790\u3002${freshnessLabel}\u3002\u8bf7\u5148\u68c0\u67e5\u8bc1\u636e\u8986\u76d6\uff0c\u518d\u51b3\u5b9a\u662f\u5426\u4fe1\u4efb\u7ed3\u679c\u3002`;
}

const ZH_CAUSAL_LABELS: Array<[RegExp, string]> = [
  [/evidence-wide causal map/gi, "\u8bc1\u636e\u5168\u56fe"],
  [/supported dag context/gi, "\u8bc1\u636e\u652f\u6491\u7684 DAG \u4e0a\u4e0b\u6587"],
  [/single root-to-outcome path/gi, "\u5355\u6761\u6839\u56e0\u5230\u7ed3\u679c\u8def\u5f84"],
  [/deal reached|agreement/gi, "\u8fbe\u6210\u534f\u8bae"],
  [/ceasefire/gi, "\u505c\u706b"],
  [/bitcoin|btc/gi, "\u6bd4\u7279\u5e01"],
  [/cryptocurrenc(?:y|ies)|crypto assets?|crypto/gi, "\u52a0\u5bc6\u8d27\u5e01"],
  [/price drop|price decline|sell-?off|market drop|crash/gi, "\u4ef7\u683c\u4e0b\u8dcc"],
  [/spot etfs?|etf flows?|exchange-traded funds?/gi, "\u73b0\u8d27 ETF \u8d44\u91d1\u6d41"],
  [/liquidations?|leveraged liquidations?/gi, "\u6760\u6746\u6e05\u7b97"],
  [/risk sentiment|risk appetite|market sentiment|sentiment/gi, "\u98ce\u9669\u60c5\u7eea"],
  [/political uncertainty/gi, "\u653f\u6cbb\u4e0d\u786e\u5b9a\u6027"],
  [/investors?/gi, "\u6295\u8d44\u8005"],
  [/digital currencies/gi, "\u6570\u5b57\u8d27\u5e01"],
  [/gold/gi, "\u9ec4\u91d1"],
  [/silver/gi, "\u767d\u94f6"],
  [/macro(?:economic)? pressure|macro factors?|interest rates?|rate expectations/gi, "\u5b8f\u89c2\u538b\u529b"],
  [/dollar strength|u\.s\. dollar/gi, "\u7f8e\u5143\u8d70\u5f3a"],
  [/profit taking/gi, "\u83b7\u5229\u4e86\u7ed3"],
  [/regulatory concerns?|regulatory pressure|regulation|regulating/gi, "\u76d1\u7ba1\u538b\u529b"],
  [/government discussions?|policy discussions?|talks?/gi, "\u653f\u7b56\u8ba8\u8bba"],
  [/government|administration/gi, "\u653f\u5e9c"],
  [/trump administration|trump/gi, "\u7279\u6717\u666e\u653f\u5e9c"],
  [/expectations?/gi, "\u9884\u671f"],
  [/favorable|friendly/gi, "\u5229\u597d"],
  [/lack of progress|stalled/gi, "\u8fdb\u5c55\u4e0d\u8db3"],
  [/bill in congress|congress(?:ional)? bill|congress|bill/gi, "\u56fd\u4f1a\u6cd5\u6848"],
  [/institutional flows?|fund flows?|capital flows?/gi, "\u8d44\u91d1\u6d41\u5411"],
  [/institutional selling|selling/gi, "\u673a\u6784\u5356\u51fa"],
  [/large financial institutions?|financial institutions?/gi, "\u91d1\u878d\u673a\u6784"],
  [/market volatility|volatility/gi, "\u5e02\u573a\u6ce2\u52a8"],
  [/trading volume|volume/gi, "\u6210\u4ea4\u91cf"],
  [/mining difficulty|hashrate|hash rate/gi, "\u6316\u77ff\u96be\u5ea6\u4e0e\u7b97\u529b"],
  [/on-chain activity|onchain activity/gi, "\u94fe\u4e0a\u6d3b\u52a8"],
  [/exchange inflows?|exchange outflows?/gi, "\u4ea4\u6613\u6240\u8d44\u91d1\u6d41"],
  [/whale activity|large holders?/gi, "\u5927\u6237\u6d3b\u52a8"],
  [/futures open interest|open interest/gi, "\u671f\u8d27\u672a\u5e73\u4ed3\u5408\u7ea6"],
  [/funding rates?/gi, "\u8d44\u91d1\u8d39\u7387"],
  [/bureau of industry and security|bis/gi, "\u7f8e\u56fd\u5de5\u4e1a\u4e0e\u5b89\u5168\u5c40"],
  [/\b(?:export administration regulations|ear)\b/gi, "\u51fa\u53e3\u7ba1\u7406\u6761\u4f8b"],
  [/export controls?|export restrictions?/gi, "\u51fa\u53e3\u7ba1\u5236"],
  [/semiconductor manufacturing items?/gi, "\u534a\u5bfc\u4f53\u5236\u9020\u9879\u76ee"],
  [/semiconductor chips?|semiconductors?/gi, "\u534a\u5bfc\u4f53\u82af\u7247"],
  [/advanced computing integrated circuits?|advanced computing items?/gi, "\u5148\u8fdb\u8ba1\u7b97\u82af\u7247"],
  [/national security concerns?/gi, "\u56fd\u5bb6\u5b89\u5168\u62c5\u5fe7"],
  [/military modernization/gi, "\u519b\u4e8b\u73b0\u4ee3\u5316"],
  [/china'?s access/gi, "\u4e2d\u56fd\u83b7\u53d6\u80fd\u529b"],
  [/critical technolog(?:y|ies)/gi, "\u5173\u952e\u6280\u672f"],
  [/supply chains?/gi, "\u4f9b\u5e94\u94fe"],
  [/policy rationale/gi, "\u653f\u7b56\u7406\u7531"],
  [/commerce department/gi, "\u7f8e\u56fd\u5546\u52a1\u90e8"],
  [/official statements?/gi, "\u5b98\u65b9\u58f0\u660e"],
  [/taiwan/gi, "\u53f0\u6e7e"],
  [/huawei/gi, "\u534e\u4e3a"],
  [/smic/gi, "\u4e2d\u82af\u56fd\u9645"],
  [/nexperia/gi, "\u5b89\u4e16\u534a\u5bfc\u4f53"],
  [/u\.s\./gi, "\u7f8e\u56fd"],
  [/china/gi, "\u4e2d\u56fd"],
];

function localizeCausalText(text: string, locale: "zh" | "en"): string {
  if (locale === "en") return text;

  let localized = text.replaceAll("_", " ");
  for (const [pattern, replacement] of ZH_CAUSAL_LABELS) {
    localized = localized.replace(pattern, replacement);
  }

  return localized
    .replace(/\bcontrols\b/gi, "\u7ba1\u5236")
    .replace(/\brestrictions\b/gi, "\u9650\u5236")
    .replace(/\brules\b/gi, "\u89c4\u5219")
    .replace(/\bpolicy\b/gi, "\u653f\u7b56")
    .replace(/\breasons\b/gi, "\u539f\u56e0")
    .replace(/\bmarket\b/gi, "\u5e02\u573a")
    .replace(/\bprice\b/gi, "\u4ef7\u683c")
    .replace(/\bdrop\b/gi, "\u4e0b\u8dcc")
    .replace(/\btoday\b/gi, "\u4eca\u65e5")
    .replace(/\bspeed\b/gi, "\u901f\u5ea6")
    .replace(/\bfactors?\b/gi, "\u56e0\u7d20")
    .replace(/\bcauses?\b/gi, "\u539f\u56e0")
    .replace(/\bin\b/gi, "\u5728")
    .replace(/\s+/g, " ")
    .trim();
}

function hasUnlocalizedEnglish(text: string): boolean {
  const tokens = text.match(/[A-Za-z]{4,}/g) ?? [];
  return tokens.length > 2;
}

function localizeCausalLabel(text: string, locale: "zh" | "en"): string {
  const localized = localizeCausalText(text, locale);
  return localized;
}

function localizeCausalDescription(text: string, label: string, locale: "zh" | "en"): string {
  const localized = localizeCausalText(text, locale);
  if (locale === "zh" && hasUnlocalizedEnglish(localized)) {
    return `\u4e0e${label}\u76f8\u5173\u7684\u8bc1\u636e\u652f\u6491\u56e0\u7d20`;
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
        intervention: locale === "en" ? "Counterfactual details remain limited in the OSS evidence board" : "\u5f53\u524d OSS \u8bc1\u636e\u5899\u4e2d\u7684\u53cd\u4e8b\u5b9e\u8be6\u60c5\u4ecd\u7136\u6709\u9650",
        outcomeChange: locale === "en" ? "Detailed counterfactual summary not yet rendered on homepage" : "\u9996\u9875\u6682\u672a\u5b8c\u6574\u6e32\u67d3\u53cd\u4e8b\u5b9e\u6458\u8981",
        probabilityShift: 0,
        description: locale === "en" ? "This homepage currently renders the selected causal chain and labels whether the result is live or demo." : "\u5f53\u524d\u9996\u9875\u4f1a\u6e32\u67d3\u6240\u9009\u56e0\u679c\u94fe\uff0c\u5e76\u6807\u6ce8\u7ed3\u679c\u6765\u81ea real analysis \u8fd8\u662f demo\u3002",
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
      title: locale === "en" ? "No causal chain available" : "\u6682\u65e0\u53ef\u5c55\u793a\u7684\u56e0\u679c\u94fe",
      outcomeLabel: query,
      totalNodes: 0,
      totalEdges: 0,
      maxDepth: 0,
      confidence: 0,
      primaryEvidenceCount: 0,
      counterfactualSummary: {
        intervention:
          locale === "en" ? "No counterfactual summary available" : "\u6682\u65e0\u53cd\u4e8b\u5b9e\u6458\u8981",
        outcomeChange:
          locale === "en" ? "Live analysis did not produce a usable chain" : "\u672c\u6b21 live \u5206\u6790\u672a\u4ea7\u51fa\u53ef\u7528\u94fe\u8def",
        probabilityShift: 0,
        description:
          locale === "en"
            ? "Inspect the status note and error details before retrying."
            : "\u8bf7\u5148\u67e5\u770b\u72b6\u6001\u8bf4\u660e\u548c\u9519\u8bef\u4fe1\u606f\uff0c\u518d\u51b3\u5b9a\u662f\u5426\u91cd\u8bd5\u3002",
      },
    },
    nodes: [],
    edges: [],
    upstreamMap: {},
  };
}

interface DragState {
  id: string;
  pointerX: number;
  pointerY: number;
  left: number;
  top: number;
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
  const selectedModel = "openrouter";
  const [selectedExplicitModel, setSelectedExplicitModel] = useState("");
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [availableModels, setAvailableModels] = useState<Record<string, string>>({});
  const [statusNote, setStatusNote] = useState("");
  const [availableChains, setAvailableChains] = useState<AnalyzeResponseV2["chains"]>([]);
  const [recommendedChainId, setRecommendedChainId] = useState<string | null>(null);
  const [selectedChainId, setSelectedChainId] = useState<string | null>(null);
  const [evidencePool, setEvidencePool] = useState<AnalyzeResponseV2["evidences"]>([]);
  const [retrievalTrace, setRetrievalTrace] = useState<ApiRetrievalTrace[]>([]);
  const [challengeChecks, setChallengeChecks] = useState<ApiChallengeCheck[]>([]);
  const [analysisBrief, setAnalysisBrief] = useState<ApiAnalysisBrief | null>(null);
  const [markdownBrief, setMarkdownBrief] = useState<string | null>(null);
  const [markdownCopyStatus, setMarkdownCopyStatus] = useState<"idle" | "copied" | "failed">("idle");
  const [showManualCopyReport, setShowManualCopyReport] = useState(false);
  const [productHarness, setProductHarness] = useState<ApiProductHarness | null>(null);
  const [scenarioOverride, setScenarioOverride] = useState("auto");
  const [scenario, setScenario] = useState<ApiScenario | null>(null);
  const [productionBrief, setProductionBrief] = useState<ApiProductionBrief | null>(null);
  const [productionHarness, setProductionHarness] = useState<ApiProductionHarness | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState("demo");
  const [runSteps, setRunSteps] = useState<ApiRunStep[]>([]);
  const [usageLedger, setUsageLedger] = useState<ApiUsageLedgerItem[]>([]);
  const [savedRuns, setSavedRuns] = useState<ApiSavedRunSummary[]>([]);
  const [savedRunsStatus, setSavedRunsStatus] = useState("");
  const [uploadedEvidenceTitle, setUploadedEvidenceTitle] = useState("");
  const [uploadedEvidenceText, setUploadedEvidenceText] = useState("");
  const [uploadedEvidenceStatus, setUploadedEvidenceStatus] = useState("");
  const [providerPreflight, setProviderPreflight] = useState<ApiProviderPreflight | null>(null);
  const [providerPreflightLoading, setProviderPreflightLoading] = useState(false);
  const [pipelineEval, setPipelineEval] = useState<AnalyzeResponseV2["evaluation"]>(null);
  const [uncertaintyReport, setUncertaintyReport] = useState<AnalyzeResponseV2["uncertainty_report"]>(null);
  const [evidenceSourceFilter, setEvidenceSourceFilter] = useState<string>("all");
  const [evidenceStanceFilter, setEvidenceStanceFilter] = useState<EvidenceStanceFilter>("all");
  const [evidenceConfidenceFilter, setEvidenceConfidenceFilter] =
    useState<EvidenceConfidenceFilter>("all");
  const [evidenceQualityFilter, setEvidenceQualityFilter] =
    useState<EvidenceQualityFilter>("all");
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
  const manualCopyReportRef = useRef<HTMLTextAreaElement>(null);

  const mockPrimaryChain = activeChain;
  
  // Board drag/pan state
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [draggingNoteId, setDraggingNoteId] = useState<string | null>(null);
  const boardRef = useRef<HTMLDivElement>(null);
  const noteDragRef = useRef<DragState | null>(null);

  // SSR-safe: compute layout only on client via useEffect
  const [notes, setNotes] = useState<StickyNote[]>([]);
  const [boardReady, setBoardReady] = useState(false);

  useEffect(() => {
    if (availableChains.length > 0) {
      const targetChainId = selectedChainId ?? recommendedChainId;
      const currentApiChain =
        availableChains.find((chain) => chain.chain_id === targetChainId) ??
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
    analysisMode.isDemo,
    analysisMode.loading,
    availableChains,
    currentQuery,
    evidencePool,
    lastQuery,
    locale,
    localizedDemo.primaryChain,
    recommendedChainId,
    selectedChainId,
  ]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/providers`)
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
    const headerHeight = CANVAS_HEADER_HEIGHT;

    const computedNotes = computeLayout(
      mockPrimaryChain.nodes,
      width,
      height,
      headerHeight,
      (type) => getTagLabel(type, t),
      leftPanelOpen,
      rightPanelOpen
    );

    setNotes(computedNotes);
    setBoardReady(true);
  }, [mockPrimaryChain, locale, t, leftPanelOpen, rightPanelOpen]);

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
  const activeChainId = mockPrimaryChain.metadata.id;
  const activeChainIsRecommended = !recommendedChainId || activeChainId === recommendedChainId;
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
        refutationStatus: chain.refutation_status,
        edgeCount: chain.edges.length,
        nodeCount: chain.nodes.length,
      })),
    [availableChains, locale]
  );
  const causalReasonSummaries = useMemo(() => {
    const chainEdges = activeApiChain?.edges ?? [];
    return chainEdges.slice(0, 4).map((edge) => {
      const evidenceIds = [...edge.supporting_evidence_ids, ...edge.refuting_evidence_ids];
      const firstEvidence = evidencePool.find((item) => evidenceIds.includes(item.id));
      return {
        id: edge.id,
        source: localizeCausalText(edge.source, locale),
        target: localizeCausalText(edge.target, locale),
        evidenceCount: evidenceIds.length,
        evidenceSource: firstEvidence?.source ?? "",
        evidenceExcerpt: firstEvidence ? localizeEvidenceContent(firstEvidence.content, locale) : "",
        refutationStatus: edge.refutation_status,
        strength: Math.round(edge.strength * 100),
      };
    });
  }, [activeApiChain, evidencePool, locale]);
  const localizedAnalysisBrief = useMemo(() => {
    if (!analysisBrief) return null;
    return {
      answer: localizeBriefText(analysisBrief.answer, locale),
      confidence: Math.round(analysisBrief.confidence * 100),
      topReasons: analysisBrief.top_reasons.map((item) => localizeBriefText(item, locale)),
      challengeSummary: localizeBriefText(analysisBrief.challenge_summary, locale),
      missingEvidence: analysisBrief.missing_evidence.map((item) =>
        localizeBriefText(item, locale)
      ),
      sourceCoverage: localizeBriefText(analysisBrief.source_coverage, locale),
    };
  }, [analysisBrief, locale]);
  const localizedMarkdownBrief = useMemo(() => {
    if (!markdownBrief) return null;
    return locale === "en" ? markdownBrief : localizeBriefText(markdownBrief, locale);
  }, [locale, markdownBrief]);
  const challengeCheckSummary = useMemo(() => {
    const checked = challengeChecks.length;
    const refuting = challengeChecks.reduce((sum, item) => sum + item.refuting_count, 0);
    const contextOnly = challengeChecks.filter((item) => item.status === "checked_context_only").length;
    return { checked, refuting, contextOnly };
  }, [challengeChecks]);
  const analysisBadgeLabel = formatAnalysisBadge(analysisMode.mode, locale);
  const freshnessLabel = formatFreshnessLabel(analysisMode.freshnessStatus, locale);
  const timeRangeLabel = formatTimeRangeLabel(analysisMode.timeRange, locale);
  const sourceHitCount = retrievalTrace.reduce((sum, item) => sum + Math.max(0, item.result_count), 0);
  const traceFailureCount = retrievalTrace.filter((item) => isDegradedSourceTrace(item)).length;
  const sourceTransparencySummary = useMemo(() => {
    const uniqueLabels = Array.from(
      new Set(
        retrievalTrace.map((item) =>
          item.source_label || item.source || formatSourceKindLabel(item.source_kind, locale)
        )
      )
    ).filter(Boolean);
    const stableCount = retrievalTrace.filter((item) => item.stability === "high").length;
    const cachedCount = retrievalTrace.filter((item) => sourceTraceStatus(item) === "cached").length;
    const degradedCount = retrievalTrace.filter((item) => isDegradedSourceTrace(item)).length;
    const successfulCount = retrievalTrace.filter(
      (item) => !isDegradedSourceTrace(item) && item.result_count > 0
    ).length;
    return {
      labels: uniqueLabels.slice(0, 3),
      checked: retrievalTrace.length,
      stable: stableCount,
      successful: successfulCount,
      cached: cachedCount,
      failed: degradedCount,
      hits: sourceHitCount,
      reviewability:
        degradedCount === 0
          ? locale === "en"
            ? "Reviewable"
            : "\u53ef\u5ba1\u9605"
          : locale === "en"
            ? "Needs source attention"
            : "\u9700\u68c0\u67e5\u6765\u6e90",
    };
  }, [locale, retrievalTrace, sourceHitCount]);
  const evidenceCoverageScore = Math.min(
    100,
    Math.round(
      (mockPrimaryChain.metadata.primaryEvidenceCount /
        Math.max(1, mockPrimaryChain.metadata.totalEdges)) *
        100
    )
  );
  const qualityGateTone =
    analysisMode.mode === "live" && evidenceCoverageScore >= 75
      ? "strong"
      : analysisMode.mode === "partial_live" || hasLowEvidenceCoverage || traceFailureCount > 0
        ? "caution"
        : "steady";

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

  const changeZoom = useCallback((delta: number) => {
    setZoomLevel((current) => Math.min(1.5, Math.max(0.7, Number((current + delta).toFixed(2)))));
  }, []);

  const resetViewport = useCallback(() => {
    setPanOffset({ x: 0, y: 0 });
    setZoomLevel(1);
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

      const nextLeft = drag.left + (event.clientX - drag.pointerX) / zoomLevel;
      const nextTop = drag.top + (event.clientY - drag.pointerY) / zoomLevel;

      setNotes((currentNotes) =>
        currentNotes.map((note) => {
          if (note.id !== drag.id) {
            return note;
          }
          const leftBound = leftPanelOpen ? PANEL_SAFE_LEFT_OPEN : PANEL_SAFE_CLOSED;
          const rightBound = rightPanelOpen ? PANEL_SAFE_RIGHT_OPEN : PANEL_SAFE_CLOSED;
          const topBound = NOTE_TOP_SAFE_PX;
          const bottomBound = NOTE_BOTTOM_SAFE_PX;
          const noteElement = document.querySelector(
            `[data-testid="sticky-card-${drag.id}"]`
          ) as HTMLElement | null;
          const visualHeight = noteElement
            ? noteElement.getBoundingClientRect().height / zoomLevel
            : note.height + NOTE_VISUAL_HEIGHT_BUFFER;
          const minLeft = (leftBound - panOffset.x) / zoomLevel;
          const maxLeft = (window.innerWidth - rightBound - panOffset.x) / zoomLevel - note.width;
          const minTop = (topBound - panOffset.y) / zoomLevel;
          const maxTop =
            (window.innerHeight - CANVAS_HEADER_HEIGHT - bottomBound - panOffset.y) /
              zoomLevel -
            visualHeight;

          return {
            ...note,
            left: Math.max(minLeft, Math.min(nextLeft, Math.max(minLeft, maxLeft))),
            top: Math.max(minTop, Math.min(nextTop, Math.max(minTop, maxTop))),
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
  }, [draggingNoteId, leftPanelOpen, panOffset.x, panOffset.y, rightPanelOpen, zoomLevel]);

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

  const selectChain = useCallback((chainId: string) => {
    const nextChain = availableChains.find((candidate) => candidate.chain_id === chainId);
    if (!nextChain) return;

    setSelectedNodeId(null);
    setSelectedFocusEdgeId(null);
    setSelectedEvidenceId(null);
    setPanOffset({ x: 0, y: 0 });
    setSelectedChainId(nextChain.chain_id);
    setActiveChain(toLocalChain(nextChain, locale, evidencePool));
  }, [availableChains, evidencePool, locale]);

  const copyMarkdownBrief = useCallback(async () => {
    if (!localizedMarkdownBrief) return;
    try {
      await navigator.clipboard.writeText(localizedMarkdownBrief);
      setMarkdownCopyStatus("copied");
      setShowManualCopyReport(false);
      window.setTimeout(() => setMarkdownCopyStatus("idle"), 1600);
    } catch {
      setMarkdownCopyStatus("failed");
      setShowManualCopyReport(true);
    }
  }, [localizedMarkdownBrief]);

  const selectManualCopyReport = useCallback(() => {
    manualCopyReportRef.current?.focus();
    manualCopyReportRef.current?.select();
  }, []);

  const selectedNote = notes.find((n) => n.id === selectedNodeId);

  const applySavedPayload = useCallback((payload: AnalyzeResponseV2) => {
    setRunId(payload.run_id ?? null);
    setRunStatus(payload.run_status ?? payload.analysis_mode);
    setRunSteps(payload.run_steps ?? []);
    setUsageLedger(payload.usage_ledger ?? []);
    setLastQuery(payload.query);
    setCurrentQuery(payload.query);
    setAvailableChains(payload.chains);
    setRecommendedChainId(payload.recommended_chain_id);
    const recommended =
      payload.chains.find((chain) => chain.chain_id === payload.recommended_chain_id) ??
      payload.chains[0];
    setSelectedChainId(recommended?.chain_id ?? null);
    setEvidencePool(payload.evidences);
    setRetrievalTrace(payload.retrieval_trace ?? []);
    setChallengeChecks(payload.challenge_checks ?? []);
    setAnalysisBrief(payload.analysis_brief ?? null);
    setMarkdownBrief(payload.markdown_brief ?? null);
    setProductHarness(payload.product_harness ?? null);
    setScenario(payload.scenario ?? null);
    setProductionBrief(payload.production_brief ?? null);
    setProductionHarness(payload.production_harness ?? null);
    setPipelineEval(payload.evaluation ?? null);
    setUncertaintyReport(payload.uncertainty_report ?? null);
    setActiveChain(
      recommended
        ? toLocalChain(recommended, locale, payload.evidences)
        : makePlaceholderChain(payload.query, locale)
    );
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
    setStatusNote(buildAnalysisStatusNote(payload, locale));
  }, [locale]);

  const refreshSavedRuns = useCallback(async () => {
    setSavedRunsStatus(locale === "en" ? "Loading saved runs..." : "\u6b63\u5728\u52a0\u8f7d\u5386\u53f2\u8fd0\u884c...");
    try {
      const response = await fetch(`${API_BASE}/api/runs`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as { runs: ApiSavedRunSummary[] };
      setSavedRuns(payload.runs ?? []);
      setSavedRunsStatus(
        payload.runs?.length
          ? locale === "en" ? "Saved runs loaded." : "\u5386\u53f2\u8fd0\u884c\u5df2\u52a0\u8f7d\u3002"
          : locale === "en" ? "No saved runs yet." : "\u6682\u65e0\u5386\u53f2\u8fd0\u884c\u3002"
      );
    } catch (error) {
      setSavedRunsStatus(
        error instanceof Error
          ? error.message
          : locale === "en" ? "Could not load saved runs." : "\u65e0\u6cd5\u52a0\u8f7d\u5386\u53f2\u8fd0\u884c\u3002"
      );
    }
  }, [locale]);

  const loadSavedRun = useCallback(async (targetRunId: string) => {
    setSavedRunsStatus(locale === "en" ? "Opening saved run..." : "\u6b63\u5728\u6253\u5f00\u5386\u53f2\u8fd0\u884c...");
    try {
      const response = await fetch(`${API_BASE}/api/runs/${targetRunId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as { response: AnalyzeResponseV2 };
      applySavedPayload(payload.response);
      setSavedRunsStatus(locale === "en" ? "Saved run opened." : "\u5386\u53f2\u8fd0\u884c\u5df2\u6253\u5f00\u3002");
    } catch (error) {
      setSavedRunsStatus(
        error instanceof Error
          ? error.message
          : locale === "en" ? "Could not open saved run." : "\u65e0\u6cd5\u6253\u5f00\u5386\u53f2\u8fd0\u884c\u3002"
      );
    }
  }, [applySavedPayload, locale]);

  const uploadEvidence = useCallback(async () => {
    const content = uploadedEvidenceText.trim();
    if (!content) return;
    setUploadedEvidenceStatus(locale === "en" ? "Uploading evidence..." : "\u6b63\u5728\u4e0a\u4f20\u8bc1\u636e...");
    try {
      const response = await fetch(`${API_BASE}/api/evidence/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: currentQuery || lastQuery || uploadedEvidenceTitle || "uploaded evidence",
          title: uploadedEvidenceTitle || "Uploaded evidence",
          content,
          source_name: uploadedEvidenceTitle || "uploaded evidence",
          domain: scenario?.key === "postmortem" ? "postmortem" : "general",
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as { evidence_id: string };
      setUploadedEvidenceStatus(
        locale === "en"
          ? `Stored ${payload.evidence_id}. It can be reused as user-owned evidence.`
          : `\u5df2\u4fdd\u5b58 ${payload.evidence_id}\uff0c\u540e\u7eed\u53ef\u4f5c\u4e3a\u7528\u6237\u81ea\u6709\u8bc1\u636e\u590d\u7528\u3002`
      );
      setUploadedEvidenceText("");
    } catch (error) {
      setUploadedEvidenceStatus(
        error instanceof Error
          ? error.message
          : locale === "en" ? "Evidence upload failed." : "\u8bc1\u636e\u4e0a\u4f20\u5931\u8d25\u3002"
      );
    }
  }, [currentQuery, lastQuery, locale, scenario?.key, uploadedEvidenceText, uploadedEvidenceTitle]);

  const runProviderPreflight = useCallback(async () => {
    setProviderPreflightLoading(true);
    setProviderPreflight(null);
    try {
      const body: Record<string, unknown> = {
        model: selectedModel,
        api_key: apiKey,
      };
      if (selectedExplicitModel) body.explicit_model = selectedExplicitModel;

      const response = await fetch(`${API_BASE}/api/providers/preflight`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        throw new Error(`Preflight failed (${response.status})`);
      }
      const payload = (await response.json()) as ApiProviderPreflight;
      setProviderPreflight(payload);
    } catch (error) {
      setProviderPreflight({
        provider: selectedModel,
        model_name: selectedExplicitModel || selectedModel,
        status: "error",
        can_run_analysis: false,
        failure_code: "request_failed",
        diagnosis: error instanceof Error ? error.message : "Preflight request failed.",
        user_action:
          locale === "en"
            ? "Check that the backend is running, then retry preflight."
            : "\u8bf7\u786e\u8ba4\u540e\u7aef\u6b63\u5728\u8fd0\u884c\uff0c\u7136\u540e\u91cd\u65b0\u9884\u68c0\u3002",
        checks: [],
      });
    } finally {
      setProviderPreflightLoading(false);
    }
  }, [apiKey, locale, selectedExplicitModel, selectedModel]);

  const runAnalysis = useCallback(async () => {
    const query = currentQuery.trim();
    if (!query) return;

    const requestId = activeRequestIdRef.current + 1;
    activeRequestIdRef.current = requestId;
    setActiveChain(makePlaceholderChain(query, locale));
    setAvailableChains([]);
    setRecommendedChainId(null);
    setSelectedChainId(null);
    setEvidencePool([]);
    setRetrievalTrace([]);
    setChallengeChecks([]);
    setAnalysisBrief(null);
    setMarkdownBrief(null);
    setMarkdownCopyStatus("idle");
    setShowManualCopyReport(false);
    setProductHarness(null);
    setScenario(null);
    setProductionBrief(null);
    setProductionHarness(null);
    setRunId(null);
    setRunStatus("running");
    setRunSteps([]);
    setUsageLedger([]);
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
    setStatusNote(locale === "en" ? "Running live analysis..." : "\u6b63\u5728\u6267\u884c\u771f\u5b9e\u5206\u6790...");
    setLastQuery(query);

    const body: Record<string, unknown> = {
      query,
      model: selectedModel,
      api_key: apiKey,
      scenario_override: scenarioOverride === "auto" ? null : scenarioOverride,
    };
    if (selectedExplicitModel) body.explicit_model = selectedExplicitModel;

    // Helper to process a successful payload (shared between SSE done and fallback)
    const processPayload = (payload: AnalyzeResponseV2) => {
      if (activeRequestIdRef.current !== requestId) return;
      if (payload.chains.length === 0) {
        setRunId(payload.run_id ?? null);
        setRunStatus(payload.run_status ?? payload.analysis_mode);
        setRunSteps(payload.run_steps ?? []);
        setUsageLedger(payload.usage_ledger ?? []);
        setAvailableChains([]);
        setRecommendedChainId(null);
        setSelectedChainId(null);
        setEvidencePool(payload.evidences);
        setRetrievalTrace(payload.retrieval_trace ?? []);
        setChallengeChecks(payload.challenge_checks ?? []);
        setAnalysisBrief(payload.analysis_brief ?? null);
        setMarkdownBrief(payload.markdown_brief ?? null);
        setMarkdownCopyStatus("idle");
        setShowManualCopyReport(false);
        setProductHarness(payload.product_harness ?? null);
        setScenario(payload.scenario ?? null);
        setProductionBrief(payload.production_brief ?? null);
        setProductionHarness(payload.production_harness ?? null);
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

      setRunId(payload.run_id ?? null);
      setRunStatus(payload.run_status ?? payload.analysis_mode);
      setRunSteps(payload.run_steps ?? []);
      setUsageLedger(payload.usage_ledger ?? []);
      setAvailableChains(payload.chains);
      setRecommendedChainId(payload.recommended_chain_id);
      setSelectedChainId(recommended.chain_id);
      setEvidencePool(payload.evidences);
      setRetrievalTrace(payload.retrieval_trace ?? []);
      setChallengeChecks(payload.challenge_checks ?? []);
      setAnalysisBrief(payload.analysis_brief ?? null);
      setMarkdownBrief(payload.markdown_brief ?? null);
      setMarkdownCopyStatus("idle");
      setShowManualCopyReport(false);
      setProductHarness(payload.product_harness ?? null);
      setScenario(payload.scenario ?? null);
      setProductionBrief(payload.production_brief ?? null);
      setProductionHarness(payload.production_harness ?? null);
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
    };

    // Helper for fallback on error
    const fallbackToDemo = () => {
      if (activeRequestIdRef.current !== requestId) return;
      setActiveChain(localizedDemo.primaryChain);
      setAvailableChains([]);
      setRecommendedChainId(null);
      setSelectedChainId(null);
      setEvidencePool([]);
      setRetrievalTrace([]);
      setChallengeChecks([]);
      setAnalysisBrief(null);
      setMarkdownBrief(null);
      setMarkdownCopyStatus("idle");
      setShowManualCopyReport(false);
      setProductHarness(null);
      setScenario(null);
      setProductionBrief(null);
      setProductionHarness(null);
      setRunId(null);
      setRunStatus("demo");
      setRunSteps([]);
      setUsageLedger([]);
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
          : "\u771f\u5b9e\u5206\u6790\u5931\u8d25\uff0c\u5f53\u524d\u56de\u9000\u5230\u672c\u5730 demo \u8bc1\u636e\u5899\u3002"
      );
    };

    try {
      // Try SSE streaming endpoint first
      const response = await fetch(`${API_BASE}/api/analyze/v2/stream`, {
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
                    : `\u5206\u6790\u9519\u8bef\uff1a${event.error}\uff0c\u5f53\u524d\u663e\u793a demo \u56de\u9000\u6570\u636e\u3002`
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
        // Non-SSE response fallback: treat as regular JSON.
        const payload = (await response.json()) as AnalyzeResponseV2;
        processPayload(payload);
      }
    } catch {
      setPipelineProgress(null);
      fallbackToDemo();
    }
  }, [
    currentQuery,
    selectedModel,
    selectedExplicitModel,
    apiKey,
    scenarioOverride,
    locale,
    localizedDemo.primaryChain,
  ]);

  return (
    <div
      ref={boardRef}
      className="font-caveat evidence-board no-select"
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: `
          /* Analyst desk: warm vellum, archival grid, subtle case-room vignette */
          repeating-linear-gradient(
            90deg,
            transparent 0px,
            rgba(96, 70, 38, 0.045) 1px,
            transparent 2px,
            transparent 18px
          ),
          repeating-linear-gradient(
            0deg,
            transparent 0px,
            rgba(96, 70, 38, 0.032) 1px,
            transparent 2px,
            transparent 18px
          ),
          radial-gradient(ellipse at 18% 18%, rgba(255, 249, 235, 0.75) 0%, transparent 36%),
          radial-gradient(ellipse at 86% 78%, rgba(72, 93, 88, 0.16) 0%, transparent 42%),
          radial-gradient(ellipse at 52% 52%, rgba(164, 61, 45, 0.08) 0%, transparent 58%),
          linear-gradient(135deg, #f7f0e3 0%, #efe2ce 46%, #dcc8a7 100%)
        `,
        fontFamily: "var(--font-sans), 'IBM Plex Sans', sans-serif",
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
          height: "64px",
          background: "rgba(41, 31, 21, 0.86)",
          backdropFilter: "blur(18px)",
          borderBottom: "1px solid rgba(255, 238, 206, 0.18)",
          boxShadow: "0 14px 38px rgba(42, 28, 14, 0.18)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          zIndex: 100,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              background: "linear-gradient(135deg, rgba(255,248,235,0.95), rgba(210,179,122,0.82))",
              border: "1px solid rgba(255, 238, 206, 0.26)",
              borderRadius: "12px",
              boxShadow: "0 8px 22px rgba(0,0,0,0.22)",
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
              stroke="#8f2e21"
              strokeWidth="2"
            >
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1
            className="font-caveat"
            style={{
              fontFamily: "var(--font-display), Fraunces, serif",
              color: "#fff2dc",
              fontSize: "1.35rem",
              fontWeight: 700,
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
              background: "rgba(255, 248, 235, 0.08)",
              border: "1px solid rgba(255, 238, 206, 0.16)",
              color: "#f0d5aa",
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
              color: "#e5cda8",
              fontSize: "0.65rem",
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                background: qualityGateTone === "strong" ? "#74b276" : qualityGateTone === "caution" ? "#d39b46" : "#78a7bd",
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
          <div className="command-chip-row">
            <span className={`command-chip command-chip-${qualityGateTone}`}>
              {locale === "en" ? "Coverage" : "\u8986\u76d6"} {evidenceCoverageScore}%
            </span>
            <span className="command-chip">
              {locale === "en" ? "Sources" : "\u6765\u6e90"} {sourceHitCount}
            </span>
            {traceFailureCount > 0 && (
              <span className="command-chip command-chip-caution">
                {locale === "en" ? "Source issues" : "\u6765\u6e90\u95ee\u9898"} {traceFailureCount}
              </span>
            )}
          </div>
          {pipelineProgress && analysisMode.loading && (
            <div style={{ display: "flex", alignItems: "center", gap: "4px", flex: 1, minWidth: 0 }}>
              <div
                style={{
                  flex: 1,
                  height: "3px",
                  background: "rgba(255, 238, 206, 0.14)",
                  borderRadius: "2px",
                  overflow: "hidden",
                  minWidth: 0,
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${pipelineProgress.totalSteps > 0 ? (pipelineProgress.stepIndex / pipelineProgress.totalSteps) * 100 : 0}%`,
                    background: "linear-gradient(90deg, #d39b46, #74b276)",
                    borderRadius: "2px",
                    transition: "width 0.4s ease",
                  }}
                />
              </div>
                <span style={{ fontSize: "0.55rem", color: "#e5cda8", whiteSpace: "nowrap" }}>
                {pipelineProgress.stepIndex}/{pipelineProgress.totalSteps}
              </span>
            </div>
          )}
          <button
            onClick={() => setLocale(locale === "en" ? "zh" : "en")}
            style={{
              background: "rgba(255,248,235,0.08)",
              border: "1px solid rgba(255,238,206,0.2)",
              borderRadius: "999px",
              padding: "5px 10px",
              fontSize: "0.62rem",
              color: "#f0d5aa",
              cursor: "pointer",
            }}
          >
            {locale === "en" ? "EN" : "\u4e2d"}
          </button>
        </div>
      </header>

      <div className="canvas-hint">
        {locale === "en"
          ? "Pan from empty space. Drag notes to rearrange evidence."
          : "\u7a7a\u767d\u5904\u53ef\u5e73\u79fb\u89c6\u56fe\uff0c\u4fbf\u7b7e\u53ef\u62d6\u62fd\u91cd\u6392\u3002"}
      </div>

      <div className="zoom-controls" aria-label={locale === "en" ? "Canvas zoom controls" : "\u89c6\u56fe\u7f29\u653e\u63a7\u4ef6"}>
        <button type="button" onClick={() => changeZoom(-0.1)} disabled={zoomLevel <= 0.7}>-</button>
        <button type="button" onClick={resetViewport}>{Math.round(zoomLevel * 100)}%</button>
        <button type="button" onClick={() => changeZoom(0.1)} disabled={zoomLevel >= 1.5}>+</button>
      </div>

      {!leftPanelOpen && (
        <button
          type="button"
          onClick={() => setLeftPanelOpen(true)}
          className="panel-toggle-button panel-toggle-left panel-toggle-collapsed"
          aria-pressed="true"
          aria-label={locale === "en" ? "Show left panel" : "\u663e\u793a\u5de6\u4fa7\u9762\u677f"}
        >
          {locale === "en" ? "Brief" : "\u7b80\u62a5"}
        </button>
      )}

      {!rightPanelOpen && (
        <button
          type="button"
          onClick={() => setRightPanelOpen(true)}
          className="panel-toggle-button panel-toggle-right panel-toggle-collapsed"
          aria-pressed="true"
          aria-label={locale === "en" ? "Show right panel" : "\u663e\u793a\u53f3\u4fa7\u9762\u677f"}
        >
          {locale === "en" ? "Evidence" : "\u8bc1\u636e"}
        </button>
      )}

      <aside
        className="left-panel"
        style={{
          position: "absolute",
          display: leftPanelOpen ? "block" : "none",
          top: "64px",
          left: 0,
          width: "280px",
          bottom: 0,
          padding: "40px 16px 18px",
          background: "linear-gradient(180deg, rgba(255,252,246,0.88), rgba(239,226,204,0.72))",
          backdropFilter: "blur(18px)",
          borderRight: "1px solid var(--analyst-border)",
          boxShadow: "18px 0 44px rgba(72, 48, 22, 0.10)",
          zIndex: 50,
          overflowY: "auto",
        }}
      >
        <button
          type="button"
          onClick={() => setLeftPanelOpen(false)}
          className="panel-embedded-toggle"
          aria-label={locale === "en" ? "Hide left panel" : "\u9690\u85cf\u5de6\u4fa7\u9762\u677f"}
        >
          {locale === "en" ? "Hide" : "\u6536\u8d77"}
        </button>
        <div className="compact-item query-brief" style={{ marginBottom: "14px" }}>
          <div className="compact-label">{locale === "en" ? "Investigation brief" : "\u8c03\u67e5\u7b80\u62a5"}</div>
          <div className="query-brief-title">{t("query.label")}</div>
          <textarea
            value={currentQuery}
            onChange={(event) => setCurrentQuery(event.target.value)}
            placeholder={t("query.placeholderExample")}
            className="analyst-textarea"
            style={{
              width: "100%",
              minHeight: "116px",
              resize: "none",
              border: "1px solid var(--analyst-border)",
              borderRadius: "14px",
              padding: "12px 13px",
              background: "rgba(255,255,255,0.74)",
              color: "var(--analyst-ink)",
              fontSize: "0.82rem",
              lineHeight: 1.55,
              outline: "none",
              boxShadow: "inset 0 1px 0 rgba(255,255,255,0.78)",
            }}
          />
          <button
            type="button"
            className="sample-query-button"
            data-testid="sample-a-share-query"
            onClick={() => {
              setCurrentQuery("芯原股份今天盘中为什么下跌？");
              setScenarioOverride("market");
            }}
          >
            {t("query.sampleAshare")}
          </button>
          <div className="compact-label" style={{ marginTop: "10px" }}>
            {locale === "en" ? "Use case" : "\u4f7f\u7528\u573a\u666f"}
          </div>
          <select
            data-testid="scenario-selector"
            value={scenarioOverride}
            onChange={(event) => setScenarioOverride(event.target.value)}
            className="analyst-input"
            style={{ cursor: "pointer" }}
          >
            <option value="auto">Auto detect</option>
            <option value="market">Market / Investment</option>
            <option value="policy_geopolitics">Policy / Geopolitics</option>
            <option value="postmortem">Postmortem</option>
          </select>
          <div style={{ fontSize: "0.56rem", color: "var(--analyst-muted)", marginTop: "5px", lineHeight: 1.35 }}>
            {scenario
              ? locale === "en"
                ? `${scenario.label} (${Math.round(scenario.confidence * 100)}%, ${scenario.detection_method})`
                : `${localizeBriefText(scenario.label, locale)} (${Math.round(scenario.confidence * 100)}%, ${scenario.detection_method})`
              : locale === "en"
                ? "Choose how the answer should be organized."
                : "\u9009\u62e9\u7b54\u6848\u5e94\u5982\u4f55\u7ec4\u7ec7\u3002"}
          </div>
          <button
            type="button"
            className="advanced-toggle"
            aria-expanded={showAdvancedSettings}
            onClick={() => setShowAdvancedSettings((current) => !current)}
          >
            <span>{locale === "en" ? "Provider settings" : "\u6a21\u578b\u4e0e\u5bc6\u94a5\u8bbe\u7f6e"}</span>
            <span>{showAdvancedSettings ? "-" : "+"}</span>
          </button>
          {showAdvancedSettings && (
            <div className="advanced-settings">
          <div className="compact-label" style={{ marginTop: "2px" }}>{t("query.model")}</div>
          <div className="provider-lock">
            <span>OpenRouter</span>
            <span>{locale === "en" ? "fixed provider" : "\u56fa\u5b9a\u63d0\u4f9b\u5546"}</span>
          </div>
          {Object.keys(availableModels).length > 0 && (
            <select
              value={selectedExplicitModel}
              onChange={(event) => setSelectedExplicitModel(event.target.value)}
              className="analyst-input"
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
            className="analyst-input"
          />
          <div style={{ fontSize: "0.58rem", color: "var(--analyst-muted)", marginTop: "6px", lineHeight: 1.45 }}>
            {locale === "en"
              ? "Stored in this browser session and sent only to the selected model provider."
              : "\u4ec5\u4fdd\u5b58\u5728\u5f53\u524d\u6d4f\u89c8\u5668\u4f1a\u8bdd\u4e2d\uff0c\u5e76\u53ea\u53d1\u9001\u7ed9\u4f60\u9009\u62e9\u7684\u6a21\u578b\u63d0\u4f9b\u5546\u3002"}
          </div>
          <button
            type="button"
            onClick={runProviderPreflight}
            disabled={providerPreflightLoading || !apiKey.trim()}
            style={{
              marginTop: "8px",
              width: "100%",
              padding: "8px 10px",
              borderRadius: "8px",
              border: "1px solid rgba(49, 95, 131, 0.24)",
              background: providerPreflightLoading ? "rgba(49,95,131,0.08)" : "rgba(255,255,255,0.66)",
              color: "var(--analyst-blue)",
              fontSize: "0.64rem",
              fontWeight: 800,
              cursor: providerPreflightLoading || !apiKey.trim() ? "not-allowed" : "pointer",
            }}
          >
            {providerPreflightLoading
              ? locale === "en" ? "Checking model..." : "\u6b63\u5728\u9884\u68c0\u6a21\u578b..."
              : locale === "en" ? "Run model preflight" : "\u8fd0\u884c\u6a21\u578b\u9884\u68c0"}
          </button>
          {providerPreflight && (
            <div
              style={{
                marginTop: "8px",
                padding: "8px 9px",
                borderRadius: "8px",
                border: providerPreflight.can_run_analysis
                  ? "1px solid rgba(92,130,84,0.22)"
                  : "1px solid rgba(160,80,60,0.22)",
                background: providerPreflight.can_run_analysis
                  ? "rgba(92,130,84,0.08)"
                  : "rgba(160,80,60,0.08)",
                color: providerPreflight.can_run_analysis ? "#526f44" : "#9a4635",
                fontSize: "0.58rem",
                lineHeight: 1.45,
              }}
            >
              <strong>
                {providerPreflight.can_run_analysis
                  ? locale === "en" ? "Preflight passed" : "\u9884\u68c0\u901a\u8fc7"
                  : locale === "en" ? "Preflight blocked" : "\u9884\u68c0\u672a\u901a\u8fc7"}
              </strong>
              {` · ${providerPreflight.model_name}`}
              <div style={{ marginTop: "4px", color: "#6b5a42" }}>
                {providerPreflight.user_action || providerPreflight.diagnosis}
              </div>
            </div>
          )}
            </div>
          )}
          <button
            onClick={runAnalysis}
            disabled={analysisMode.loading || !currentQuery.trim()}
            style={{
              marginTop: "10px",
              width: "100%",
              padding: "11px 12px",
              borderRadius: "14px",
              border: "1px solid rgba(49, 95, 131, 0.28)",
              background: analysisMode.loading
                ? "rgba(49,95,131,0.10)"
                : "linear-gradient(135deg, rgba(49,95,131,0.94), rgba(35,68,94,0.96))",
              color: analysisMode.loading ? "var(--analyst-blue)" : "#fff8eb",
              fontSize: "0.78rem",
              fontWeight: 700,
              cursor: analysisMode.loading ? "wait" : "pointer",
              boxShadow: analysisMode.loading
                ? "none"
                : "0 14px 30px rgba(30, 62, 88, 0.22)",
            }}
          >
            {analysisMode.loading ? t("header.status.processing") : t("query.submit")}
          </button>
          <div
            data-testid="run-orchestration-status"
            style={{
              marginTop: "9px",
              padding: "8px 9px",
              border: "1px solid rgba(49, 95, 131, 0.14)",
              borderRadius: "8px",
              background: "rgba(255,255,255,0.54)",
              color: "#5c4a32",
              fontSize: "0.56rem",
              lineHeight: 1.45,
            }}
          >
            <strong style={{ color: "#315f83" }}>
              {locale === "en" ? "Run orchestration" : "\u8fd0\u884c\u7f16\u6392"}
            </strong>
            <div>
              {locale === "en" ? "Status" : "\u72b6\u6001"}: {runStatus}
              {runId ? ` / ${runId}` : ""}
            </div>
            {runSteps.slice(0, 4).map((step) => (
              <div key={step.id}>
                {step.status.toUpperCase()} - {step.label}
              </div>
            ))}
            {usageLedger.slice(0, 3).map((item) => (
              <div key={`${item.category}-${item.name}`}>
                {item.category}: {item.quota_owner} / {item.status}
              </div>
            ))}
          </div>
        </div>

        <UploadedEvidencePanel
          title={uploadedEvidenceTitle}
          text={uploadedEvidenceText}
          status={uploadedEvidenceStatus}
          locale={locale}
          onTitleChange={setUploadedEvidenceTitle}
          onTextChange={setUploadedEvidenceText}
          onUpload={uploadEvidence}
        />

        <SavedRunsPanel
          runs={savedRuns}
          status={savedRunsStatus}
          locale={locale}
          onRefresh={refreshSavedRuns}
          onOpenRun={loadSavedRun}
        />

        <h2 className="panel-title">{t("panel.hypotheses")}</h2>

        {localizedAnalysisBrief && (
          <ReadableBriefPanel
            brief={localizedAnalysisBrief}
            markdownBrief={localizedMarkdownBrief}
            markdownCopyStatus={markdownCopyStatus}
            showManualCopyReport={showManualCopyReport}
            sourceTransparencySummary={sourceTransparencySummary}
            hasRefutingChallenges={challengeCheckSummary.refuting > 0}
            locale={locale}
            manualCopyReportRef={manualCopyReportRef}
            onCopyMarkdown={copyMarkdownBrief}
            onSelectManualCopyReport={selectManualCopyReport}
          />
        )}

        {productionBrief && (
          <ProductionBriefPanel
            brief={productionBrief}
            harness={productionHarness}
            locale={locale}
            localizeText={localizeBriefText}
          />
        )}

        {productHarness && (
          <div className="compact-item" style={{ background: "rgba(255,255,255,0.76)" }}>
            <div className="compact-label">{locale === "en" ? "Value harness" : "Value Harness"}</div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
              <strong style={{ fontSize: "0.68rem", color: "#4d3c28" }}>
                {Math.round(productHarness.score * 100)}%
              </strong>
              <span style={{ fontSize: "0.56rem", color: productHarness.status === "ready_for_review" ? "#526f44" : "#a0503c", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {productHarness.status.replaceAll("_", " ")}
              </span>
            </div>
            <div style={{ marginTop: "6px", fontSize: "0.6rem", color: "#5c4a32", lineHeight: 1.45 }}>
              {locale === "en"
                ? productHarness.user_value_summary
                : localizeBriefText(productHarness.user_value_summary, locale)}
            </div>
            {productHarness.checks.slice(0, 3).map((check) => (
              <div key={check.id} style={{ marginTop: "6px", fontSize: "0.56rem", color: check.status === "pass" ? "#526f44" : check.status === "warn" ? "#8a6a40" : "#a0503c", lineHeight: 1.35 }}>
                {check.status.toUpperCase()} · {check.label}
              </div>
            ))}
            {productHarness.next_actions[0] && (
              <div style={{ marginTop: "6px", fontSize: "0.56rem", color: "#8b7355", lineHeight: 1.45 }}>
                {locale === "en" ? "Next: " : "\u4e0b\u4e00\u6b65\uff1a"}
                {locale === "en"
                  ? productHarness.next_actions[0]
                  : localizeBriefText(productHarness.next_actions[0], locale)}
              </div>
            )}
          </div>
        )}

        <div className="compact-item">
          <div className="compact-label">{t("home.chain.primary")}</div>
          <div>{primaryChainTitle}</div>
          <div style={{ marginTop: "4px", fontSize: "0.6rem", color: "#7a6b55" }}>
            {t("graph.confidence")} = {activeChainConfidence}%
          </div>
          {activeChainIsRecommended && availableChains.length > 0 && (
            <div style={{ marginTop: "6px", fontSize: "0.56rem", color: "#4a7a9e", letterSpacing: "0.04em", textTransform: "uppercase" }}>
              {locale === "en" ? "Recommended chain" : "\u63a8\u8350\u94fe\u8def"}
            </div>
          )}
          {hasLowConfidence && (
            <div style={{ marginTop: "6px", fontSize: "0.58rem", color: "#a0503c", lineHeight: 1.5 }}>
              {locale === "en" ? "Low confidence. Treat this chain as a tentative explanation." : "\u5f53\u524d\u94fe\u8def\u7f6e\u4fe1\u504f\u4f4e\uff0c\u8bf7\u5c06\u5176\u89c6\u4e3a\u6682\u5b9a\u89e3\u91ca\u3002"}
            </div>
          )}
          {hasLowEvidenceCoverage && (
            <div style={{ marginTop: "4px", fontSize: "0.58rem", color: "#a0503c", lineHeight: 1.5 }}>
              {locale === "en" ? "Evidence coverage is thin. Inspect sources before trusting the result." : "\u5f53\u524d\u8bc1\u636e\u8986\u76d6\u504f\u8584\uff0c\u4fe1\u4efb\u7ed3\u679c\u524d\u8bf7\u5148\u68c0\u67e5\u6765\u6e90\u3002"}
            </div>
          )}
        </div>

        {causalReasonSummaries.length > 0 && (
          <div className="compact-item">
            <div className="compact-label">{locale === "en" ? "Reason summary" : "\u539f\u56e0\u6458\u8981"}</div>
            {causalReasonSummaries.map((reason) => (
              <button
                type="button"
                key={`${reason.id}-reason`}
                onClick={() => {
                  const edge = activeApiChain?.edges.find((item) => item.id === reason.id);
                  if (edge) focusEdge(edge);
                }}
                style={{
                  width: "100%",
                  marginTop: "7px",
                  padding: "7px 8px",
                  borderRadius: "6px",
                  border: selectedFocusEdgeId === reason.id
                    ? "1px solid rgba(59,110,165,0.30)"
                    : "1px solid rgba(160,140,110,0.14)",
                  background: selectedFocusEdgeId === reason.id
                    ? "rgba(59,110,165,0.08)"
                    : "rgba(255,255,255,0.50)",
                  color: "#5c4a32",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <div style={{ fontSize: "0.62rem", lineHeight: 1.45 }}>
                  <strong>{reason.source}</strong> {locale === "en" ? "helped lead to" : "\u5bfc\u81f4"} <strong>{reason.target}</strong>
                </div>
                <div style={{ marginTop: "3px", fontSize: "0.54rem", color: "#8b7355", lineHeight: 1.4 }}>
                  {locale === "en"
                    ? `${reason.strength}% edge strength · ${reason.evidenceCount} evidence item(s)`
                    : `${reason.strength}% \u8fb9\u5f3a\u5ea6 · ${reason.evidenceCount} \u6761\u8bc1\u636e`}
                  {reason.evidenceSource ? ` · ${reason.evidenceSource}` : ""}
                </div>
                {reason.evidenceExcerpt && (
                  <div style={{ marginTop: "5px", fontSize: "0.58rem", color: "#6b5a42", lineHeight: 1.45 }}>
                    {reason.evidenceExcerpt.length > 120
                      ? `${reason.evidenceExcerpt.slice(0, 120)}...`
                      : reason.evidenceExcerpt}
                  </div>
                )}
                <div style={{ marginTop: "4px", fontSize: "0.52rem", color: "#8b7355", lineHeight: 1.35 }}>
                  {formatRefutationStatusLabel(reason.refutationStatus, locale)}
                </div>
              </button>
            ))}
          </div>
        )}

        {chainProbabilityItems.length > 0 && (
          <div className="compact-item">
            <div className="compact-label">{t("home.chain.alternative")}</div>
            {chainProbabilityItems.map((chain) => (
              <button
                type="button"
                key={chain.chain_id}
                onClick={() => selectChain(chain.chain_id)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  marginTop: "6px",
                  padding: "6px 8px",
                  borderRadius: "4px",
                  border: chain.chain_id === activeChainId ? "1px solid rgba(59,110,165,0.28)" : "1px solid rgba(160,140,110,0.12)",
                  background: chain.chain_id === activeChainId ? "rgba(59,110,165,0.08)" : "rgba(255,255,255,0.55)",
                  color: "#5c4a32",
                  fontSize: "0.62rem",
                  cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px" }}>
                  <span>{localizeCausalText(chain.label, locale)}</span>
                  {chain.chain_id === recommendedChainId && (
                    <span style={{ fontSize: "0.5rem", color: "#4a7a9e", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      {locale === "en" ? "Rec" : "\u63a8\u8350"}
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
            <div className="compact-label">{locale === "en" ? "Chain compare" : "\u94fe\u8def\u6bd4\u8f83"}</div>
            {chainCompareItems.map((chain) => (
              <button
                type="button"
                key={`${chain.chain_id}-compare`}
                onClick={() => selectChain(chain.chain_id)}
                aria-pressed={chain.chain_id === activeChainId}
                data-testid={`chain-compare-${chain.chain_id}`}
                style={{
                  width: "100%",
                  marginTop: "6px",
                  padding: "8px 9px",
                  borderWidth: "1px",
                  borderStyle: "solid",
                  borderColor: chain.chain_id === activeChainId
                    ? "rgba(49,95,131,0.34)"
                    : "rgba(160,140,110,0.14)",
                  borderRadius: "12px",
                  background: chain.chain_id === activeChainId
                    ? "linear-gradient(135deg, rgba(49,95,131,0.12), rgba(255,255,255,0.78))"
                    : "rgba(255,255,255,0.45)",
                  cursor: "pointer",
                  textAlign: "left",
                  fontSize: "0.62rem",
                  color: "var(--analyst-ink-soft)",
                  lineHeight: 1.5,
                  boxShadow: chain.chain_id === activeChainId
                    ? "0 10px 24px rgba(49,95,131,0.12)"
                    : "none",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                  <strong style={{ color: chain.chain_id === activeChainId ? "#3b6ea5" : "#5c4a32" }}>{chain.label}</strong>
                  <span>{chain.probability}%</span>
                </div>
                <div>
                  {locale === "en"
                    ? `${chain.supportCount} support / ${
                        chain.refuteCount > 0 ? `${chain.refuteCount} challenge` : formatRefutationStatusLabel(chain.refutationStatus, locale)
                      } / ${chain.nodeCount} nodes`
                    : `${chain.supportCount} \u652f\u6301 / ${
                        chain.refuteCount > 0 ? `${chain.refuteCount} \u53cd\u8bc1` : formatRefutationStatusLabel(chain.refutationStatus, locale)
                      } / ${chain.nodeCount} \u8282\u70b9`}
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
              {locale === "en" ? "High uncertainty. Review upstream assumptions and evidence quality." : "\u5f53\u524d\u4e0d\u786e\u5b9a\u6027\u8f83\u9ad8\uff0c\u8bf7\u91cd\u70b9\u68c0\u67e5\u4e0a\u6e38\u5047\u8bbe\u4e0e\u8bc1\u636e\u8d28\u91cf\u3002"}
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
          display: rightPanelOpen ? "block" : "none",
          top: "64px",
          right: 0,
          width: "340px",
          bottom: 0,
          padding: "40px 16px 18px",
          background: "linear-gradient(180deg, rgba(255,252,246,0.90), rgba(238,226,207,0.76))",
          backdropFilter: "blur(18px)",
          borderLeft: "1px solid var(--analyst-border)",
          boxShadow: "-18px 0 44px rgba(72, 48, 22, 0.10)",
          zIndex: 50,
          overflowY: "auto",
        }}
      >
        <button
          type="button"
          onClick={() => setRightPanelOpen(false)}
          className="panel-embedded-toggle panel-embedded-toggle-right"
          aria-label={locale === "en" ? "Hide right panel" : "\u9690\u85cf\u53f3\u4fa7\u9762\u677f"}
        >
          {locale === "en" ? "Hide" : "\u6536\u8d77"}
        </button>
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
              color: (statusNote && (statusNote.includes("\u5931\u8d25") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "#c0392b" : undefined,
              background: (statusNote && (statusNote.includes("\u5931\u8d25") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "rgba(192, 57, 43, 0.08)" : undefined,
              borderLeft: (statusNote && (statusNote.includes("\u5931\u8d25") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "2px solid #c0392b" : undefined,
              padding: (statusNote && (statusNote.includes("\u5931\u8d25") || statusNote.includes("failed") || statusNote.includes("error") || statusNote.includes("Error"))) ? "2px 6px" : undefined,
            }}
          >
            {statusNote || (analysisMode.isDemo ? t("demo.banner") : t("status.liveAnalysis"))}
          </div>
          <SourceProgressPanel
            loading={analysisMode.loading}
            mode={analysisMode.mode}
            pipelineProgress={pipelineProgress}
            partialLiveReasons={analysisMode.partialLiveReasons}
            locale={locale}
          />
          {!analysisMode.loading && (
            <SourceTracePanel
              locale={locale}
              mode={analysisMode.mode}
              retrievalTrace={retrievalTrace}
            />
          )}
        </div>

        {uncertaintyReport && !analysisMode.isDemo && (
          <div className="compact-item" style={{ background: "rgba(255,255,255,0.72)" }}>
            <div className="compact-label">{locale === "en" ? "Uncertainty report" : "\u4e0d\u786e\u5b9a\u6027\u62a5\u544a"}</div>
            <div style={{ fontSize: "0.65rem", color: "#5c4a32", lineHeight: 1.5 }}>
              {Math.round(uncertaintyReport.overall_uncertainty * 100)}% · {uncertaintyReport.summary}
            </div>
            {uncertaintyReport.dominant_uncertainty_type && (
              <div style={{ fontSize: "0.56rem", color: "#8b7355", marginTop: "4px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {locale === "en" ? "Dominant" : "\u4e3b\u5bfc\u7c7b\u578b"}: {uncertaintyReport.dominant_uncertainty_type}
              </div>
            )}
          </div>
        )}

        <ChallengeCoveragePanel
          challengeChecks={challengeChecks}
          challengeCheckSummary={challengeCheckSummary}
          activeEdges={activeApiChain?.edges ?? []}
          locale={locale}
          localizeText={localizeCausalText}
          onFocusEdge={focusEdge}
        />

        {selectedApiEdges.length > 0 && (
          <div className="compact-item" style={{ background: "rgba(255,255,255,0.72)" }}>
            <div className="compact-label">{locale === "en" ? "Connected edges" : "\u5173\u8054\u8fb9"}</div>
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
                  {locale === "en" ? "Conflict" : "\u51b2\u7a81"}: {edge.evidence_conflict ?? "none"}
                </div>
                <div style={{ fontSize: "0.54rem", color: edge.refuting_evidence_ids.length > 0 ? "#a0503c" : "#8b7355", marginTop: "3px" }}>
                  {formatRefutationStatusLabel(edge.refutation_status, locale)}
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

        <EvidenceFilterPanel
          title={t("home.evidence.related")}
          emptyLabel={t("home.evidence.empty")}
          sourceFilterOptions={sourceFilterOptions}
          evidenceSourceFilter={evidenceSourceFilter}
          setEvidenceSourceFilter={setEvidenceSourceFilter}
          evidenceStanceFilter={evidenceStanceFilter}
          setEvidenceStanceFilter={setEvidenceStanceFilter}
          evidenceConfidenceFilter={evidenceConfidenceFilter}
          setEvidenceConfidenceFilter={setEvidenceConfidenceFilter}
          evidenceQualityFilter={evidenceQualityFilter}
          setEvidenceQualityFilter={setEvidenceQualityFilter}
          showAllEvidence={showAllEvidence}
          setShowAllEvidence={setShowAllEvidence}
          hiddenEvidenceCount={hiddenEvidenceCount}
          hiddenEvidenceBreakdown={hiddenEvidenceBreakdown}
          prioritizedEvidence={prioritizedEvidence}
          selectedEvidenceId={selectedEvidenceId}
          selectedNodeCitationByEvidenceId={selectedNodeCitationByEvidenceId}
          locale={locale}
          getReliabilityLabel={getReliabilityLabel}
          localizeEvidenceContent={localizeEvidenceContent}
          onFocusEvidence={focusEvidence}
        />

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

        {false && (
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
            - {t("home.actions.traceUpstream")}
            <br />- {t("home.actions.compareChains")}
            <br />- {t("home.actions.viewCounterfactuals")}
            <br />- {t("home.actions.dragNotes")}
          </div>
        </div>
        )}
      </aside>

      <div
        className="main-canvas"
        style={{
          position: "absolute",
          top: "64px",
          left: 0,
          right: 0,
          bottom: 0,
          overflow: "hidden",
          transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel})`,
          transformOrigin: "0 0",
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
          padding: 10px 11px;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(248, 241, 229, 0.56));
          border: 1px solid var(--analyst-border);
          border-radius: 14px;
          margin-bottom: 10px;
          font-size: 0.68rem;
          color: var(--analyst-ink);
          line-height: 1.48;
          box-shadow: 0 8px 22px rgba(72, 48, 22, 0.06);
          transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
        }

        .compact-item:hover {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(249, 243, 232, 0.70));
          border-color: var(--analyst-border-strong);
          transform: translateY(-1px);
        }

        .compact-label {
          font-size: 0.58rem;
          color: var(--analyst-muted);
          text-transform: uppercase;
          letter-spacing: 0.12em;
          margin-bottom: 6px;
          font-weight: 700;
        }

        .panel-title {
          font-family: var(--font-display), Fraunces, serif;
          color: var(--analyst-ink);
          font-size: 1.06rem;
          font-weight: 650;
          letter-spacing: -0.015em;
          margin: 16px 0 12px;
          padding-bottom: 9px;
          border-bottom: 1px solid var(--analyst-border);
        }

        .query-brief {
          position: relative;
          overflow: hidden;
          background:
            radial-gradient(circle at 14% 0%, rgba(205, 83, 55, 0.13), transparent 30%),
            linear-gradient(180deg, rgba(255,255,255,0.86), rgba(247,239,225,0.70));
        }

        .query-brief::before {
          content: "";
          position: absolute;
          inset: 0;
          pointer-events: none;
          background-image:
            linear-gradient(rgba(90, 68, 42, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(90, 68, 42, 0.028) 1px, transparent 1px);
          background-size: 18px 18px;
          mask-image: linear-gradient(180deg, rgba(0,0,0,0.45), transparent 85%);
        }

        .query-brief-title {
          position: relative;
          margin-bottom: 9px;
          color: var(--analyst-ink);
          font-family: var(--font-display), Fraunces, serif;
          font-size: 1.05rem;
          font-weight: 650;
          letter-spacing: -0.02em;
        }

        .analyst-textarea,
        .analyst-input {
          position: relative;
          font-family: var(--font-sans), sans-serif;
          transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
        }

        .analyst-textarea:focus,
        .analyst-input:focus {
          border-color: rgba(49, 95, 131, 0.42) !important;
          box-shadow: 0 0 0 3px rgba(49, 95, 131, 0.10), inset 0 1px 0 rgba(255,255,255,0.78);
        }

        .sample-query-button {
          display: inline-flex;
          align-items: center;
          margin-top: 8px;
          max-width: 100%;
          border: 1px solid rgba(49, 95, 131, 0.24);
          border-radius: 8px;
          padding: 7px 10px;
          background: rgba(255,255,255,0.64);
          color: var(--analyst-ink);
          font-family: var(--font-sans), sans-serif;
          font-size: 0.68rem;
          line-height: 1.35;
          text-align: left;
          cursor: pointer;
          transition: border-color 0.16s ease, background 0.16s ease, transform 0.16s ease;
        }

        .sample-query-button:hover {
          border-color: rgba(49, 95, 131, 0.42);
          background: rgba(255,255,255,0.86);
          transform: translateY(-1px);
        }

        .analyst-input {
          width: 100%;
          box-sizing: border-box;
          margin-top: 5px;
          padding: 8px 10px;
          border: 1px solid var(--analyst-border);
          border-radius: 11px;
          outline: none;
          background: rgba(255,255,255,0.76);
          color: var(--analyst-ink);
          font-size: 0.68rem;
        }

        .advanced-toggle {
          position: relative;
          width: 100%;
          margin-top: 9px;
          padding: 8px 10px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border: 1px solid rgba(111, 85, 52, 0.14);
          border-radius: 12px;
          background: rgba(255, 251, 244, 0.70);
          color: var(--analyst-muted);
          font-size: 0.64rem;
          font-weight: 700;
          letter-spacing: 0.04em;
          cursor: pointer;
        }

        .advanced-toggle:hover {
          color: var(--analyst-blue);
          border-color: rgba(49, 95, 131, 0.24);
          background: rgba(255, 255, 255, 0.82);
        }

        .advanced-settings {
          position: relative;
          margin-top: 9px;
          padding: 9px;
          border: 1px dashed rgba(111, 85, 52, 0.18);
          border-radius: 13px;
          background: rgba(255, 248, 237, 0.54);
        }

        .provider-lock {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-top: 5px;
          padding: 8px 10px;
          border: 1px solid var(--analyst-border);
          border-radius: 11px;
          background: rgba(255, 255, 255, 0.68);
          color: var(--analyst-ink);
          font-size: 0.68rem;
          font-weight: 700;
        }

        .provider-lock span:last-child {
          color: var(--analyst-muted);
          font-size: 0.56rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .panel-toggle-button {
          position: absolute;
          top: 118px;
          z-index: 72;
          border: 1px solid rgba(101, 75, 42, 0.14);
          border-radius: 999px;
          padding: 5px 8px;
          background: rgba(255, 250, 239, 0.64);
          color: rgba(92, 74, 50, 0.68);
          cursor: pointer;
          font-size: 0.58rem;
          font-weight: 700;
          box-shadow: 0 8px 20px rgba(72, 48, 22, 0.08);
          backdrop-filter: blur(12px);
          transition:
            transform 0.16s ease,
            background 0.16s ease,
            color 0.16s ease,
            opacity 0.16s ease;
          opacity: 0.62;
        }

        .panel-toggle-left {
          left: 8px;
        }

        .panel-toggle-right {
          right: 8px;
        }

        .panel-toggle-button:hover {
          transform: translateY(-1px);
          background: rgba(255, 250, 239, 0.92);
          border-color: rgba(49, 95, 131, 0.28);
          color: var(--analyst-blue);
          opacity: 1;
        }

        .panel-embedded-toggle {
          position: absolute;
          top: 12px;
          right: 12px;
          z-index: 2;
          border: 1px solid rgba(101, 75, 42, 0.12);
          border-radius: 999px;
          padding: 4px 8px;
          background: rgba(255, 255, 255, 0.52);
          color: rgba(92, 74, 50, 0.58);
          cursor: pointer;
          font-size: 0.54rem;
          font-weight: 800;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          backdrop-filter: blur(10px);
        }

        .panel-embedded-toggle-right {
          right: auto;
          left: 12px;
        }

        .panel-embedded-toggle:hover {
          background: rgba(255, 255, 255, 0.86);
          border-color: rgba(49, 95, 131, 0.24);
          color: var(--analyst-blue);
        }

        @media (max-width: 720px) {
          .left-panel,
          .right-panel {
            width: min(86vw, 320px) !important;
          }

          .left-panel {
            z-index: 64 !important;
          }

          .right-panel {
            z-index: 56 !important;
          }

          .panel-embedded-toggle {
            min-height: 30px;
            min-width: 58px;
          }
        }

        .zoom-controls {
          position: absolute;
          top: 112px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 74;
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px;
          border: 1px solid rgba(101, 75, 42, 0.14);
          border-radius: 999px;
          background: rgba(255, 250, 239, 0.72);
          box-shadow: 0 10px 24px rgba(72, 48, 22, 0.08);
          backdrop-filter: blur(12px);
        }

        .zoom-controls button {
          min-width: 30px;
          height: 26px;
          border: 0;
          border-radius: 999px;
          background: transparent;
          color: rgba(92, 74, 50, 0.72);
          cursor: pointer;
          font-size: 0.62rem;
          font-weight: 800;
        }

        .zoom-controls button:hover:not(:disabled) {
          background: rgba(49, 95, 131, 0.10);
          color: var(--analyst-blue);
        }

        .zoom-controls button:disabled {
          opacity: 0.38;
          cursor: not-allowed;
        }

        .canvas-hint {
          position: absolute;
          top: 78px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 20;
          pointer-events: none;
          max-width: min(620px, calc(100vw - 48px));
          padding: 7px 12px;
          border: 1px solid rgba(101, 75, 42, 0.16);
          border-radius: 999px;
          background: rgba(255, 250, 239, 0.74);
          box-shadow: 0 10px 24px rgba(72, 48, 22, 0.08);
          color: var(--analyst-muted);
          font-size: 0.62rem;
          font-weight: 700;
          letter-spacing: 0.03em;
          text-align: center;
          backdrop-filter: blur(10px);
        }

        .command-chip-row {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 10px;
        }

        .command-chip {
          border: 1px solid rgba(255, 248, 235, 0.18);
          border-radius: 999px;
          padding: 4px 8px;
          background: rgba(255, 248, 235, 0.08);
          color: rgba(255, 248, 235, 0.78);
          font-size: 0.58rem;
          font-weight: 700;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .command-chip-strong {
          border-color: rgba(118, 166, 119, 0.36);
          background: rgba(118, 166, 119, 0.16);
          color: #dff1d6;
        }

        .command-chip-caution {
          border-color: rgba(209, 159, 75, 0.38);
          background: rgba(209, 159, 75, 0.15);
          color: #f4ddb4;
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
