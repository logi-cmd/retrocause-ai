'use client';

import React from 'react';
import { GraphStats, ChainMetadata } from '@/data/mockData';
import { useI18n } from '@/lib/i18n';

type ViewType = 'chain' | 'causal' | 'debate' | 'table';

interface ViewTabsProps {
  activeView: ViewType;
  onViewChange: (view: ViewType) => void;
  stats: GraphStats;
  chainMeta?: ChainMetadata;
}

const viewTabKeys: Record<ViewType, string> = {
  chain: 'viewTabs.chain',
  causal: 'viewTabs.causal',
  debate: 'viewTabs.debate',
  table: 'viewTabs.table',
};

export default function ViewTabs({ activeView, onViewChange, stats, chainMeta }: ViewTabsProps) {
  const { t } = useI18n();

  return (
    <div 
      className="flex items-center h-11 px-5 border-b border-[rgba(200,190,175,0.35)] bg-[rgba(252,250,245,0.95)] shrink-0 relative"
      style={{
        boxShadow: '0 2px 8px rgba(139, 119, 89, 0.08)'
      }}
    >
      <div 
        className="absolute top-1.5 left-1/2 -translate-x-1/2 w-2.5 h-2.5 rounded-full border border-white"
        style={{
          background: 'linear-gradient(135deg, #E86363 0%, var(--marker-red) 60%, #A03030 100%)',
          boxShadow: '0 1px 3px rgba(139, 89, 89, 0.3)',
        }}
      />
      
      <div className="flex items-center gap-0.5">
        {(Object.keys(viewTabKeys) as ViewType[]).map((view) => {
          const isActive = activeView === view;
          return (
            <button
              key={view}
              className={`
                relative px-3.5 py-1.5 text-xs font-medium rounded-md
                transition-all duration-200
                ${isActive 
                  ? 'text-white shadow-[0_2px_6px_rgba(59,110,165,0.3)]' 
                  : 'text-[var(--ink-500)] hover:text-[var(--marker-blue)] hover:bg-[rgba(59,110,165,0.06)]'
                }
              `}
              onClick={() => onViewChange(view)}
              style={isActive ? {
                backgroundColor: 'var(--marker-blue)',
                marginBottom: '-1px',
                paddingBottom: '6px',
                borderBottom: '2px solid var(--marker-blue)',
              } : {
                borderBottom: '2px solid transparent',
              }}
            >
              {isActive && (
                <span 
                  className="absolute -bottom-px left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
                  style={{
                    backgroundColor: 'var(--marker-blue)',
                    boxShadow: '0 0 5px rgba(59,110,165,0.5)',
                  }}
                />
              )}
              {t(viewTabKeys[view] as Parameters<typeof t>[0])}
            </button>
          );
        })}
      </div>
      <div className="ml-auto flex items-center gap-1.5 text-xs text-[var(--ink-400)] font-mono">
        {activeView === 'chain' && chainMeta ? (
          <>
            <span 
              className="px-2 py-0.5 rounded bg-[var(--paper-aged)] text-[var(--ink-500)] border border-[var(--paper-border)] transition-colors duration-150"
            >
              {t("graph.depth")} {chainMeta.maxDepth}
            </span>
            <span 
              className="px-2 py-0.5 rounded bg-[var(--paper-aged)] text-[var(--ink-500)] border border-[var(--paper-border)] transition-colors duration-150"
            >
              {chainMeta.totalNodes} {t("graph.nodes")}
            </span>
            <span 
              className="px-2 py-0.5 rounded text-[var(--marker-blue)] font-medium border border-[var(--marker-blue)]/25 bg-[var(--info-bg)] transition-colors duration-150"
            >
              {t("graph.confidence")} {(chainMeta.confidence * 100).toFixed(0)}%
            </span>
          </>
        ) : (
          <>
            <span 
              className="px-2 py-0.5 rounded bg-[var(--paper-aged)] text-[var(--ink-500)] border border-[var(--paper-border)] transition-colors duration-150"
            >
              {stats.nodeCount} {t("graph.nodes")}
            </span>
            <span 
              className="px-2 py-0.5 rounded bg-[var(--paper-aged)] text-[var(--ink-500)] border border-[var(--paper-border)] transition-colors duration-150"
            >
              {stats.edgeCount} {t("graph.edges")}
            </span>
            <span 
              className="px-2 py-0.5 rounded text-[var(--marker-blue)] font-medium border border-[var(--marker-blue)]/25 bg-[var(--info-bg)] transition-colors duration-150"
            >
              {stats.confidence}%
            </span>
          </>
        )}
      </div>
    </div>
  );
}

export type { ViewType };
