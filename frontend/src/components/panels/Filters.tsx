
"use client";

import React from "react";
import {
  timeRangeOptions,
  causalStrengthOptions,
  evidenceQualityOptions,
} from "@/data/mockData";

interface FiltersProps {
  timeRange?: string;
  causalStrength?: string;
  evidenceQuality?: string;
  onTimeRangeChange?: (value: string) => void;
  onCausalStrengthChange?: (value: string) => void;
  onEvidenceQualityChange?: (value: string) => void;
}

export default function Filters({
  timeRange = "all",
  causalStrength = "all",
  evidenceQuality = "all",
  onTimeRangeChange,
  onCausalStrengthChange,
  onEvidenceQualityChange,
}: FiltersProps) {
  return (
    <div className="p-4 mb-4 bg-[var(--paper-white)] border border-[var(--paper-border)] rounded-lg mx-4 shadow-[var(--paper-shadow)]">
      <label className="block text-xs uppercase tracking-widest text-[var(--ink-400)] mb-3 font-semibold">
        筛选条件
      </label>
      <div className="space-y-4">
        <div>
          <span className="text-xs text-[var(--ink-500)] mb-1 block">时间范围</span>
          <select
            className="w-full px-3 py-2 text-sm rounded-md border border-[var(--paper-border)] bg-[var(--paper-white)] text-[var(--ink-700)] focus:border-[var(--marker-blue)] focus:ring-2 focus:ring-[var(--marker-blue)]/10 outline-none transition-all"
            value={timeRange}
            onChange={(e) => onTimeRangeChange?.(e.target.value)}
          >
            {timeRangeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <span className="text-xs text-[var(--ink-500)] mb-1 block">因果强度</span>
          <select
            className="w-full px-3 py-2 text-sm rounded-md border border-[var(--paper-border)] bg-[var(--paper-white)] text-[var(--ink-700)] focus:border-[var(--marker-blue)] focus:ring-2 focus:ring-[var(--marker-blue)]/10 outline-none transition-all"
            value={causalStrength}
            onChange={(e) => onCausalStrengthChange?.(e.target.value)}
          >
            {causalStrengthOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <span className="text-xs text-[var(--ink-500)] mb-1 block">证据质量</span>
          <select
            className="w-full px-3 py-2 text-sm rounded-md border border-[var(--paper-border)] bg-[var(--paper-white)] text-[var(--ink-700)] focus:border-[var(--marker-blue)] focus:ring-2 focus:ring-[var(--marker-blue)]/10 outline-none transition-all"
            value={evidenceQuality}
            onChange={(e) => onEvidenceQualityChange?.(e.target.value)}
          >
            {evidenceQualityOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

