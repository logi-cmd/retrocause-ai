"use client";

import React from "react";
import LocaleToggle from "@/components/ui/LocaleToggle";
import { useI18n } from "@/lib/i18n";

const statusKeys = {
  connected: "header.status.live" as const,
  disconnected: "header.status.disconnected" as const,
  processing: "header.status.processing" as const,
};

const statusDotClass = {
  connected: "status-dot-success",
  disconnected: "status-dot-error",
  processing: "status-dot-warning",
};

interface HeaderProps {
  connectionStatus?: "connected" | "disconnected" | "processing";
  isDemoMode?: boolean;
  lastQuery?: string;
}

export default function Header({
  connectionStatus = "connected",
  isDemoMode = false,
  lastQuery = "",
}: HeaderProps) {
  const { t } = useI18n();

  return (
    <header 
      className="flex items-center justify-between px-5 shrink-0 relative z-[100]"
      style={{
        height: '52px',
        background: 'rgba(250, 246, 238, 0.92)',
        backdropFilter: 'blur(8px)',
        borderBottom: '1px solid rgba(160, 140, 110, 0.2)',
      }}
    >
      <div className="flex items-center gap-3">
        <div 
          className="w-7 h-7 rounded flex items-center justify-center"
          style={{
            background: 'rgba(180, 80, 60, 0.1)',
            border: '1px solid rgba(180, 80, 60, 0.2)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a0503c" strokeWidth="2">
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
        </div>
        <h1 
          style={{
            fontFamily: "'Caveat', cursive",
            fontSize: '1.5rem',
            fontWeight: 500,
            color: '#5c4a32',
            letterSpacing: '0.02em',
          }}
        >
          {t("header.title")}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <div 
          className="px-3 py-1 rounded text-xs font-medium tracking-wider uppercase"
          style={{
            background: 'rgba(180, 80, 60, 0.1)',
            border: '1px solid rgba(180, 80, 60, 0.25)',
            color: '#a0503c',
          }}
        >
          {lastQuery ? lastQuery.slice(0, 30) + (lastQuery.length > 30 ? '...' : '') : t("home.badge.question")}
        </div>
        <div 
          className="flex items-center gap-1.5 text-xs"
          style={{ color: '#8b7355' }}
        >
          <span 
            className={`w-1.5 h-1.5 rounded-full animate-pulse ${statusDotClass[connectionStatus]}`}
            style={{ background: '#2D8A5F' }}
          />
          <span>{isDemoMode ? t("status.demoMode") : t(statusKeys[connectionStatus])}</span>
        </div>
        <LocaleToggle />
      </div>
    </header>
  );
}
