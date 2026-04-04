"use client";

import React from "react";
import { ChainEdgeEvidence, Evidence, EvidenceReliability } from "@/data/mockData";
import { useI18n } from "@/lib/i18n";

type EvidenceItem =
  | (ChainEdgeEvidence & { _kind: "chain" })
  | (Evidence & { _kind: "legacy" });

interface EvidenceListProps {
  evidences: ChainEdgeEvidence[] | Evidence[];
}

function isChainEvidence(e: ChainEdgeEvidence | Evidence): e is ChainEdgeEvidence {
  return "causalWeight" in e && "reliability" in e && !("source" in e);
}

function isLegacyEvidence(e: ChainEdgeEvidence | Evidence): e is Evidence {
  return "source" in e && "content" in e;
}

function EvidenceCard({ 
  e,
  t,
}: { 
  e: ChainEdgeEvidence | Evidence;
  t: (key: Parameters<ReturnType<typeof useI18n>['t']>[0]) => string;
}) {
  const content = e.content;
  const reliability: EvidenceReliability =
    isChainEvidence(e) ? e.reliability : (e as Evidence).reliability;
  const weight = isChainEvidence(e) ? e.causalWeight : (e as Evidence).causalWeight;
  const reliabilityConfig: Record<EvidenceReliability, { color: string; label: string; bg: string }> = {
    strong: { color: "var(--thread-success)", label: t("home.evidence.strong"), bg: "rgba(45, 138, 95, 0.08)" },
    medium: { color: "var(--ink-400)", label: t("home.evidence.medium"), bg: "rgba(138, 138, 138, 0.08)" },
    weak: { color: "var(--marker-red)", label: t("home.evidence.weak"), bg: "rgba(201, 74, 74, 0.08)" },
  };
  const config = reliabilityConfig[reliability];

  return (
    <div
      className="p-3 rounded-md relative overflow-hidden"
      style={{ 
        borderLeft: `3px solid ${config.color}`,
        backgroundColor: config.bg
      }}
    >
      <p className="text-sm mb-2 text-[var(--ink-700)] leading-relaxed">{content}</p>
      <div className="flex items-center gap-3">
        <span 
          className="text-xs font-medium px-1.5 py-0.5 rounded"
          style={{ 
            backgroundColor: `${config.color}20`,
            color: config.color 
          }}
        >
          {reliability === "strong" ? t("strength.strong") : reliability === "medium" ? t("strength.medium") : t("strength.weak")}
        </span>
        <span className="text-xs text-[var(--ink-400)] font-mono">
          {t("home.table.weight")} {Math.round(weight * 100)}%
        </span>
      </div>
    </div>
  );
}

export default function EvidenceList({ evidences }: EvidenceListProps) {
  const { t } = useI18n();
  const reliabilityConfig: Record<EvidenceReliability, { color: string; label: string; bg: string }> = {
    strong: { color: "var(--thread-success)", label: t("home.evidence.strong"), bg: "rgba(45, 138, 95, 0.08)" },
    medium: { color: "var(--ink-400)", label: t("home.evidence.medium"), bg: "rgba(138, 138, 138, 0.08)" },
    weak: { color: "var(--marker-red)", label: t("home.evidence.weak"), bg: "rgba(201, 74, 74, 0.08)" },
  };
  if (evidences.length === 0) {
    return (
      <div className="p-4 rounded-lg bg-[var(--paper-white)] border border-[var(--paper-border)] shadow-[var(--paper-shadow)]">
        <h4 className="text-xs uppercase tracking-widest text-[var(--ink-400)] mb-3 font-semibold">
          {t("home.evidence.related")} (0)
        </h4>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-10 h-10 rounded-full bg-[var(--paper-aged)] flex items-center justify-center mb-3">
            <svg className="w-5 h-5 text-[var(--ink-400)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-sm text-[var(--ink-500)]">{t("home.evidence.empty")}</p>
        </div>
      </div>
    );
  }

  // Group evidences by reliability
  const grouped: Record<EvidenceReliability, (ChainEdgeEvidence | Evidence)[]> = {
    strong: [],
    medium: [],
    weak: [],
  };

  evidences.forEach((e) => {
    const reliability: EvidenceReliability =
      isChainEvidence(e) ? e.reliability : (e as Evidence).reliability;
    grouped[reliability].push(e);
  });

  const hasMultipleGroups = Object.values(grouped).filter(g => g.length > 0).length > 1;

  return (
    <div className="p-4 rounded-lg bg-[var(--paper-white)] border border-[var(--paper-border)] shadow-[var(--paper-shadow)]">
      <h4 className="text-xs uppercase tracking-widest text-[var(--ink-400)] mb-3 font-semibold">
        {t("home.evidence.related")} ({evidences.length})
      </h4>
      <div className="space-y-4">
        {(["strong", "medium", "weak"] as EvidenceReliability[]).map((reliability) => {
          const items = grouped[reliability];
          if (items.length === 0) return null;
          const config = reliabilityConfig[reliability];
          
          return (
            <div key={reliability}>
              <div className="flex items-center gap-2 mb-2">
                <span 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: config.color }}
                />
                <span className="text-xs font-medium" style={{ color: config.color }}>
                  {config.label} ({items.length})
                </span>
                {hasMultipleGroups && (
                  <span className="text-xs text-[var(--ink-400)]">
                    — {t("home.evidence.weightShare")} {Math.round(items.reduce((sum, e) => {
                      const weight = isChainEvidence(e) ? e.causalWeight : (e as Evidence).causalWeight;
                      return sum + weight;
                    }, 0) / evidences.reduce((sum, e) => {
                      const weight = isChainEvidence(e) ? e.causalWeight : (e as Evidence).causalWeight;
                      return sum + weight;
                    }, 0) * 100)}%
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {items.map((e) => (
                  <EvidenceCard key={isChainEvidence(e) ? e.evidenceId : (e as Evidence).id} e={e} t={t} />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
