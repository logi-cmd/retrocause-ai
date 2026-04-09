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
      title: chain.label,
      outcomeLabel: chain.nodes[chain.nodes.length - 1]?.label ?? chain.label,
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
      label: node.label,
      type: mapNodeType(node.type),
      probability: Math.round(node.probability * 100),
      depth: node.depth,
      description: {
        brief: node.description,
        detail: node.description,
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
            label: candidate.label,
            probability: Math.round(candidate.probability * 100),
            depth: candidate.depth,
            type: mapNodeType(candidate.type),
          })),
      ])
    ),
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
  const [analysisMode, setAnalysisMode] = useState<{ isDemo: boolean; demoTopic: string | null; loading: boolean }>({
    isDemo: true,
    demoTopic: null,
    loading: false,
  });

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
    setActiveChain(localizedDemo.primaryChain);
    setAvailableChains([]);
    setRecommendedChainId(null);
    setEvidencePool([]);
    setPipelineEval(null);
    setUncertaintyReport(null);
    setSelectedNodeId(null);
    setPanOffset({ x: 0, y: 0 });
  }, [localizedDemo]);

  useEffect(() => {
    let cancelled = false;
    fetch("http://127.0.0.1:8000/api/providers")
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
  const connectedNodeIds = selectedNodeId
    ? new Set(
        mockPrimaryChain.edges.flatMap((edge) =>
          edge.source === selectedNodeId || edge.target === selectedNodeId
            ? [edge.source, edge.target]
            : []
        )
      )
    : new Set<string>();
  if (selectedNodeId) {
    connectedNodeIds.add(selectedNodeId);
  }
  const primaryChainTitle = mockPrimaryChain.metadata.title;
  const activeApiChain = useMemo(
    () => availableChains.find((chain) => chain.chain_id === mockPrimaryChain.metadata.id) ?? null,
    [availableChains, mockPrimaryChain.metadata.id]
  );
  const selectedApiNode = activeApiChain?.nodes.find((node) => node.id === selectedNodeId) ?? null;
  const selectedApiEdges = useMemo(
    () =>
      activeApiChain?.edges.filter(
        (edge) => edge.source === selectedNodeId || edge.target === selectedNodeId
      ) ?? [],
    [activeApiChain, selectedNodeId]
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
  const selectedEdgeIds = selectedNodeId
    ? new Set(
        mockPrimaryChain.edges
          .filter((edge) => edge.source === selectedNodeId || edge.target === selectedNodeId)
          .map((edge) => edge.id)
      )
    : new Set<string>();
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
    if (selectedNodeEvidenceIds.length > 0) {
      return selectedNodeEvidenceIds.includes(item.id);
    }

    if (activeChainEvidenceIds.size > 0) {
      return activeChainEvidenceIds.has(item.id);
    }

    return false;
  });
  const evidenceBase = relatedEvidence.length > 0 ? relatedEvidence : evidencePool;
  const getReliabilityLabel = (reliability: string) => {
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
  };
  const visibleEvidence = evidenceBase.filter((item) => {
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

    return true;
  });
  const chainCompareItems = useMemo(
    () =>
      availableChains.slice(0, 4).map((chain) => ({
        chain_id: chain.chain_id,
        label: chain.label,
        probability: Math.round(chain.probability * 100),
        supportCount: chain.supporting_evidence_ids.length,
        refuteCount: chain.refuting_evidence_ids.length,
        edgeCount: chain.edges.length,
        nodeCount: chain.nodes.length,
      })),
    [availableChains]
  );

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
  }, []);

  const selectedNote = notes.find((n) => n.id === selectedNodeId);

  const runAnalysis = useCallback(async () => {
    const query = currentQuery.trim();
    if (!query) {
      return;
    }

    setAnalysisMode((current) => ({ ...current, loading: true }));
    setStatusNote(locale === "en" ? "Running live analysis…" : "正在执行真实分析…");
    setLastQuery(query);

    try {
      const body: Record<string, unknown> = { query, model: selectedModel, api_key: apiKey };
      if (selectedExplicitModel) {
        body.explicit_model = selectedExplicitModel;
      }
      const response = await fetch("http://127.0.0.1:8000/api/analyze/v2", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = (await response.json()) as AnalyzeResponseV2;
      const recommended = payload.chains.find((chain) => chain.chain_id === payload.recommended_chain_id) ?? payload.chains[0];

      if (!recommended) {
        throw new Error("No chains returned");
      }

      setAvailableChains(payload.chains);
      setRecommendedChainId(payload.recommended_chain_id);
      setEvidencePool(payload.evidences);
      setPipelineEval(payload.evaluation ?? null);
      setUncertaintyReport(payload.uncertainty_report ?? null);
      setActiveChain(toLocalChain(recommended, locale, payload.evidences));
      setEvidenceSourceFilter("all");
      setEvidenceStanceFilter("all");
      setEvidenceConfidenceFilter("all");

      setAnalysisMode({
        isDemo: payload.is_demo,
        demoTopic: payload.demo_topic,
        loading: false,
      });
      setSelectedNodeId(null);
      setPanOffset({ x: 0, y: 0 });
      if (payload.is_demo && payload.error) {
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
    } catch {
      setActiveChain(localizedDemo.primaryChain);
      setAvailableChains([]);
      setRecommendedChainId(null);
      setEvidencePool([]);
      setPipelineEval(null);
      setUncertaintyReport(null);
      setAnalysisMode({ isDemo: true, demoTopic: null, loading: false });
      setSelectedNodeId(null);
      setPanOffset({ x: 0, y: 0 });
      setStatusNote(
        locale === "en"
          ? "Live analysis failed; showing local demo board instead."
          : "真实分析失败，当前回退到本地 demo 证据墙。"
      );
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
                : analysisMode.isDemo
                  ? t("status.demoMode")
                  : t("header.status.live")}
            </span>
          </div>
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
                  <span>{chain.label}</span>
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
              <div
                key={`${chain.chain_id}-compare`}
                style={{
                  marginTop: "6px",
                  paddingTop: "6px",
                  borderTop: "1px dashed rgba(160,140,110,0.18)",
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
              </div>
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

        <div className="compact-item" style={{ background: analysisMode.isDemo ? "rgba(255,248,240,0.9)" : "rgba(240,248,244,0.9)" }}>
          <div className="compact-label">{analysisMode.isDemo ? t("status.demoMode") : t("header.status.live")}</div>
          <div style={{ fontSize: "0.65rem", lineHeight: 1.5 }}>{statusNote || (analysisMode.isDemo ? t("demo.banner") : t("status.liveAnalysis"))}</div>
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
              <div key={`${edge.id}-edge`} style={{ marginBottom: "10px", paddingBottom: "10px", borderBottom: "1px dashed rgba(160,140,110,0.18)" }}>
                <div style={{ fontSize: "0.62rem", color: "#5c4a32", lineHeight: 1.4 }}>
                  <strong>{edge.source}</strong> → <strong>{edge.target}</strong>
                </div>
                <div style={{ fontSize: "0.56rem", color: edge.evidence_conflict && edge.evidence_conflict !== "none" ? "#a0503c" : "#8b7355", marginTop: "3px" }}>
                  {locale === "en" ? "Conflict" : "冲突"}: {edge.evidence_conflict ?? "none"}
                </div>
                {(edge.citation_spans?.[0]?.quoted_text) && (
                  <div style={{ fontSize: "0.58rem", color: "#6b5a42", marginTop: "6px", lineHeight: 1.5, fontStyle: "italic" }}>
                    “{edge.citation_spans[0].quoted_text}”
                  </div>
                )}
              </div>
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
          </div>
          {visibleEvidence.length > 0 ? (
            visibleEvidence.map((item) => (
              <div key={item.id} style={{ marginBottom: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px", fontSize: "0.56rem", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  <span style={{ color: item.is_supporting ? "#5a7a52" : "#a0503c" }}>
                    {item.is_supporting ? t("home.evidence.supporting") : t("home.evidence.refuting")}
                  </span>
                  <span style={{ color: "#8b7355" }}>{getReliabilityLabel(item.reliability)}</span>
                </div>
                <div style={{ fontSize: "0.65rem", color: "#5c4a32", lineHeight: 1.45 }}>{item.content}</div>
                {selectedNodeCitationByEvidenceId.get(item.id)?.quoted_text && (
                  <div style={{ fontSize: "0.58rem", color: "#6b5a42", lineHeight: 1.45, marginTop: "4px", fontStyle: "italic" }}>
                    “{selectedNodeCitationByEvidenceId.get(item.id)?.quoted_text}”
                  </div>
                )}
                <div style={{ fontSize: "0.56rem", color: "#8b7355", marginTop: "2px" }}>{item.source}</div>
              </div>
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
