'use client';

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { CausalNode, CausalEdge } from '@/data/mockData';
import { useI18n, type TranslationKey } from '@/lib/i18n';
import { StickyCard, type StickyCardNote } from '@/lib/sticky-card';
import { buildEdgePath } from '@/lib/sticky-graph-layout';

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

function toLegacyStickyNote(
  node: CausalNode,
  position: NodePosition,
  rotation: number,
  t: (key: TranslationKey) => string,
  cardWidth = CARD_WIDTH
): StickyCardNote {
  const stickyColor = getStickyColor(node.id);
  const typeConfig = {
    outcome: { labelKey: 'graph.type.outcome' as TranslationKey, badgeKey: 'graph.badge.outcome' as TranslationKey, tag: 'effect' as const },
    factor: { labelKey: 'graph.type.factor' as TranslationKey, badgeKey: 'graph.badge.factor' as TranslationKey, tag: 'factor' as const },
    intermediate: { labelKey: 'graph.type.intermediate' as TranslationKey, badgeKey: 'graph.badge.intermediate' as TranslationKey, tag: 'mediator' as const },
  };
  const config = typeConfig[node.type];
  return {
    id: node.id,
    title: node.label,
    depth: 0,
    detail: `${t(config.labelKey)} · P: ${node.probability ?? 0}%`,
    tag: t(config.badgeKey),
    tagClass: config.tag,
    color: stickyColor,
    top: position.y,
    left: position.x,
    rotate: rotation,
    width: cardWidth,
    height: 120,
  };
}

const CARD_WIDTH = 160;

// Legacy canvas view. The homepage evidence board is the canonical graph/card path;
// this view stays for secondary mock-data development surfaces and reuses shared path math.
export default function CausalGraphView({ nodes, edges, selectedNodeId, onNodeSelect }: CausalGraphViewProps) {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const [positions, setPositions] = useState<NodePosition[]>([]);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
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
  }, [nodes, positions.length]);

  const getPointerPosition = useCallback((e: React.PointerEvent) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const rect = containerRef.current.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }, []);

  const handleCardMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>, nodeId: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const pos = positions.find((p) => p.id === nodeId);
    if (pos) {
      setDragOffset({ x: e.clientX - rect.left - pos.x, y: e.clientY - rect.top - pos.y });
      setDragging(nodeId);
    }
  }, [positions]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging || !containerRef.current) return;

    const { x, y } = getPointerPosition(e);
    const newX = Math.max(20, Math.min(containerSize.width - 180, x - dragOffset.x));
    const newY = Math.max(20, Math.min(containerSize.height - 120, y - dragOffset.y));

    setPositions((prev) =>
      prev.map((p) => (p.id === dragging ? { ...p, x: newX, y: newY } : p))
    );
  }, [dragging, dragOffset, getPointerPosition, containerSize]);

  const handlePointerUp = useCallback(() => {
    if (dragging) {
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
        path: buildEdgePath(x1, y1, x2, y2, 1).d,
      };
    }).filter(Boolean);
  }, [edges, positions]);

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
        const note = toLegacyStickyNote(node, pos, rotations[node.id], t, CARD_WIDTH);

        return (
          <StickyCard
            key={node.id}
            note={note}
            isSelected={selectedNodeId === node.id}
            isDragging={isDragging}
            depthLabel={t("graph.nodes")}
            onClick={() => handleNodeClick(node.id)}
            onMouseDown={(event) => handleCardMouseDown(event, node.id)}
          />
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
