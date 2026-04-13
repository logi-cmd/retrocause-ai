'use client';

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { CausalNode, CausalEdge } from '@/data/mockData';
import { useI18n, type TranslationKey } from '@/lib/i18n';

interface CausalGraphViewProps {
  nodes: CausalNode[];
  edges: CausalEdge[];
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string) => void;
}

interface NodePosition {
  id: string;
  x: number;
  y: number;
}

const STICKY_COLORS = ['sticky-yellow', 'sticky-cream', 'sticky-pink', 'sticky-blue', 'sticky-mint', 'sticky-lavender'] as const;
type StickyColor = typeof STICKY_COLORS[number];

const STICKY_ROTATIONS: Record<string, number> = {
  'N1': -2,
  'N2': 1.5,
  'N3': -1,
  'N4': 2.5,
  'N5': -1.5,
  'N6': 1,
  'N7': -2.5,
  'N8': 1,
};

function getStickyColor(nodeId: string): StickyColor {
  const hash = nodeId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return STICKY_COLORS[hash % STICKY_COLORS.length];
}

function getStickyRotation(nodeId: string): number {
  return STICKY_ROTATIONS[nodeId] ?? (Math.random() * 4 - 2);
}

const PushpinSVG = () => (
  <svg 
    viewBox="0 0 24 24" 
    className="absolute" 
    style={{ 
      top: '-10px', 
      left: '50%',
      transform: 'translateX(-50%)',
      width: '22px',
      height: '22px',
      zIndex: 20,
      filter: 'drop-shadow(0 2px 3px rgba(80, 60, 40, 0.25))'
    }}
  >
    <defs>
      <linearGradient id="pinRed" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style={{ stopColor: '#d64545' }} />
        <stop offset="100%" style={{ stopColor: '#a33030' }} />
      </linearGradient>
    </defs>
    <circle cx="12" cy="8" r="6" fill="url(#pinRed)" />
    <ellipse cx="10" cy="6" rx="2" ry="1.5" fill="rgba(255,255,255,0.35)" />
    <rect x="11" y="13" width="2" height="8" fill="#b8a080" />
  </svg>
);

const TAG_COLORS: Record<string, { bg: string; color: string }> = {
  cause: { bg: 'rgba(196, 69, 54, 0.15)', color: '#943d30' },
  effect: { bg: 'rgba(70, 130, 180, 0.15)', color: '#4a7a9e' },
  evidence: { bg: 'rgba(100, 140, 90, 0.15)', color: '#5a7a52' },
  mediator: { bg: 'rgba(180, 140, 80, 0.15)', color: '#8a6a40' },
  factor: { bg: 'rgba(140, 100, 160, 0.15)', color: '#6a5080' },
};

const StickyCard = ({ 
  node, 
  rotation, 
  isSelected, 
  onSelect,
  t,
  cardWidth = 160
}: { 
  node: CausalNode; 
  rotation: number;
  isSelected: boolean;
  onSelect?: () => void;
  t: (key: TranslationKey) => string;
  cardWidth?: number;
}) => {
  const stickyColor = getStickyColor(node.id);
  const typeConfig = {
    outcome: { labelKey: 'graph.type.outcome' as TranslationKey, badgeKey: 'graph.badge.outcome' as TranslationKey, tag: 'effect' as const },
    factor: { labelKey: 'graph.type.factor' as TranslationKey, badgeKey: 'graph.badge.factor' as TranslationKey, tag: 'factor' as const },
    intermediate: { labelKey: 'graph.type.intermediate' as TranslationKey, badgeKey: 'graph.badge.intermediate' as TranslationKey, tag: 'mediator' as const },
  };
  const config = typeConfig[node.type];
  const tagStyle = TAG_COLORS[config.tag] || TAG_COLORS.evidence;
  
  return (
    <div
      className={`absolute cursor-pointer select-none transition-all duration-200 ${stickyColor}`}
      style={{
        width: `${cardWidth}px`,
        padding: '22px 14px 14px 14px',
        borderRadius: '2px',
        boxShadow: isSelected 
          ? '0 4px 12px rgba(80, 60, 40, 0.2)' 
          : '0 3px 8px rgba(80, 60, 40, 0.15), 0 1px 3px rgba(80, 60, 40, 0.1)',
        transform: `rotate(${rotation}deg)`,
        transformOrigin: 'top center',
        borderBottom: '3px solid rgba(180, 160, 120, 0.3)',
      }}
      onClick={onSelect}
    >
      <PushpinSVG />
      
      <div style={{ transform: `rotate(${-rotation}deg)` }}>
        <div 
          className="mb-1" 
          style={{ 
            fontFamily: "'Caveat', cursive", 
            fontSize: '1.15rem', 
            color: '#3d3225',
            lineHeight: 1.2,
            fontWeight: 600,
          }}
        >
          {node.label}
        </div>
        <div 
          className="text-xs uppercase tracking-wider mb-2 pb-1.5 border-b"
          style={{ 
            color: '#7a6b55',
            borderColor: 'rgba(160, 140, 110, 0.3)',
            fontSize: '0.6rem',
            letterSpacing: '0.06em',
          }}
        >
          {t(node.type === 'outcome' ? 'graph.type.outcome' : node.type === 'factor' ? 'graph.type.factor' : 'graph.type.intermediate')}
        </div>
        <div className="text-xs leading-relaxed mb-2" style={{ color: '#5c4a32' }}>
          P: {node.probability}%
        </div>
        <span 
          className="inline-block px-2 py-1 rounded text-xs font-semibold uppercase tracking-wide"
          style={{ 
            background: tagStyle.bg,
            color: tagStyle.color,
            fontSize: '0.55rem',
            fontWeight: 600,
          }}
        >
          {t(config.badgeKey)}
        </span>
      </div>
    </div>
  );
};

const CARD_WIDTH = 160;

/**
 * Compute a red-string-style bezier path between two pin locations.
 * The control point sags below the lower endpoint, proportional to
 * the distance between the two points (gravity effect, max 35 px).
 */
function computeRedStringPath(
  x1: number, y1: number,
  x2: number, y2: number
): string {
  const dist = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
  const sag = Math.min(dist * 0.12, 35);
  const midX = (x1 + x2) / 2;
  const midY = Math.max(y1, y2) + sag;
  return `M ${x1} ${y1} Q ${midX} ${midY} ${x2} ${y2}`;
}

export default function CausalGraphView({ nodes, edges, selectedNodeId, onNodeSelect }: CausalGraphViewProps) {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const [positions, setPositions] = useState<NodePosition[]>([]);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updatePositions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setContainerSize({ width: rect.width, height: rect.height });
        
        if (nodes.length > 0 && positions.length === 0) {
          setPositions(nodes.map((node) => ({
            id: node.id,
            x: ((node.x ?? 50) / 100) * rect.width,
            y: ((node.y ?? 50) / 100) * rect.height,
          })));
        }
      }
    };
    
    updatePositions();
    window.addEventListener('resize', updatePositions);
    return () => window.removeEventListener('resize', updatePositions);
  }, [nodes]);

  const getPointerPosition = useCallback((e: React.PointerEvent) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const rect = containerRef.current.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }, []);

  const handlePointerDown = useCallback((e: React.PointerEvent, nodeId: string) => {
    e.preventDefault();
    e.stopPropagation();
    containerRef.current?.setPointerCapture(e.pointerId);

    const pos = positions.find((p) => p.id === nodeId);
    if (pos) {
      const { x, y } = getPointerPosition(e);
      setDragOffset({ x: x - pos.x, y: y - pos.y });
      setDragging(nodeId);
    }
  }, [positions, getPointerPosition]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging || !containerRef.current) return;

    const { x, y } = getPointerPosition(e);
    const newX = Math.max(20, Math.min(containerSize.width - 180, x - dragOffset.x));
    const newY = Math.max(20, Math.min(containerSize.height - 120, y - dragOffset.y));

    setPositions((prev) =>
      prev.map((p) => (p.id === dragging ? { ...p, x: newX, y: newY } : p))
    );
  }, [dragging, dragOffset, getPointerPosition, containerSize]);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (dragging) {
      containerRef.current?.releasePointerCapture(e.pointerId);
      setDragging(null);
    }
  }, [dragging]);

  const rotations = useMemo(() => {
    return nodes.reduce((acc, node) => {
      acc[node.id] = getStickyRotation(node.id);
      return acc;
    }, {} as Record<string, number>);
  }, [nodes]);

  const edgesWithPositions = useMemo(() => {
    return edges.map((edge) => {
      const sourcePos = positions.find((p) => p.id === edge.source);
      const targetPos = positions.find((p) => p.id === edge.target);
      if (!sourcePos || !targetPos) return null;

      const dx = targetPos.x - sourcePos.x;
      const spreadX = dx === 0 ? 0 : Math.sign(dx) * 15;

      const x1 = sourcePos.x + CARD_WIDTH / 2 + spreadX;
      const y1 = sourcePos.y + 2;
      const x2 = targetPos.x + CARD_WIDTH / 2 - spreadX;
      const y2 = targetPos.y + 2;

      return {
        ...edge,
        path: computeRedStringPath(x1, y1, x2, y2),
      };
    }).filter(Boolean);
  }, [edges, positions, containerSize]);

  const handleNodeClick = useCallback((nodeId: string) => {
    onNodeSelect?.(nodeId === selectedNodeId ? '' : nodeId);
  }, [selectedNodeId, onNodeSelect]);

  if (positions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center" style={{ color: '#8b7355' }}>
        {t("graph.loadingText")}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-full relative overflow-hidden"
      style={{ background: 'transparent' }}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ zIndex: 5 }}
      >
        {edgesWithPositions.map((edge) => {
          if (!edge) return null;
          return (
            <path
              key={edge.id}
              d={edge.path}
              stroke="#c44536"
              strokeWidth="2.5"
              fill="none"
              opacity={dragging ? 0.7 : 0.7}
              strokeLinecap="round"
            />
          );
        })}
      </svg>

      {positions.map((pos) => {
        const node = nodes.find((n) => n.id === pos.id);
        if (!node) return null;
        const isDragging = dragging === node.id;
        const isHovered = hoveredNode === node.id;

        return (
          <div
            key={node.id}
            className="absolute"
            style={{
              left: pos.x,
              top: pos.y,
              zIndex: isDragging ? 50 : isHovered ? 20 : 10,
              animation: `scaleIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards`,
            }}
            onPointerDown={(e) => handlePointerDown(e, node.id)}
            onPointerEnter={() => setHoveredNode(node.id)}
            onPointerLeave={() => setHoveredNode(null)}
          >
            <StickyCard
              node={node}
              rotation={rotations[node.id]}
              isSelected={selectedNodeId === node.id}
              onSelect={() => handleNodeClick(node.id)}
              t={t}
              cardWidth={CARD_WIDTH}
            />
          </div>
        );
      })}

      <div 
        className="absolute bottom-4 right-4 text-xs px-3 py-2 rounded z-20"
        style={{ 
          background: 'rgba(250, 246, 238, 0.9)',
          backdropFilter: 'blur(4px)',
          border: '1px solid rgba(160, 140, 110, 0.2)',
          color: '#8b7355',
          fontFamily: "'IBM Plex Mono', monospace",
        }}
      >
        {nodes.length} {t("graph.nodes")} / {edges.length} {t("graph.connections")}
      </div>
    </div>
  );
}
