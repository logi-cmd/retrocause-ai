
"use client";

import React from "react";
import { ProbabilityBar as ProbabilityBarType } from "@/data/mockData";
import { useI18n } from "@/lib/i18n";

interface ProbabilityBarProps {
  bars: ProbabilityBarType[];
}

export default function ProbabilityBar({ bars }: ProbabilityBarProps) {
  const { t } = useI18n();
  return (
    <div className="p-5 rounded-lg bg-[var(--paper-white)] border border-[var(--paper-border)] shadow-[var(--paper-shadow)]">
      <h4 className="text-xs uppercase tracking-widest text-[var(--ink-400)] mb-4 font-semibold">
        {t("rightPanel.probabilityDistribution")}
      </h4>
      <div className="space-y-4">
        {bars.map((p) => (
          <div key={p.label} className="flex items-center gap-3">
            <span className="w-24 text-xs text-[var(--ink-500)] truncate font-mono font-medium">
              {p.label}
            </span>
            <div className="flex-1 h-3 bg-[var(--paper-aged)] rounded-full overflow-hidden border border-[var(--paper-border)]">
              <div
                className="h-full rounded-full transition-all duration-500 ease-out"
                style={{
                  width: `${p.value}%`,
                  backgroundColor: p.color || "var(--marker-blue)",
                  boxShadow: `0 0 8px ${p.color || "var(--marker-blue)"}40`
                }}
              />
            </div>
            <span className="w-12 text-xs text-[var(--ink-400)] text-right font-mono font-bold">
              {p.value}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

