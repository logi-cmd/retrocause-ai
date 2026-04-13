'use client';

import React from 'react';
import { Hypothesis, Evidence } from '@/data/mockData';
import { useI18n } from '@/lib/i18n';

interface DataTableViewProps {
  hypotheses: Hypothesis[];
  evidences: Evidence[];
}

export default function DataTableView({ hypotheses, evidences }: DataTableViewProps) {
  const { t } = useI18n();
  return (
    <div className="h-full relative overflow-hidden flex flex-col" style={{ background: 'transparent' }}>
      <div className="shrink-0 px-4 pt-3 pb-2">
        <span 
          className="text-[10px] uppercase tracking-wider"
          style={{ 
            fontFamily: "'IBM Plex Mono', monospace",
            color: '#8b7355',
          }}
        >
          {t('home.table.title')}
        </span>
      </div>

      <div className="flex-1 overflow-auto scrollbar-thin px-3 pb-3">
        <div className="rounded p-3" style={{ background: 'rgba(255, 255, 255, 0.6)', border: '1px solid rgba(160, 140, 110, 0.15)' }}>
          <div className="text-[9px] uppercase tracking-wider mb-2" style={{ color: '#7a6b55', fontFamily: "'Caveat', cursive", fontSize: '0.9rem' }}>
            {t('panel.hypotheses')}
          </div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.id')}</th>
                <th className="text-left text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.hypothesis')}</th>
                <th className="text-right text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.prob')}</th>
                <th className="text-right text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.strength')}</th>
                <th className="text-right text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('panel.evidence')}</th>
              </tr>
            </thead>
            <tbody>
              {hypotheses.map((h) => (
                <tr key={h.id} className="border-t" style={{ borderColor: 'rgba(160, 140, 110, 0.1)' }}>
                  <td className="py-2 text-[11px] font-mono" style={{ color: '#8b7355' }}>{h.id}</td>
                  <td className="py-2 text-[11px]" style={{ color: '#5c4a32' }}>{h.title}</td>
                  <td className="py-2 text-[11px] font-mono text-right" style={{ color: '#5c4a32' }}>{h.probability}%</td>
                  <td className="py-2 text-[11px] font-mono text-right" style={{ color: '#8b7355' }}>{h.causalStrength.toFixed(2)}</td>
                  <td className="py-2 text-[11px] font-mono text-right" style={{ color: '#8b7355' }}>{h.evidenceCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="rounded p-3 mt-3" style={{ background: 'rgba(255, 255, 255, 0.6)', border: '1px solid rgba(160, 140, 110, 0.15)' }}>
          <div className="text-[9px] uppercase tracking-wider mb-2" style={{ color: '#7a6b55', fontFamily: "'Caveat', cursive", fontSize: '0.9rem' }}>
            {t('panel.evidence')}
          </div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.id')}</th>
                <th className="text-left text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.content')}</th>
                <th className="text-left text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.source')}</th>
                <th className="text-right text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.reliability')}</th>
                <th className="text-right text-[10px] uppercase tracking-wider pb-2" style={{ color: '#8b7355' }}>{t('home.table.weight')}</th>
              </tr>
            </thead>
            <tbody>
              {evidences.map((e) => (
                <tr key={e.id} className="border-t" style={{ borderColor: 'rgba(160, 140, 110, 0.1)' }}>
                  <td className="py-2 text-[11px] font-mono" style={{ color: '#8b7355' }}>{e.id}</td>
                  <td className="py-2 text-[11px] max-w-xs truncate" style={{ color: '#5c4a32' }}>{e.content}</td>
                  <td className="py-2 text-[11px]" style={{ color: '#8b7355' }}>{e.source}</td>
                  <td className="py-2 text-right">
                    <span
                      className="text-[11px] font-mono"
                      style={{
                        color: e.reliability === 'strong' ? '#5a7a52' : e.reliability === 'medium' ? '#8a6a40' : '#943d30',
                      }}
                    >
                      {e.reliability === 'strong' ? t('strength.strong') : e.reliability === 'medium' ? t('strength.medium') : t('strength.weak')}
                    </span>
                  </td>
                  <td className="py-2 text-[11px] font-mono text-right" style={{ color: '#8b7355' }}>{e.causalWeight.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
