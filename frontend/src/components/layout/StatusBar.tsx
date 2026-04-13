'use client';

import React from 'react';
import { EngineStatus } from '@/data/mockData';
import { useI18n, type TranslationKey } from '@/lib/i18n';

interface StatusBarProps {
  status: EngineStatus;
}

const stateLabelKeys: Record<string, TranslationKey> = {
  ready: "status.engineReady",
  processing: "status.engineProcessing",
  error: "status.engineError",
};

const stateDotClass: Record<string, string> = {
  ready: "status-dot-success",
  processing: "status-dot-warning",
  error: "status-dot-error",
};

export default function StatusBar({ status }: StatusBarProps) {
  const { t } = useI18n();

  const dotClass = stateDotClass[status.state];
  const labelKey = stateLabelKeys[status.state];

  return (
    <footer className="flex items-center h-4 px-4 border-t border-[var(--paper-border)] bg-[var(--paper-aged)] shrink-0 text-xs text-[var(--ink-400)]">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1">
          <span className={`status-dot ${dotClass}`} />
          {t(labelKey)}
        </span>
        <span className="text-[var(--ink-300)]">|</span>
        <span className="font-mono">{t("status.progressLabel")}: {status.progress}%</span>
        <span className="text-[var(--ink-300)]">|</span>
        <span className="font-mono">{t("status.chainCount")}: {status.causalChainCount}</span>
        <span className="text-[var(--ink-300)]">|</span>
        <span className="font-mono">{t("status.hypothesisCountLabel")}: {status.hypothesisCount}</span>
      </div>
      <div className="ml-auto">
        <span className="font-mono">{status.timestamp}</span>
      </div>
    </footer>
  );
}
