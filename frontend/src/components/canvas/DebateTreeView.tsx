'use client';

import React, { useState } from 'react';
import { useI18n } from '@/lib/i18n';

export interface DebateMetric {
  probability: number;
  confidence: number;
  evidenceIds: string[];
}

export interface DebateEvidence {
  id: string;
  content: string;
  type: 'support' | 'challenge';
  weight: number;
}

export interface AgentReport {
  id: string;
  agentName: string;
  agentRole: string;
  stance: 'support' | 'oppose' | 'neutral';
  phase: number;
  timestamp: string;
  conclusion: string;
  reasoning: string;
  metrics: DebateMetric;
  evidenceChain: DebateEvidence[];
  children?: AgentReport[];
}

export interface DebateTreeViewProps {
  reports: AgentReport[];
}

const STANCE_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  support: {
    border: 'rgba(100, 140, 90, 0.4)',
    bg: 'rgba(255, 255, 255, 0.7)',
    text: '#3d3225',
  },
  oppose: {
    border: 'rgba(196, 69, 54, 0.3)',
    bg: 'rgba(255, 250, 248, 0.7)',
    text: '#3d3225',
  },
  neutral: {
    border: 'rgba(160, 140, 110, 0.3)',
    bg: 'rgba(255, 255, 255, 0.6)',
    text: '#5c4a32',
  },
};

function getPhaseLabel(phase: number, t: ReturnType<typeof useI18n>["t"]): string {
  switch (phase) {
    case 1:
      return t('debate.phase.1');
    case 2:
      return t('debate.phase.2');
    case 3:
      return t('debate.phase.3');
    case 4:
      return t('debate.phase.4');
    case 5:
      return t('debate.phase.5');
    default:
      return `${t('debate.phaseLabel')} ${phase}`;
  }
}

function getRoleIcon(role: string): string {
  switch (role) {
    case '溯因推理':
      return '●';
    case '演绎推理':
      return '■';
    case '归纳推理':
      return '▲';
    case '魔鬼代言':
      return '◆';
    case '仲裁':
      return '★';
    default:
      return '●';
  }
}

function getRoleLabel(role: string, t: ReturnType<typeof useI18n>["t"]): string {
  switch (role) {
    case '溯因推理':
      return t('debate.role.abduction');
    case '演绎推理':
      return t('debate.role.deduction');
    case '归纳推理':
      return t('debate.role.induction');
    case '魔鬼代言':
      return t('debate.role.devilsAdvocate');
    case '仲裁':
      return t('debate.role.arbitration');
    default:
      return role;
  }
}

function ProbabilityBar({ value }: { value: number }) {
  const filledBlocks = Math.round(value / 10);
  const emptyBlocks = 10 - filledBlocks;
  
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex gap-0.5">
        {Array.from({ length: filledBlocks }).map((_, i) => (
          <div key={`filled-${i}`} className="w-1.5 h-2.5 rounded-sm" style={{ background: 'rgba(180, 140, 80, 0.5)' }} />
        ))}
        {Array.from({ length: emptyBlocks }).map((_, i) => (
          <div key={`empty-${i}`} className="w-1.5 h-2.5 rounded-sm" style={{ background: 'rgba(160, 140, 110, 0.15)' }} />
        ))}
      </div>
      <span className="text-[10px] font-mono" style={{ color: '#8b7355' }}>{value}%</span>
    </div>
  );
}

function EvidenceBadge({ evidence }: { evidence: DebateEvidence }) {
  const isSupport = evidence.type === 'support';
  
  return (
    <div 
      className="flex items-start gap-2 px-2 py-1.5 rounded text-[11px]"
      style={{ 
        background: isSupport ? 'rgba(100, 140, 90, 0.1)' : 'rgba(196, 69, 54, 0.08)',
        borderLeft: `2px solid ${isSupport ? 'rgba(100, 140, 90, 0.5)' : 'rgba(196, 69, 54, 0.4)'}`,
      }}
    >
      <span className="font-mono shrink-0" style={{ color: isSupport ? '#5a7a52' : '#943d30' }}>
        {evidence.id}
      </span>
      <span className="flex-1 leading-relaxed" style={{ color: '#5c4a32' }}>
        {evidence.content}
      </span>
    </div>
  );
}

function ReportCard({ report, expanded, onToggle }: { 
  report: AgentReport; 
  expanded: boolean;
  onToggle: () => void;
}) {
  const { t } = useI18n();
  const colors = STANCE_COLORS[report.stance] || STANCE_COLORS.neutral;
  const roleIcon = getRoleIcon(report.agentRole);

  return (
    <div 
      className="rounded"
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        borderBottom: `3px solid ${colors.border}`,
      }}
    >
      <button 
        onClick={onToggle}
        className="w-full px-3 py-2 flex items-start gap-3 text-left rounded"
        style={{ background: 'transparent' }}
      >
        <div className="flex flex-col items-center min-w-[20px]">
          <span className="text-[10px] font-mono" style={{ color: '#8b7355' }}>
            {report.phase.toString().padStart(2, '0')}
          </span>
          <span style={{ color: 'rgba(160, 140, 110, 0.6)' }}>{roleIcon}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-[12px] font-medium" style={{ color: colors.text, fontFamily: "'Caveat', cursive", fontSize: '1rem' }}>
              {report.agentName}
            </span>
              <span className="text-[9px]" style={{ color: '#8b7355' }}>
                {getRoleLabel(report.agentRole, t)}
              </span>
          </div>
          
          {!expanded && (
            <p className="text-[11px] truncate" style={{ color: '#7a6b55' }}>
              {report.conclusion}
            </p>
          )}
        </div>

        {!expanded && (
          <div className="flex items-center gap-2 text-[10px] font-mono shrink-0">
            <ProbabilityBar value={report.metrics.probability} />
          </div>
        )}

        <span className="text-[10px]" style={{ color: '#8b7355' }}>
          {expanded ? '−' : '+'}
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t" style={{ borderColor: 'rgba(160, 140, 110, 0.15)' }}>
          <div className="text-[10px] font-mono mb-2" style={{ color: '#8b7355' }}>
            T+{report.timestamp}
          </div>

          <div className="mb-2">
            <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: '#8b7355' }}>{t('debate.section.conclusion')}</div>
            <p className="text-[12px]" style={{ color: '#5c4a32', lineHeight: 1.5 }}>
              {report.conclusion}
            </p>
          </div>

          <div className="mb-2">
            <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: '#8b7355' }}>{t('debate.section.reasoning')}</div>
            <p className="text-[11px] leading-relaxed" style={{ color: '#6b5a42' }}>
              {report.reasoning}
            </p>
          </div>

          <div className="mb-2 p-2 rounded" style={{ background: 'rgba(160, 140, 110, 0.08)' }}>
            <div className="text-[9px] uppercase tracking-wider mb-1.5" style={{ color: '#8b7355' }}>{t('debate.section.metrics')}</div>
            <div className="flex items-center gap-4 text-[10px]">
              <div>
                <span style={{ color: '#8b7355' }}>{t('debate.metric.probability')}: </span>
                <span className="font-mono" style={{ color: '#5c4a32' }}>{report.metrics.probability}%</span>
              </div>
              <div>
                <span style={{ color: '#8b7355' }}>{t('debate.metric.confidence')}: </span>
                <span className="font-mono" style={{ color: '#5c4a32' }}>{(report.metrics.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>

          {report.evidenceChain.length > 0 && (
            <div>
              <div className="text-[9px] uppercase tracking-wider mb-1.5" style={{ color: '#8b7355' }}>{t('debate.section.evidence')}</div>
              <div className="space-y-1">
                {report.evidenceChain.map((ev) => (
                  <EvidenceBadge key={ev.id} evidence={ev} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PhaseConnector({ phase }: { phase: number }) {
  const { t } = useI18n();
  return (
    <div className="flex items-center gap-2 py-2">
      <div className="h-px flex-1" style={{ background: 'rgba(160, 140, 110, 0.2)' }} />
      <span className="text-[9px] font-mono px-2" style={{ color: '#8b7355' }}>
        {t('debate.phaseLabel').toUpperCase()} {phase.toString().padStart(2, '0')} — {getPhaseLabel(phase, t)}
      </span>
      <div className="h-px flex-1" style={{ background: 'rgba(160, 140, 110, 0.2)' }} />
    </div>
  );
}

function TimelineView({ reports }: { reports: AgentReport[] }) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set([reports[0]?.id]));
  
  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const reportsByPhase = reports.reduce((acc, report) => {
    if (!acc[report.phase]) acc[report.phase] = [];
    acc[report.phase].push(report);
    return acc;
  }, {} as Record<number, AgentReport[]>);

  const phases = Object.keys(reportsByPhase).map(Number).sort((a, b) => a - b);

  return (
    <div className="space-y-0.5">
      {phases.map((phase) => (
        <div key={phase}>
          <PhaseConnector phase={phase} />
          <div className="space-y-1.5 pl-2">
            {reportsByPhase[phase].map((report) => (
              <ReportCard
                key={report.id}
                report={report}
                expanded={expandedIds.has(report.id)}
                onToggle={() => toggleExpanded(report.id)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function DebateStatsSummary({ reports }: { reports: AgentReport[] }) {
  const { t } = useI18n();
  const totalEvidence = reports.reduce(
    (sum, r) => sum + (r.evidenceChain ? r.evidenceChain.length : 0), 
    0
  );
  
  const avgProbability = reports.length > 0 ? reports.reduce(
    (sum, r) => sum + r.metrics.probability, 
    0
  ) / reports.length : 0;

  return (
    <div className="flex items-center gap-3 text-[10px]">
      <span style={{ color: '#8b7355' }}>
        {t('debate.summary.reports')}: <span className="font-mono" style={{ color: '#5c4a32' }}>{reports.length}</span>
      </span>
      <span style={{ color: 'rgba(160, 140, 110, 0.4)' }}>|</span>
      <span style={{ color: '#8b7355' }}>
        {t('debate.summary.evidence')}: <span className="font-mono" style={{ color: '#5c4a32' }}>{totalEvidence}</span>
      </span>
      <span style={{ color: 'rgba(160, 140, 110, 0.4)' }}>|</span>
      <span style={{ color: '#8b7355' }}>
        {t('debate.summary.avgProbability')}: <span className="font-mono" style={{ color: '#5c4a32' }}>{avgProbability.toFixed(1)}%</span>
      </span>
    </div>
  );
}

export default function DebateTreeView({ reports }: DebateTreeViewProps) {
  const { t } = useI18n();
  const [viewMode, setViewMode] = useState<'timeline' | 'tree'>('timeline');

  if (!reports || reports.length === 0) {
    return (
      <div className="h-full flex items-center justify-center" style={{ background: 'transparent' }}>
        <div className="text-center">
          <div className="text-sm mb-1" style={{ color: '#7a6b55' }}>{t('debate.empty.title')}</div>
          <div className="text-[11px] font-mono" style={{ color: '#8b7355' }}>{t('debate.empty.detail')}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden" style={{ background: 'transparent' }}>
      <div className="shrink-0 px-4 pt-3 pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span 
              className="text-[9px] uppercase tracking-wider"
              style={{ 
                fontFamily: "'IBM Plex Mono', monospace",
                color: '#8b7355',
              }}
            >
              {t('debate.title')}
            </span>
          </div>
          
          <div className="flex items-center gap-1">
            <button
              onClick={() => setViewMode('timeline')}
              className="px-2 py-1 text-[10px] rounded"
              style={{
                background: viewMode === 'timeline' ? 'rgba(180, 140, 80, 0.2)' : 'transparent',
                color: viewMode === 'timeline' ? '#8a6a40' : '#8b7355',
              }}
            >
              {t('debate.view.timeline')}
            </button>
            <button
              onClick={() => setViewMode('tree')}
              className="px-2 py-1 text-[10px] rounded"
              style={{
                background: viewMode === 'tree' ? 'rgba(180, 140, 80, 0.2)' : 'transparent',
                color: viewMode === 'tree' ? '#8a6a40' : '#8b7355',
              }}
            >
              {t('debate.view.tree')}
            </button>
          </div>
        </div>
        
        <div className="mt-2">
          <DebateStatsSummary reports={reports} />
        </div>
      </div>

      <div className="flex-1 overflow-auto px-3 pb-3 scrollbar-thin">
        {viewMode === 'timeline' ? (
          <TimelineView reports={reports} />
        ) : (
          <TreeView reports={reports} />
        )}
      </div>

      <div className="shrink-0 px-4 py-2 border-t" style={{ borderColor: 'rgba(160, 140, 110, 0.15)' }}>
        <div className="flex items-center justify-between text-[10px]">
          <span style={{ color: '#8b7355' }}>{t('debate.footer.title')}</span>
          <div className="flex items-center gap-3">
            <span style={{ color: '#5a7a52' }}>
              {t('debate.footer.support')}: {reports.filter(r => r.stance === 'support').length}
            </span>
            <span style={{ color: '#943d30' }}>
              {t('debate.footer.oppose')}: {reports.filter(r => r.stance === 'oppose').length}
            </span>
            <span style={{ color: '#8b7355' }}>
              {t('debate.footer.neutral')}: {reports.filter(r => r.stance === 'neutral').length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function TreeView({ reports }: { reports: AgentReport[] }) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set([reports[0]?.id]));

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const buildTree = (reports: AgentReport[]): AgentReport[] => {
    const rootReports = reports.filter(r => r.phase === 1);
    
    const attachChildren = (parent: AgentReport): AgentReport => {
      const children = reports.filter(r => r.phase === parent.phase + 1);
      return {
        ...parent,
        children: children.length > 0 ? children.map(c => attachChildren(c)) : undefined,
      };
    };

    return rootReports.map(r => attachChildren(r));
  };

  const tree = buildTree(reports);

  const renderNode = (report: AgentReport, depth: number = 0): React.ReactNode => {
    return (
      <div key={report.id} className="relative">
        {depth > 0 && (
          <div 
            className="absolute"
            style={{ 
              left: `${(depth - 1) * 16 + 8}px`,
              top: 0,
              height: '50%',
              borderLeft: '1px solid rgba(160, 140, 110, 0.2)',
            }}
          />
        )}
        
        <div className="pl-4">
          <ReportCard
            report={report}
            expanded={expandedIds.has(report.id)}
            onToggle={() => toggleExpanded(report.id)}
          />
          
          {report.children && expandedIds.has(report.id) && (
            <div className="ml-4 pl-3 border-l" style={{ borderColor: 'rgba(160, 140, 110, 0.15)' }}>
              {report.children.map(child => renderNode(child, depth + 1))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-1">
      {tree.map(node => renderNode(node))}
    </div>
  );
}
