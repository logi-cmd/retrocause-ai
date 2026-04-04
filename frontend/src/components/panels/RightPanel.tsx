"use client";

import React, { useState } from "react";
import NodeDetail from "./NodeDetail";
import EvidenceList from "./EvidenceList";
import ProbabilityBar from "./ProbabilityBar";
import AgentList from "./AgentList";
import {
  ChainNode,
  UpstreamNode,
  ChainEdgeEvidence,
  CounterfactualSummary,
  ProbabilityBar as ProbabilityBarType,
  Agent,
} from "@/data/mockData";
import { useI18n, type TranslationKey } from "@/lib/i18n";

type RightPanelTab = "query" | "detail" | "evidence";

interface RightPanelProps {
  query: string;
  statusNote: string;
  isDemoMode: boolean;
  demoTopic?: string | null;
  activeChainTitle: string;
  activeChainConfidence: number;
  hypothesisCount: number;
  selectedChainNode: ChainNode | undefined;
  upstreamCauses: UpstreamNode[];
  relevantEvidence: ChainEdgeEvidence[];
  counterfactual: CounterfactualSummary;
  probabilityBars: ProbabilityBarType[];
  agents: Agent[];
  onUpstreamSelect?: (nodeId: string) => void;
}

const TAB_KEYS: Record<RightPanelTab, TranslationKey> = {
  query: "rightPanel.tab.query",
  detail: "rightPanel.tab.detail",
  evidence: "rightPanel.tab.evidence",
};

const TAB_ICONS: Record<RightPanelTab, React.ReactNode> = {
  query: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16l2.879-2.879m0 0A3 3 0 1015.12 8.88a3 3 0 00-4.242 4.242zM21 21l-4.35-4.35" />
    </svg>
  ),
  detail: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  evidence: (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
};

function UpstreamCausesSection({
  upstreamCauses,
  onUpstreamSelect,
  t,
}: {
  upstreamCauses: UpstreamNode[];
  onUpstreamSelect?: (nodeId: string) => void;
  t: (key: TranslationKey) => string;
}) {
  if (upstreamCauses.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center px-4">
        <div className="w-12 h-12 rounded-full bg-[var(--paper-aged)] flex items-center justify-center mb-3">
          <svg className="w-6 h-6" style={{ color: 'var(--ink-400)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </div>
        <p className="text-sm font-medium mb-1" style={{ color: 'var(--ink-600)' }}>{t("rightPanel.noUpstream")}</p>
        <p className="text-xs" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.chainStart")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {upstreamCauses.map((up) => (
        <div
          key={up.id}
          className="flex items-center justify-between px-4 py-3 rounded-lg cursor-pointer transition-all duration-150"
          style={{
            background: 'var(--paper-white)',
            border: '1px solid var(--paper-border)',
          }}
          onClick={() => onUpstreamSelect?.(up.id)}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--paper-aged)';
            e.currentTarget.style.borderColor = 'var(--ink-300)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--paper-white)';
            e.currentTarget.style.borderColor = 'var(--paper-border)';
          }}
        >
          <div className="flex items-center gap-3">
            <span
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{
                backgroundColor:
                  up.type === "factor"
                    ? "var(--thread-success)"
                    : up.type === "outcome"
                      ? "var(--marker-blue)"
                      : "var(--ink-400)",
              }}
            />
            <div className="text-left">
              <span className="text-sm block" style={{ color: 'var(--ink-700)' }}>{up.label}</span>
              <span className="text-xs" style={{ color: 'var(--ink-400)' }}>
                {t("rightPanel.depth")} {up.depth} · {up.type === "factor" ? t("rightPanel.typeFactor") : up.type === "outcome" ? t("rightPanel.typeOutcome") : t("rightPanel.typeIntermediate")}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm font-mono font-semibold" style={{ color: 'var(--ink-700)' }}>
              {up.probability}%
            </span>
            <svg className="w-4 h-4" style={{ color: 'var(--ink-400)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function RightPanel({
  query,
  statusNote,
  isDemoMode,
  demoTopic,
  activeChainTitle,
  activeChainConfidence,
  hypothesisCount,
  selectedChainNode,
  upstreamCauses,
  relevantEvidence,
  counterfactual,
  probabilityBars,
  agents,
  onUpstreamSelect,
}: RightPanelProps) {
  const [activeTab, setActiveTab] = useState<RightPanelTab>("query");
  const { t } = useI18n();

  const modeLabel = isDemoMode
    ? t(demoTopic === "svb"
        ? "demo.topic.svb"
        : demoTopic === "stock"
          ? "demo.topic.stock"
          : demoTopic === "crisis"
            ? "demo.topic.crisis"
            : demoTopic === "rent"
              ? "demo.topic.rent"
              : "demo.topic.default" as TranslationKey)
    : t("rightPanel.liveAnalysis");

  return (
    <>
      <div className="shrink-0" style={{ 
        borderBottom: '1px solid rgba(160, 140, 110, 0.15)',
      }}>
        <div className="h-13 px-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 
              className="text-xs font-semibold uppercase tracking-widest"
              style={{ color: '#6b5a42', fontFamily: "'Caveat', cursive", fontSize: '1rem', letterSpacing: '0.05em' }}
            >
              {activeTab === "query" ? t("rightPanel.queryTitle") : selectedChainNode?.label ?? t("rightPanel.nodeDetail")}
            </h2>
          </div>
          <div className="flex items-center gap-1 p-1 rounded-lg" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
            {(Object.keys(TAB_KEYS) as RightPanelTab[]).map((tab) => {
              const isActive = activeTab === tab;
              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded transition-all duration-150"
                  style={{
                    background: isActive ? 'var(--marker-blue)' : 'transparent',
                    color: isActive ? '#ffffff' : '#8b7355',
                  }}
                >
                  {TAB_ICONS[tab]}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto scrollbar-thin">
        <div className="h-full transition-opacity duration-200 p-4">

          {activeTab === "query" && (
            <div className="space-y-4">
              <section className="rounded p-3 relative" style={{
                background: 'rgba(255, 255, 255, 0.5)',
                border: '1px solid rgba(160, 140, 110, 0.1)',
              }}>
                <div className="absolute top-0 left-0 w-1 h-full rounded-l" style={{ background: 'rgba(70, 130, 180, 0.3)' }} />
                <div className="flex items-center justify-between gap-3 mb-3 pl-2">
                  <div className="flex items-center gap-2">
                    <span 
                      className="text-[9px] py-1 px-2.5 rounded"
                      style={{
                        background: 'rgba(59, 110, 165, 0.1)',
                        color: 'var(--marker-blue)',
                        border: '1px solid rgba(59, 110, 165, 0.2)'
                      }}
                    >
                      {t("rightPanel.currentQuestion")}
                    </span>
                  </div>
                  <span 
                    className="text-[10px] px-2 py-0.5 rounded"
                    style={{
                      background: isDemoMode ? 'rgba(184, 134, 11, 0.08)' : 'rgba(59, 110, 165, 0.1)',
                      color: isDemoMode ? 'var(--thread-warning)' : 'var(--marker-blue)',
                      border: isDemoMode ? '1px solid rgba(184, 134, 11, 0.15)' : '1px solid rgba(59, 110, 165, 0.2)'
                    }}
                  >
                    {modeLabel}
                  </span>
                </div>
                <div className="pl-2">
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--ink-700)' }}>{query}</p>
                  <p className="mt-3 text-xs leading-relaxed" style={{ color: 'var(--ink-400)' }}>{statusNote}</p>
                </div>
              </section>

              <section className="rounded p-3 relative" style={{
                background: 'rgba(255, 255, 255, 0.5)',
                border: '1px solid rgba(160, 140, 110, 0.1)',
              }}>
                <div className="absolute top-0 left-0 w-1 h-full rounded-l" style={{ background: 'rgba(180, 80, 60, 0.3)' }} />
                <div className="flex items-center justify-between gap-3 mb-3 pl-2">
                  <div className="flex items-center gap-2">
                    <span 
                      className="text-[9px] py-1 px-2.5 rounded"
                      style={{
                        background: 'rgba(220, 38, 38, 0.08)',
                        color: 'var(--marker-red)',
                        border: '1px solid rgba(220, 38, 38, 0.15)'
                      }}
                    >
                      {t("rightPanel.mainChain")}
                    </span>
                  </div>
                  <span 
                    className="text-[9px] py-0.5 px-2 rounded font-mono"
                    style={{
                      background: 'rgba(220, 38, 38, 0.08)',
                      color: 'var(--marker-red)',
                      border: '1px solid rgba(220, 38, 38, 0.15)'
                    }}
                  >
                    {Math.round(activeChainConfidence * 100)}%
                  </span>
                </div>
                <div className="pl-2">
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--ink-700)' }}>{activeChainTitle}</p>
                  <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-md px-2 py-2.5" style={{ background: 'var(--paper-aged)' }}>
                      <div className="text-base font-mono font-semibold" style={{ color: 'var(--ink-700)' }}>{hypothesisCount}</div>
                      <div className="text-[10px] uppercase tracking-wider mt-0.5" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.statHypotheses")}</div>
                    </div>
                    <div className="rounded-md px-2 py-2.5" style={{ background: 'var(--paper-aged)' }}>
                      <div className="text-base font-mono font-semibold" style={{ color: 'var(--ink-700)' }}>{upstreamCauses.length}</div>
                      <div className="text-[10px] uppercase tracking-wider mt-0.5" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.statUpstream")}</div>
                    </div>
                    <div className="rounded-md px-2 py-2.5" style={{ background: 'var(--paper-aged)' }}>
                      <div className="text-base font-mono font-semibold" style={{ color: 'var(--ink-700)' }}>{relevantEvidence.length}</div>
                      <div className="text-[10px] uppercase tracking-wider mt-0.5" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.statEvidence")}</div>
                    </div>
                  </div>
                </div>
              </section>

              <section className="rounded-lg p-4" style={{
                background: 'var(--paper-aged)',
                border: '1px dashed var(--paper-border)'
              }}>
                <div className="flex items-center gap-2 mb-3">
                  <svg className="w-3.5 h-3.5" style={{ color: 'var(--ink-400)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--ink-500)' }}>{t("rightPanel.investigationTips")}</span>
                </div>
                <ul className="space-y-2.5 text-xs leading-relaxed" style={{ color: 'var(--ink-600)' }}>
                  <li className="flex items-start gap-2">
                    <span style={{ color: 'var(--marker-blue)' }}>→</span>
                    <span>{t("rightPanel.tip1")}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span style={{ color: 'var(--marker-blue)' }}>→</span>
                    <span>{t("rightPanel.tip2")}</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span style={{ color: 'var(--marker-red)' }}>!</span>
                    <span>{t("rightPanel.tip3")}</span>
                  </li>
                </ul>
              </section>
            </div>
          )}

          {activeTab === "detail" && (
            <div className="space-y-4">
              {selectedChainNode ? (
                <>
                  <section>
                    <div className="flex items-center gap-2 mb-3">
                      <span 
                        className="text-[9px] py-1 px-2.5 rounded"
                        style={{
                          background: 'rgba(59, 110, 165, 0.1)',
                          color: 'var(--marker-blue)',
                          border: '1px solid rgba(59, 110, 165, 0.2)'
                        }}
                      >
                        {t("rightPanel.basicInfo")}
                      </span>
                      <span 
                        className="text-[9px] py-0.5 px-2 rounded"
                        style={{
                          background: `${getTypeConfig(t)[selectedChainNode.type].color}10`,
                          color: getTypeConfig(t)[selectedChainNode.type].color,
                          border: `1px solid ${getTypeConfig(t)[selectedChainNode.type].color}25`
                        }}
                      >
                        {getTypeConfig(t)[selectedChainNode.type].label}
                      </span>
                    </div>
                    <NodeDetail node={selectedChainNode} />
                  </section>

                  <section>
                    <div className="flex items-center gap-2 mb-3">
                      <span 
                        className="text-[9px] py-1 px-2.5 rounded"
                        style={{
                          background: 'rgba(59, 110, 165, 0.1)',
                          color: 'var(--marker-blue)',
                          border: '1px solid rgba(59, 110, 165, 0.2)'
                        }}
                      >
                        {t("rightPanel.upstreamCauses")}
                      </span>
                      {upstreamCauses.length > 0 && (
                        <span 
                          className="text-[9px] py-0.5 px-2 rounded"
                          style={{
                            background: 'rgba(220, 38, 38, 0.08)',
                            color: 'var(--marker-red)',
                            border: '1px solid rgba(220, 38, 38, 0.15)'
                          }}
                        >
                          {upstreamCauses.length}
                        </span>
                      )}
                    </div>
                    <UpstreamCausesSection
                      upstreamCauses={upstreamCauses}
                      onUpstreamSelect={onUpstreamSelect}
                      t={t}
                    />
                  </section>

                  <section>
                    <div className="flex items-center gap-2 mb-3">
                      <span 
                        className="text-[9px] py-1 px-2.5 rounded"
                        style={{
                          background: 'rgba(59, 110, 165, 0.1)',
                          color: 'var(--marker-blue)',
                          border: '1px solid rgba(59, 110, 165, 0.2)'
                        }}
                      >
                        {t("rightPanel.counterfactual")}
                      </span>
                      <span 
                        className="text-[9px] py-0.5 px-2 rounded"
                        style={{
                          background: 'rgba(184, 134, 11, 0.08)',
                          color: 'var(--thread-warning)',
                          border: '1px solid rgba(184, 134, 11, 0.15)'
                        }}
                      >
                        {t("rightPanel.whatIf")}
                      </span>
                    </div>
                    <div className="rounded-lg p-4 relative" style={{
                      background: 'var(--paper-white)',
                      border: '1px solid var(--paper-border)'
                    }}>
                      <div className="absolute top-0 left-0 w-1 h-full rounded-l-lg" style={{ background: 'var(--thread-warning)' }} />
                      <div className="space-y-3 pl-2">
                        <div className="flex items-start gap-2">
                           <span className="text-xs shrink-0 w-16 pt-0.5" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.intervention")}</span>
                           <span className="text-sm" style={{ color: 'var(--ink-700)' }}>{counterfactual.intervention}</span>
                         </div>
                         <div className="flex items-start gap-2">
                           <span className="text-xs shrink-0 w-16 pt-0.5" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.outcomeChange")}</span>
                           <span className="text-sm" style={{ color: 'var(--ink-700)' }}>{counterfactual.outcomeChange}</span>
                         </div>
                         <div className="flex items-start gap-2">
                           <span className="text-xs shrink-0 w-16 pt-0.5" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.probShift")}</span>
                          <span
                            className="text-sm font-mono font-semibold"
                            style={{
                              color:
                                counterfactual.probabilityShift < 0
                                  ? "var(--thread-success)"
                                  : "var(--marker-red)",
                            }}
                          >
                            {counterfactual.probabilityShift > 0 ? "+" : ""}
                            {counterfactual.probabilityShift}%
                          </span>
                        </div>
                        <p className="text-xs leading-relaxed pt-2" style={{ 
                          color: 'var(--ink-500)',
                          borderTop: '1px solid var(--paper-border)'
                        }}>
                          {counterfactual.description}
                        </p>
                      </div>
                    </div>
                  </section>

                  <section>
                    <div className="flex items-center gap-2 mb-3">
                      <span 
                        className="text-[9px] py-1 px-2.5 rounded"
                        style={{
                          background: 'rgba(59, 110, 165, 0.1)',
                          color: 'var(--marker-blue)',
                          border: '1px solid rgba(59, 110, 165, 0.2)'
                        }}
                      >
                        {t("rightPanel.agents")}
                      </span>
                    </div>
                    <AgentList agents={agents} />
                  </section>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="relative mb-6">
                    <div className="w-20 h-20 rounded-full bg-[var(--paper-aged)] flex items-center justify-center">
                      <svg className="w-10 h-10" style={{ color: 'var(--ink-400)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                      </svg>
                    </div>
                    <div 
                      className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full"
                      style={{ background: 'var(--marker-red)', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}
                    />
                  </div>
                  <p className="text-sm font-medium mb-2" style={{ color: 'var(--ink-600)' }}>{t("rightPanel.selectNode")}</p>
                  <p className="text-xs max-w-[200px] leading-relaxed" style={{ color: 'var(--ink-400)' }}>
                    {t("rightPanel.selectNodeHint")}
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "evidence" && (
            <div className="space-y-4">
              {relevantEvidence.length > 0 && (
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <span 
                      className="text-[9px] py-1 px-2.5 rounded"
                      style={{
                        background: 'rgba(34, 197, 94, 0.08)',
                        color: 'var(--thread-success)',
                        border: '1px solid rgba(34, 197, 94, 0.15)'
                      }}
                    >
                      {t("rightPanel.supportingEvidence")}
                    </span>
                    <span 
                      className="text-[9px] py-0.5 px-2 rounded"
                      style={{
                        background: 'rgba(34, 197, 94, 0.08)',
                        color: 'var(--thread-success)',
                        border: '1px solid rgba(34, 197, 94, 0.15)'
                      }}
                    >
                      {relevantEvidence.length} {t("rightPanel.items")}
                    </span>
                  </div>
                  <EvidenceList evidences={relevantEvidence} />
                </section>
              )}

              <section>
                <div className="flex items-center gap-2 mb-3">
                  <span 
                    className="text-[9px] py-1 px-2.5 rounded"
                    style={{
                      background: 'rgba(59, 110, 165, 0.1)',
                      color: 'var(--marker-blue)',
                      border: '1px solid rgba(59, 110, 165, 0.2)'
                    }}
                  >
                    {t("rightPanel.probabilityDistribution")}
                  </span>
                </div>
                <ProbabilityBar bars={probabilityBars} />
              </section>

              <div className="rounded-lg p-4 relative" style={{
                background: 'var(--paper-white)',
                border: '1px solid var(--paper-border)'
              }}>
                <div className="absolute top-0 left-0 w-1 h-full rounded-l-lg" style={{ background: 'var(--ink-400)' }} />
                <div className="flex items-center justify-center gap-6 py-2 pl-2">
                  <div className="text-center">
                    <span className="text-lg font-mono font-bold" style={{ color: 'var(--ink-700)' }}>
                      {selectedChainNode?.probability ?? "--"}
                      {selectedChainNode ? "%" : ""}
                    </span>
                    <span className="text-[10px] block mt-0.5 uppercase tracking-wider" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.nodeProbability")}</span>
                  </div>
                  <div className="w-px h-10" style={{ background: 'var(--paper-border)' }} />
                  <div className="text-center">
                    <span className="text-lg font-mono font-bold" style={{ color: 'var(--ink-700)' }}>{relevantEvidence.length}</span>
                    <span className="text-[10px] block mt-0.5 uppercase tracking-wider" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.evidenceItems")}</span>
                  </div>
                  <div className="w-px h-10" style={{ background: 'var(--paper-border)' }} />
                  <div className="text-center">
                    <span className="text-lg font-mono font-bold" style={{ color: 'var(--ink-700)' }}>{upstreamCauses.length}</span>
                    <span className="text-[10px] block mt-0.5 uppercase tracking-wider" style={{ color: 'var(--ink-400)' }}>{t("rightPanel.upstreamNodes")}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function getTypeConfig(t: (key: TranslationKey) => string): Record<string, { label: string; color: string; description: string }> {
  return {
    outcome: { 
      label: t("rightPanel.type.outcome"), 
      color: "var(--marker-blue)",
      description: t("rightPanel.type.outcomeDesc")
    },
    factor: { 
      label: t("rightPanel.type.factor"), 
      color: "var(--thread-success)",
      description: t("rightPanel.type.factorDesc")
    },
    intermediate: { 
      label: t("rightPanel.type.intermediate"), 
      color: "#8b5cf6",
      description: t("rightPanel.type.intermediateDesc")
    },
  };
}
