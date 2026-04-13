"use client";

import React from "react";
import { ChainNode } from "@/data/mockData";
import { useI18n } from "@/lib/i18n";

interface NodeDetailProps {
  node: ChainNode;
}

export default function NodeDetail({ node }: NodeDetailProps) {
  const { t } = useI18n();
  const typeConfig: Record<ChainNode["type"], { label: string; color: string; description: string }> = {
    outcome: {
      label: t("rightPanel.type.outcome"),
      color: "var(--marker-blue)",
      description: t("rightPanel.type.outcomeDesc"),
    },
    factor: {
      label: t("rightPanel.type.factor"),
      color: "var(--ink-400)",
      description: t("rightPanel.type.factorDesc"),
    },
    intermediate: {
      label: t("rightPanel.type.intermediate"),
      color: "var(--ink-300)",
      description: t("rightPanel.type.intermediateDesc"),
    },
  };
  const config = typeConfig[node.type];

  return (
    <div 
      className="p-5 rounded-lg bg-[var(--paper-white)] border border-[var(--paper-border)] shadow-[var(--paper-shadow)]"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-base font-semibold text-[var(--ink-900)] pr-2">{node.label}</h3>
        <div className="shrink-0 text-right">
          <span 
            className="text-lg font-mono font-bold block px-2 py-0.5 rounded"
            style={{ 
              backgroundColor: `${config.color}15`,
              color: config.color
            }}
          >
            {node.probability}%
          </span>
          <span className="text-xs text-[var(--ink-400)]">{t("nodeDetail.conditionalProbability")}</span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span 
          className="text-xs font-medium px-2 py-1 rounded"
          style={{ 
            backgroundColor: `${config.color}15`,
            color: config.color
          }}
        >
          {config.label}
        </span>
        <span className="text-xs text-[var(--ink-400)] px-2 py-1 rounded bg-[var(--paper-aged)]">
          {config.description}
        </span>
      </div>

      <div className="text-xs text-[var(--ink-400)] mb-3 flex items-center gap-2">
        <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
          <span>{t("graph.depth")} {node.depth} — {t("nodeDetail.depthLevel")}</span>
        </div>

      <div className="border-t border-[var(--paper-border)] pt-4 space-y-3">
        <div>
          <span className="text-xs font-semibold text-[var(--ink-500)] uppercase tracking-wider">
            {t("nodeDetail.brief")}
          </span>
          <p className="text-sm text-[var(--ink-600)] leading-relaxed mt-1">
            {node.description.brief}
          </p>
        </div>
        <div>
          <span className="text-xs font-semibold text-[var(--ink-500)] uppercase tracking-wider">
            {t("nodeDetail.detail")}
          </span>
          <p className="text-xs text-[var(--ink-400)] leading-relaxed mt-1">
            {node.description.detail}
          </p>
        </div>
      </div>
    </div>
  );
}
