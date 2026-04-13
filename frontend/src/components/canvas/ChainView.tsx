'use client';

import React, { useMemo, useRef, useEffect, useState } from 'react';
import {
  CausalChain,
  ChainNode,
  ChainEdge,
  ChainMetadata,
} from '@/data/mockData';
import { useI18n } from '@/lib/i18n';

interface ChainViewProps {
  chain: CausalChain;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string) => void;
}

function getAncestorPath(
  nodeId: string,
  nodes: ChainNode[],
): Set<string> {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const ancestors = new Set<string>();
  const stack = [nodeId];
  while (stack.length > 0) {
    const current = stack.pop()!;
    const node = nodeMap.get(current);
    if (!node) continue;
    for (const upId of node.upstreamIds) {
      if (!ancestors.has(upId)) {
        ancestors.add(upId);
        stack.push(upId);
      }
    }
  }
  return ancestors;
}

const nodeTypeConfig: Record<ChainNode['type'], { border: string; bg: string; indicator: string; text: string }> = {
  outcome: { 
    border: 'rgba(70, 130, 180, 0.4)', 
    bg: 'linear-gradient(145deg, #eef5fa 0%, #dce8f2 100%)', 
    indicator: '#4a7a9e', 
    text: '#3d3225',
  },
  factor: { 
    border: 'rgba(180, 140, 80, 0.4)', 
    bg: 'linear-gradient(145deg, #fef9e7 0%, #f9e8c8 100%)', 
    indicator: '#8a6a40', 
    text: '#3d3225',
  },
  intermediate: { 
    border: 'rgba(100, 140, 90, 0.4)', 
    bg: 'linear-gradient(145deg, #eef8f3 0%, #d8efe2 100%)', 
    indicator: '#5a7a52', 
    text: '#3d3225',
  },
};

const edgeTypeColors: Record<string, string> = {
  strong: '#5a7a52',
  weak: '#8a6a40',
  negative: '#943d30',
  uncertain: '#8b7355',
};

const CARD_WIDTH = 200;
const CARD_HEIGHT = 120;

function EvidenceCard({
  node,
  isSelected,
  isOnPath,
  onSelect,
  style,
  animationDelay,
}: {
  node: ChainNode;
  isSelected: boolean;
  isOnPath: boolean;
  onSelect: () => void;
  style?: React.CSSProperties;
  animationDelay?: number;
}) {
  const colors = nodeTypeConfig[node.type];
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <button
      onClick={onSelect}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        ...style,
        width: CARD_WIDTH,
        minHeight: CARD_HEIGHT,
        background: colors.bg,
        borderColor: isSelected ? 'var(--marker-blue)' : isOnPath ? 'rgba(70, 130, 180, 0.4)' : colors.border,
        borderWidth: isSelected ? 2 : 1,
        borderBottom: `3px solid ${colors.border}`,
        boxShadow: isSelected 
          ? '0 4px 12px rgba(80, 60, 40, 0.2)' 
          : isOnPath 
            ? '0 4px 10px rgba(80, 60, 40, 0.15)'
            : '0 3px 8px rgba(80, 60, 40, 0.12), 0 1px 3px rgba(80, 60, 40, 0.08)',
        transform: isHovered && !isSelected ? 'translateY(-2px) rotate(0.5deg)' : isSelected ? 'translateY(-1px) rotate(-0.5deg)' : 'translateY(0) rotate(0deg)',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
        textAlign: 'left',
        position: 'absolute',
        animation: `fadeSlideUp 0.35s ease-out ${animationDelay || 0}s forwards`,
        opacity: 0,
        paddingTop: '18px',
      }}
      className="rounded border p-3"
    >
      <div 
        className="absolute"
        style={{ 
          top: '-8px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '18px',
          height: '18px',
          zIndex: 20,
        }}
      >
        <svg viewBox="0 0 24 24" style={{ width: '100%', height: '100%', filter: 'drop-shadow(0 2px 2px rgba(80, 60, 40, 0.25))' }}>
          <defs>
            <linearGradient id={`pinGrad-${node.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#d64545' }} />
              <stop offset="100%" style={{ stopColor: '#a33030' }} />
            </linearGradient>
          </defs>
          <circle cx="12" cy="8" r="6" fill={`url(#pinGrad-${node.id})`} />
          <ellipse cx="10" cy="6" rx="2" ry="1.5" fill="rgba(255,255,255,0.35)" />
          <rect x="11" y="13" width="2" height="7" fill="#b8a080" />
        </svg>
      </div>
      
      <div className="flex flex-col gap-1.5">
        <div className="flex items-start justify-between gap-2">
          <span 
            className="text-sm font-semibold leading-tight"
            style={{ 
              color: colors.text,
              fontFamily: "'Caveat', cursive",
              fontSize: '1.1rem',
            }}
          >
            {node.label}
          </span>
          <span 
            className="text-[10px] font-mono shrink-0 px-1.5 py-0.5 rounded"
            style={{ 
              backgroundColor: `${colors.indicator}15`,
              color: colors.indicator,
              fontWeight: 600
            }}
          >
            {node.probability}%
          </span>
        </div>
        <p 
          className="text-[11px] leading-relaxed line-clamp-2"
          style={{ color: '#5c4a32' }}
        >
          {node.description.brief}
        </p>
      </div>
    </button>
  );
}

function ConnectionLine({
  x1, y1, x2, y2,
  strength,
  type,
  isHighlighted,
  animationDelay,
}: {
  x1: number; y1: number; x2: number; y2: number;
  strength: number;
  type: string;
  isHighlighted: boolean;
  animationDelay?: number;
}) {
  const color = isHighlighted ? 'var(--marker-blue)' : edgeTypeColors[type];
  const strokeWidth = isHighlighted ? 2.5 : strength > 0.7 ? 2 : 1.5;
  const midX = (x1 + x2) / 2;
  const pathLength = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  
  return (
    <path
      d={`M ${x1} ${y1} Q ${midX} ${y1}, ${midX} ${(y1 + y2) / 2} T ${x2} ${y2}`}
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeOpacity={isHighlighted ? 1 : 0.55}
      strokeDasharray={isHighlighted ? 'none' : '5 3'}
      style={{
        strokeDashoffset: pathLength,
        animation: `drawLine 0.6s ease-out ${animationDelay || 0}s forwards`
      }}
    />
  );
}

function ChainMetadataHeader({ metadata }: { metadata: ChainMetadata }) {
  const { t } = useI18n();
  return (
    <div 
      className="flex items-center gap-4 px-1"
      style={{ color: '#8b7355' }}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-wider">{t('graph.confidence')}</span>
        <span className="text-[11px] font-mono font-semibold" style={{ color: '#8a6a40' }}>
          {(metadata.confidence * 100).toFixed(0)}%
        </span>
      </div>
      <div className="w-px h-3" style={{ background: 'rgba(160, 140, 110, 0.3)' }} />
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-wider">{t('graph.depth')}</span>
        <span className="text-[11px] font-mono" style={{ color: '#7a6b55' }}>
          {metadata.maxDepth}
        </span>
      </div>
      <div className="w-px h-3" style={{ background: 'rgba(160, 140, 110, 0.3)' }} />
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-wider">{t('graph.nodes')}</span>
        <span className="text-[11px] font-mono" style={{ color: '#7a6b55' }}>
          {metadata.totalNodes}
        </span>
      </div>
      <div className="w-px h-3" style={{ background: 'rgba(160, 140, 110, 0.3)' }} />
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-wider">{t('panel.evidence')}</span>
        <span className="text-[11px] font-mono" style={{ color: '#7a6b55' }}>
          {metadata.primaryEvidenceCount}
        </span>
      </div>
    </div>
  );
}

function BoardLegend() {
  const { t } = useI18n();
  return (
    <div 
      className="absolute bottom-3 left-3 flex flex-col gap-1.5 text-[10px] px-3 py-2.5 rounded"
      style={{ 
        background: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(4px)',
        border: '1px solid rgba(160, 140, 110, 0.15)',
        color: '#7a6b55',
      }}
    >
      <span 
        className="text-[9px] font-semibold uppercase tracking-wider mb-0.5"
        style={{ fontFamily: "'Caveat', cursive", color: '#6b5a42' }}
      >
        {t('home.legend.title')}
      </span>
      <div className="flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(196, 69, 54, 0.3)' }} />
        <span>{t('graph.legend.cause')}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(70, 130, 180, 0.3)' }} />
        <span>{t('home.legend.effect')}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(180, 140, 80, 0.3)' }} />
        <span>{t('graph.legend.mediator')}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-sm" style={{ background: 'rgba(100, 140, 90, 0.3)' }} />
        <span>{t('panel.evidence')}</span>
      </div>
    </div>
  );
}

function SelectionHint() {
  const { t } = useI18n();
  return (
    <div 
      className="absolute top-4 right-4 flex items-center gap-2 text-[10px] px-3 py-2 rounded"
      style={{ 
        background: 'rgba(255, 255, 255, 0.7)',
        backdropFilter: 'blur(4px)',
        border: '1px solid rgba(160, 140, 110, 0.2)',
        color: '#8b7355',
        animation: 'fadeSlideIn 0.3s ease-out forwards',
      }}
    >
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{t('home.hint.clickNode')}</span>
    </div>
  );
}

export default function ChainView({
  chain,
  selectedNodeId,
  onNodeSelect,
}: ChainViewProps) {
  const { t } = useI18n();
  const { metadata, nodes, edges } = chain;
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 900, height: 600 });

  const nodesByDepth = useMemo(() => {
    const groups: Record<number, ChainNode[]> = {};
    nodes.forEach((node) => {
      if (!groups[node.depth]) groups[node.depth] = [];
      groups[node.depth].push(node);
    });
    return groups;
  }, [nodes]);

  const maxDepth = metadata.maxDepth;

  const ancestorPath = useMemo(() => {
    if (!selectedNodeId) return new Set<string>();
    return getAncestorPath(selectedNodeId, nodes);
  }, [selectedNodeId, nodes]);

  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    const paddingX = 80;
    const paddingY = 100;
    const availableWidth = containerSize.width - paddingX * 2 - CARD_WIDTH;
    const availableHeight = containerSize.height - paddingY * 2 - CARD_HEIGHT;
    
    Object.entries(nodesByDepth).forEach(([depthStr, depthNodes]) => {
      const depth = parseInt(depthStr);
      const x = paddingX + (depth / maxDepth) * availableWidth;
      
      const verticalStep = availableHeight / (depthNodes.length + 1);
      depthNodes.forEach((node, idx) => {
        const y = paddingY + verticalStep * (idx + 1);
        positions[node.id] = { x, y };
      });
    });
    
    return positions;
  }, [nodesByDepth, maxDepth, containerSize]);

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setContainerSize({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const isEdgeHighlighted = (edge: ChainEdge): boolean => {
    if (!selectedNodeId) return false;
    const sourceInPath = ancestorPath.has(edge.source) || edge.source === selectedNodeId;
    const targetInPath = ancestorPath.has(edge.target) || edge.target === selectedNodeId;
    return sourceInPath && targetInPath;
  };

  return (
    <div className="h-full flex flex-col" style={{ background: 'transparent' }}>
      {/* Case File Header Zone - minimal, warm */}
      <div className="shrink-0 px-4 pt-3 pb-2 relative">
        {/* Case file stamp style */}
        <div className="flex items-center gap-2 mb-1">
          <span 
            className="text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-wider"
            style={{ 
              backgroundColor: 'rgba(180, 80, 60, 0.1)',
              color: '#a0503c',
              border: '1px solid rgba(180, 80, 60, 0.2)',
              fontFamily: "'IBM Plex Mono', monospace",
            }}
          >
            {t('home.chain.primary')}
          </span>
          <h2 
            className="text-base font-bold tracking-tight"
            style={{ 
              fontFamily: "'Caveat', cursive",
              color: '#3d3225',
              fontSize: '1.25rem',
            }}
          >
            {metadata.outcomeLabel}
          </h2>
        </div>
        <p 
          className="text-xs mb-2 pl-1 line-clamp-1"
          style={{ color: '#7a6b55' }}
        >
          {metadata.title}
        </p>
        <ChainMetadataHeader metadata={metadata} />
      </div>

      {/* Evidence Board Zone - transparent to show parent cork board */}
      <div 
        ref={containerRef}
        className="flex-1 relative overflow-hidden"
        style={{ background: 'transparent' }}
      >
        {/* Grid overlay */}
        <div 
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(var(--paper-border) 1px, transparent 1px),
              linear-gradient(90deg, var(--paper-border) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px',
            opacity: 'var(--texture-grid)',
          }}
        />

        {/* Depth gradient zones - left (causes) darker */}
        <div 
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'linear-gradient(90deg, rgba(0,0,0,0.015) 0%, transparent 30%, transparent 70%, rgba(0,0,0,0.01) 100%)',
          }}
        />

        {/* Flow direction indicator */}
        <div 
          className="absolute top-4 left-1/2 -translate-x-1/2 flex items-center gap-2 text-[10px] uppercase tracking-wider px-4 py-1.5 rounded"
          style={{ 
            background: 'rgba(255, 255, 255, 0.6)',
            backdropFilter: 'blur(4px)',
            border: '1px solid rgba(160, 140, 110, 0.2)',
            color: '#8b7355',
          }}
        >
          <div className="w-6 h-px" style={{ background: 'rgba(160, 140, 110, 0.4)' }} />
          <span>{t('home.flow.title')}</span>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </div>

        {!selectedNodeId && <SelectionHint />}

        <svg 
          className="absolute inset-0 pointer-events-none"
          width={containerSize.width}
          height={containerSize.height}
        >
          <defs>
            <filter id="lineGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {edges.map((edge, idx) => {
            const sourcePos = nodePositions[edge.source];
            const targetPos = nodePositions[edge.target];
            if (!sourcePos || !targetPos) return null;
            
            const x1 = sourcePos.x + CARD_WIDTH;
            const y1 = sourcePos.y + CARD_HEIGHT / 2;
            const x2 = targetPos.x;
            const y2 = targetPos.y + CARD_HEIGHT / 2;
            
            return (
              <ConnectionLine
                key={edge.id}
                x1={x1} y1={y1} x2={x2} y2={y2}
                strength={edge.strength}
                type={edge.type}
                isHighlighted={isEdgeHighlighted(edge)}
                animationDelay={0.1 + idx * 0.03}
              />
            );
          })}
        </svg>

        {nodes.map((node, idx) => {
          const pos = nodePositions[node.id];
          if (!pos) return null;
          
          const isSelected = selectedNodeId === node.id;
          const isOnPath = isSelected || ancestorPath.has(node.id);
          
          return (
            <EvidenceCard
              key={node.id}
              node={node}
              isSelected={isSelected}
              isOnPath={isOnPath}
              onSelect={() => onNodeSelect?.(node.id)}
              animationDelay={0.15 + idx * 0.04}
              style={{
                left: pos.x,
                top: pos.y,
              }}
            />
          );
        })}

        <BoardLegend />
      </div>

      {/* Analysis Notes Footer Zone - minimal */}
      <div 
        className="shrink-0 px-4 py-2"
        style={{ 
          borderTop: '1px solid rgba(160, 140, 110, 0.15)',
        }}
      >
        <div className="flex items-start gap-2">
          <span 
            className="text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-wider shrink-0"
            style={{ 
              backgroundColor: 'rgba(180, 80, 60, 0.1)',
              color: '#a0503c',
              fontFamily: "'IBM Plex Mono', monospace",
            }}
          >
            {t('panel.counterfactual')}
          </span>
          <p className="text-xs leading-relaxed" style={{ color: '#5c4a32' }}>
            {metadata.counterfactualSummary.description}
          </p>
        </div>
      </div>
    </div>
  );
}
