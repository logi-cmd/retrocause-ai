'use client';

import React, { useState } from 'react';
import ViewTabs, { ViewType } from './ViewTabs';
import CausalGraphView from './CausalGraphView';
import ChainView from './ChainView';
import DebateTreeView, { AgentReport } from './DebateTreeView';
import DataTableView from './DataTableView';
import {
  CausalNode,
  CausalEdge,
  Hypothesis,
  Evidence,
  GraphStats,
  CausalChain,
} from '@/data/mockData';

interface MainCanvasProps {
  nodes: CausalNode[];
  edges: CausalEdge[];
  reports: AgentReport[];
  hypotheses: Hypothesis[];
  evidences: Evidence[];
  stats: GraphStats;
  chain?: CausalChain;
  selectedChainNodeId?: string;
  onChainNodeSelect?: (nodeId: string) => void;
}

export default function MainCanvas({
  nodes,
  edges,
  reports,
  hypotheses,
  evidences,
  stats,
  chain,
  selectedChainNodeId,
  onChainNodeSelect,
}: MainCanvasProps) {
  const [activeView, setActiveView] = useState<ViewType>('causal');

  return (
    <>
      <div className="flex-1 relative overflow-hidden">
        <div className="h-full overflow-hidden relative">
          <div 
            className="absolute inset-0 transition-view animate-entrance relative"
            style={{
              background: `
                radial-gradient(ellipse at 20% 30%, rgba(180, 160, 130, 0.15) 0%, transparent 40%),
                radial-gradient(ellipse at 80% 70%, rgba(200, 180, 150, 0.12) 0%, transparent 40%),
                linear-gradient(180deg, #f8f4eb 0%, #f0e8d8 50%, #e8dfc8 100%)
              `
            }}
          >
            <div 
              className="absolute inset-0 pointer-events-none"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
                opacity: '0.04',
              }}
            />
            <div 
              className="absolute inset-0 pointer-events-none"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(160, 140, 110, 0.06) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(160, 140, 110, 0.06) 1px, transparent 1px)
                `,
                backgroundSize: '40px 40px',
              }}
            />
            
            {activeView === 'chain' && chain && (
              <ChainView
                chain={chain}
                selectedNodeId={selectedChainNodeId}
                onNodeSelect={onChainNodeSelect}
              />
            )}
            {activeView === 'causal' && (
              <CausalGraphView 
                nodes={nodes} 
                edges={edges}
                selectedNodeId={selectedChainNodeId}
                onNodeSelect={onChainNodeSelect}
              />
            )}
            {activeView === 'debate' && <DebateTreeView reports={reports} />}
            {activeView === 'table' && <DataTableView hypotheses={hypotheses} evidences={evidences} />}
          </div>
        </div>
      </div>
      <ViewTabs activeView={activeView} onViewChange={setActiveView} stats={stats} chainMeta={chain?.metadata} />
    </>
  );
}
