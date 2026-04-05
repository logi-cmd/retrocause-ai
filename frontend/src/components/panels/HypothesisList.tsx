
"use client";

import React from "react";
import { Hypothesis } from "@/data/mockData";
import { useI18n } from "@/lib/i18n";

interface HypothesisListProps {
  hypotheses: Hypothesis[];
  selectedId?: string;
  onSelect?: (hypothesis: Hypothesis) => void;
}

function getStrengthColor(strength: number): string {
  if (strength >= 0.7) return "var(--thread-success)";
  if (strength >= 0.4) return "var(--thread-warning)";
  return "var(--marker-red)";
}

function getStrengthLabel(strength: number, t: ReturnType<typeof useI18n>["t"]): string {
  if (strength >= 0.7) return `${t("strength.strong")}${t("strength.causal")}`;
  if (strength >= 0.4) return `${t("strength.medium")}${t("strength.causal")}`;
  return `${t("strength.weak")}${t("strength.causal")}`;
}

export default function HypothesisList({
  hypotheses,
  selectedId,
  onSelect,
}: HypothesisListProps) {
  const { t } = useI18n();
  if (hypotheses.length === 0) {
    return (
      <div className="flex-1 overflow-auto p-4 pt-0">
        <div className="mb-3">
          <span className="text-xs uppercase tracking-widest text-[var(--ink-400)] font-semibold">
            {t("leftPanel.competingHypotheses")} (0)
          </span>
        </div>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-12 h-12 rounded-full bg-[var(--paper-aged)] flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-[var(--ink-400)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <p className="text-sm text-[var(--ink-500)] mb-1">{t("hypothesis.empty")}</p>
          <p className="text-xs text-[var(--ink-400)]">{t("hypothesis.emptyHint")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-4 pt-0">
      <div className="mb-3">
        <span className="text-xs uppercase tracking-widest text-[var(--ink-400)] font-semibold section-header inline-block">
          {t("leftPanel.competingHypotheses")} ({hypotheses.length})
        </span>
      </div>
      <div className="space-y-3">
        {hypotheses.map((h) => {
          const isSelected = h.id === selectedId;
          const strengthColor = getStrengthColor(h.causalStrength);
          return (
            <div
              key={h.id}
              className={`p-4 rounded-lg cursor-pointer transition-all duration-200 ease-[var(--ease-out-quart)]
                ${isSelected 
                  ? "bg-[var(--paper-white)] border-2 shadow-md" 
                  : "bg-[var(--paper-white)] border border-[var(--paper-border)] hover:shadow-md hover:-translate-y-0.5"}`}
              style={{
                borderColor: isSelected ? 'var(--marker-blue)' : undefined,
                boxShadow: isSelected 
                  ? '0 4px 12px rgba(91, 141, 239, 0.2)' 
                  : '0 1px 3px rgba(0,0,0,0.06)',
                transitionTimingFunction: 'var(--ease-out-quart)'
              }}
              onClick={() => onSelect?.(h)}
            >
              {isSelected && (
                <div className="mb-2">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-sm marker-chip marker-chip-blue">
                    {t("hypothesis.current")}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-[var(--ink-800)]">{h.title}</span>
                <div className="flex items-center gap-2">
                  <span 
                    className="text-xs font-mono px-1.5 py-0.5 rounded"
                    style={{ 
                      backgroundColor: `${strengthColor}15`,
                      color: strengthColor 
                    }}
                  >
                    {getStrengthLabel(h.causalStrength, t)}
                  </span>
                  <span 
                    className="text-xs font-mono px-1.5 py-0.5 rounded"
                    style={{ 
                      backgroundColor: 'var(--info-bg)',
                      color: 'var(--marker-blue)'
                    }}
                  >
                    {h.probability}%
                  </span>
                </div>
              </div>
              <p className="text-xs text-[var(--ink-500)] line-clamp-2 leading-relaxed mb-2">
                {h.description}
              </p>
              <div className="flex items-center gap-3 text-xs text-[var(--ink-400)]">
                <span className="flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {h.evidenceCount} {t("hypothesis.evidenceCount")}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
