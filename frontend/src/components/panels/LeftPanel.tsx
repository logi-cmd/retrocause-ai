"use client";

import React, { useState } from "react";
import QueryInput from "./QueryInput";
import Filters from "./Filters";
import { Hypothesis, CausalChain } from "@/data/mockData";
import { useI18n, type TranslationKey } from "@/lib/i18n";

interface LeftPanelProps {
  hypotheses: Hypothesis[];
  selectedHypothesisId?: string;
  onHypothesisSelect?: (hypothesis: Hypothesis) => void;
  onQuerySubmit?: (query: string) => void;
  graphOverview?: React.ReactNode;
  chain?: CausalChain;
}

function getStrengthColor(strength: number): string {
  if (strength >= 0.7) return "var(--thread-success)";
  if (strength >= 0.4) return "var(--thread-warning)";
  return "var(--marker-red)";
}

function getStrengthLabel(strength: number, t: (key: TranslationKey) => string): string {
  if (strength >= 0.7) return t("strength.strong");
  if (strength >= 0.4) return t("strength.medium");
  return t("strength.weak");
}

function HypothesisCard({ 
  h, 
  isSelected, 
  onSelect,
  compact = false,
  t
}: { 
  h: Hypothesis; 
  isSelected: boolean; 
  onSelect?: (h: Hypothesis) => void;
  compact?: boolean;
  t: (key: TranslationKey) => string;
}) {
  const strengthColor = getStrengthColor(h.causalStrength);
  
  if (compact) {
    return (
      <div
        className={`
          relative p-2 rounded cursor-pointer transition-all duration-200
          ${isSelected 
            ? "bg-[var(--marker-blue)]/8 shadow-sm ring-1 ring-[var(--marker-blue)]/30" 
            : "bg-[var(--paper-cream)] hover:bg-[var(--paper-aged)] hover:shadow-sm"}
        `}
        style={{
          border: isSelected ? '1px solid var(--marker-blue)/30' : '1px solid var(--paper-border)',
        }}
        onClick={() => onSelect?.(h)}
      >
        {isSelected && (
          <div className="absolute -left-1 top-2 w-1 h-4 bg-[var(--marker-blue)] rounded-r" />
        )}
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-semibold truncate max-w-[80px] text-[var(--ink-700)]">
            {h.title}
          </span>
          <span 
            className="text-[9px] font-mono px-1 py-0.5 rounded"
            style={{ 
              backgroundColor: `${strengthColor}15`,
              color: strengthColor 
            }}
          >
            {h.probability}%
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        relative p-3 rounded-lg cursor-pointer transition-all duration-200
        ${isSelected 
          ? "bg-[var(--marker-blue)]/8 shadow-md ring-1 ring-[var(--marker-blue)]/30" 
          : "bg-[var(--paper-white)] hover:shadow-sm"}
      `}
      style={{
        border: isSelected ? '1px solid var(--marker-blue)/30' : '1px solid var(--paper-border)',
        boxShadow: isSelected 
          ? 'var(--card-lift-selected)' 
          : 'var(--paper-shadow)',
      }}
      onClick={() => onSelect?.(h)}
    >
      {isSelected && (
        <div className="absolute -left-1 top-3 w-1.5 h-6 bg-[var(--marker-blue)] rounded-r" />
      )}
      
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs font-bold leading-tight text-[var(--ink-700)]">
          {h.title}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          <span 
            className="text-[9px] font-mono px-1.5 py-0.5 rounded"
            style={{ 
              backgroundColor: `${strengthColor}15`,
              color: strengthColor 
            }}
          >
            {getStrengthLabel(h.causalStrength, t)}{t("strength.causal")}
          </span>
        </div>
      </div>
      
      <p className="text-[10px] leading-relaxed mb-2 line-clamp-2 text-[var(--ink-500)]">
        {h.description}
      </p>
      
      <div className="flex items-center gap-2 text-[9px] text-[var(--ink-400)]">
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {h.evidenceCount}{t("leftPanel.evidence")}
        </span>
        <span className="font-mono text-[var(--marker-blue)]">
          {h.probability}%
        </span>
      </div>
    </div>
  );
}

function ClusterHeader ({ 
  label, 
  count, 
  variant = "default" 
}: { 
  label: string;
  count?: number;
  variant?: "default" | "warning" | "info";
}) {
  const colorClass = variant === "warning" 
    ? "var(--marker-red)" 
    : variant === "info" 
      ? "var(--marker-blue)" 
      : "var(--ink-400)";
  
  return (
    <div className="flex items-center gap-2 mb-2">
      <div className="w-3 h-px" style={{ backgroundColor: colorClass }} />
      <span className="text-[9px] uppercase tracking-widest font-semibold" style={{ color: colorClass }}>
        {label}
      </span>
      {count !== undefined && (
        <span className="text-[9px] font-mono text-[var(--ink-400)]">
          {count}
        </span>
      )}
    </div>
  );
}

function EvidenceCluster({ 
  title, 
  items, 
  weight = "normal" 
}: { 
  title: string;
  items: Array<{ label: string; value: string; type?: "support" | "challenge" | "neutral" }>;
  weight?: "light" | "normal" | "heavy";
}) {
  const isHeavy = weight === "heavy";
  const isLight = weight === "light";
  
  return (
    <div 
      className="relative rounded-lg p-3"
      style={{
        background: isHeavy 
          ? 'var(--marker-blue)/5' 
          : isLight 
            ? 'var(--paper-aged)' 
            : 'var(--paper-cream)',
        border: isHeavy 
          ? '1px solid var(--marker-blue)/20' 
          : isLight 
            ? '1px dashed var(--paper-border)' 
            : '1px solid var(--paper-border)',
      }}
    >
      {isHeavy && (
        <div className="absolute -top-px left-4 right-4 h-px" style={{
          background: 'linear-gradient(to right, transparent, var(--marker-blue)/30, transparent)'
        }} />
      )}
      
      <div className="text-[9px] uppercase tracking-wider mb-2 font-medium text-[var(--ink-500)]">
        {title}
      </div>
      
      <div className="space-y-1.5">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-2">
            <div 
              className="w-2 h-2 rounded-sm mt-0.5 flex-shrink-0"
              style={{
                backgroundColor: item.type === "support" ? "var(--thread-success)" : 
                  item.type === "challenge" ? "var(--marker-red)" : 
                  "var(--ink-400)"
              }}
            />
            <div className="flex-1 min-w-0">
              <span className="text-[9px] font-medium truncate block text-[var(--ink-700)]">
                {item.label}
              </span>
              <span className="text-[9px] truncate block text-[var(--ink-500)]">
                {item.value}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChainTrail({ chain, t }: { chain?: CausalChain; t: (key: TranslationKey) => string }) {
  if (!chain) return null;
  
  return (
    <div className="relative">
      <div className="absolute left-[7px] top-2 bottom-4 w-px" style={{
        background: 'linear-gradient(to bottom, var(--marker-blue)/40, var(--ink-300)/20, transparent)'
      }} />
      
      <div className="space-y-2">
        {chain.nodes.slice(0, 4).map((node) => {
          const isOutcome = node.type === "outcome";
          const isFactor = node.type === "factor";
          const borderColor = isOutcome
            ? "var(--marker-blue)"
            : isFactor
              ? "var(--thread-success)"
              : "var(--ink-400)";
          
          return (
            <div key={node.id} className="relative flex items-start gap-2 pl-4">
              <div 
                className="absolute left-0 top-1 w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center"
                style={{ 
                  borderColor: borderColor,
                  backgroundColor: 'var(--paper-white)',
                }}
              >
                <div 
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: borderColor }}
                />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span 
                    className="text-[9px] font-bold"
                    style={{ color: borderColor }}
                  >
                    {node.probability}%
                  </span>
                  <span className="text-[9px] font-semibold truncate text-[var(--ink-700)]">
                    {node.label}
                  </span>
                </div>
                {node.description.brief && (
                  <p className="text-[8px] leading-relaxed line-clamp-1 text-[var(--ink-400)]">
                    {node.description.brief}
                  </p>
                )}
              </div>
            </div>
          );
        })}
        
        {chain.nodes.length > 4 && (
          <div className="relative flex items-center gap-2 pl-4">
            <div 
              className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full border border-dashed"
              style={{ borderColor: 'var(--ink-400)' }}
            />
            <span className="text-[8px] text-[var(--ink-400)]">
              +{chain.nodes.length - 4} {t("leftPanel.moreNodes")}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function LeftPanel({
  hypotheses,
  selectedHypothesisId,
  onHypothesisSelect,
  onQuerySubmit,
  graphOverview,
  chain,
}: LeftPanelProps) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div 
        className="px-3 pt-3 pb-2" 
        style={{ 
          borderBottom: '1px solid rgba(160, 140, 110, 0.15)',
        }}
      >
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-sm bg-[var(--marker-blue)]/10 flex items-center justify-center">
              <svg className="w-2.5 h-2.5 text-[var(--marker-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <span 
              className="text-[10px] uppercase tracking-widest font-bold"
              style={{ color: '#6b5a42' }}
            >
              {t("leftPanel.caseFile")}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] font-mono" style={{ color: '#8b7355' }}>
              {hypotheses.length}{t("leftPanel.hypotheses")}
            </span>
          </div>
        </div>
        <QueryInput 
          value={query}
          onChange={setQuery}
          onSubmit={() => onQuerySubmit?.(query)} 
        />
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 scrollbar-thin">
        
        <div>
          <ClusterHeader label={t("leftPanel.competingHypotheses")} count={hypotheses.length} />
          
          {hypotheses.filter(h => h.id === selectedHypothesisId).map(h => (
            <div key={h.id} className="mb-2">
              <HypothesisCard h={h} isSelected={true} onSelect={onHypothesisSelect} t={t} />
            </div>
          ))}
          
          {hypotheses.filter(h => h.id !== selectedHypothesisId).length > 0 && (
            <div className="grid grid-cols-2 gap-2">
              {hypotheses
                .filter(h => h.id !== selectedHypothesisId)
                .slice(0, 4)
                .map(h => (
                  <HypothesisCard 
                    key={h.id} 
                    h={h} 
                    isSelected={false} 
                    onSelect={onHypothesisSelect}
                    compact
                    t={t}
                  />
                ))}
            </div>
          )}
        </div>

        {chain && (
          <div className="relative">
            <div className="absolute -left-2 top-0 bottom-0 w-px" style={{
              background: 'linear-gradient(to bottom, rgba(160, 140, 110, 0.2), transparent)'
            }} />
            <div className="pl-2">
              <ClusterHeader label={t("leftPanel.causalChain")} variant="info" />
              <ChainTrail chain={chain} t={t} />
            </div>
          </div>
        )}

        {chain && (
          <div className="space-y-2">
            <ClusterHeader label={t("leftPanel.keyEvidence")} variant="warning" />
            
            <EvidenceCluster 
              title={t("leftPanel.strongSupport")}
              weight="heavy"
              items={chain.edges
                .filter(e => e.type === "strong" && e.evidence.length > 0)
                .slice(0, 2)
                .flatMap(e => e.evidence.slice(0, 1))
                .map(ev => ({
                  label: ev.evidenceId,
                  value: ev.content.length > 40 ? ev.content.slice(0, 40) + "…" : ev.content,
                  type: "support" as const
                }))}
            />
          </div>
        )}

        {graphOverview && (
          <div className="pt-2 border-t" style={{ borderColor: 'rgba(160, 140, 110, 0.15)' }}>
            {graphOverview}
          </div>
        )}
        
      </div>

      <div className="px-3 py-2 border-t" style={{ borderColor: 'rgba(160, 140, 110, 0.15)', background: 'rgba(255, 255, 255, 0.3)' }}>
        <Filters />
      </div>
    </div>
  );
}
