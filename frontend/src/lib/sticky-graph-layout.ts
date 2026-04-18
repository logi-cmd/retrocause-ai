import type { ChainEdge, ChainNode } from "@/data/mockData";
import type { StickyCardNote } from "@/lib/sticky-card";

const STICKY_COLORS = [
  "sticky-yellow",
  "sticky-cream",
  "sticky-blue",
  "sticky-pink",
  "sticky-mint",
  "sticky-lavender",
] as const;

type StickyColor = (typeof STICKY_COLORS)[number];

const NOTE_DIMS: Record<StickyColor, [number, number]> = {
  "sticky-yellow": [180, 130],
  "sticky-cream": [170, 125],
  "sticky-blue": [165, 122],
  "sticky-pink": [160, 120],
  "sticky-mint": [170, 125],
  "sticky-lavender": [155, 118],
};

export const CANVAS_HEADER_HEIGHT = 64;
export const NOTE_TOP_SAFE_PX = 24;
export const NOTE_BOTTOM_SAFE_PX = 42;
export const NOTE_VISUAL_HEIGHT_BUFFER = 14;
export const PANEL_SAFE_LEFT_OPEN = 296;
export const PANEL_SAFE_RIGHT_OPEN = 356;
export const PANEL_SAFE_CLOSED = 24;
const NARROW_BOARD_WIDTH = 720;
const NARROW_PANEL_SAFE_OPEN = 48;

export interface StickyNote extends Omit<StickyCardNote, "color"> {
  color: StickyColor;
}

export interface CausalStringPath {
  id: string;
  source: string;
  target: string;
  d: string;
  opacity: number;
  width: number;
}

function getTagClass(type: ChainNode["type"]): string {
  switch (type) {
    case "outcome":
      return "tag-effect";
    case "factor":
      return "tag-cause";
    case "intermediate":
      return "tag-mediator";
    default:
      return "tag-cause";
  }
}

function getStickyColor(index: number, depth: number): StickyColor {
  const combined = (index * 3 + depth * 2) % STICKY_COLORS.length;
  return STICKY_COLORS[combined];
}

export function computeLayout(
  nodes: ChainNode[],
  boardWidth: number,
  boardHeight: number,
  headerHeight: number,
  getLabel: (type: ChainNode["type"]) => string,
  leftPanelOpen = true,
  rightPanelOpen = true
): StickyNote[] {
  if (nodes.length === 0) return [];

  const safeBoardWidth = Math.max(1, Number.isFinite(boardWidth) ? boardWidth : 1);
  const safeBoardHeight = Math.max(1, Number.isFinite(boardHeight) ? boardHeight : 1);
  const isNarrowBoard = safeBoardWidth <= NARROW_BOARD_WIDTH;
  const leftMargin = isNarrowBoard
    ? leftPanelOpen
      ? NARROW_PANEL_SAFE_OPEN
      : PANEL_SAFE_CLOSED
    : leftPanelOpen
      ? Math.min(340, Math.max(230, safeBoardWidth * 0.22))
      : 88;
  const rightMargin = isNarrowBoard
    ? rightPanelOpen
      ? NARROW_PANEL_SAFE_OPEN
      : PANEL_SAFE_CLOSED
    : rightPanelOpen
      ? Math.min(400, Math.max(260, safeBoardWidth * 0.26))
      : 88;
  const canvasHeight = Math.max(1, safeBoardHeight - headerHeight);
  const topMargin = NOTE_TOP_SAFE_PX;
  const bottomMargin = NOTE_BOTTOM_SAFE_PX + NOTE_VISUAL_HEIGHT_BUFFER;
  const usableWidth = Math.max(1, safeBoardWidth - leftMargin - rightMargin);
  const usableHeight = Math.max(1, canvasHeight - topMargin - bottomMargin);

  const rotations = [-3, -1.5, 0.5, 2, -2, 1.5, -0.5, 3, -2.5, 1];
  const n = nodes.length;
  const sortedNodes = [...nodes].sort((a, b) => a.depth - b.depth);
  const cols = Math.min(n, Math.max(2, Math.ceil(Math.sqrt(n * (usableWidth / usableHeight)))));
  const rows = Math.ceil(n / cols);
  const cellW = usableWidth / cols;
  const cellH = usableHeight / rows;
  const prelimPositions: { node: ChainNode; x: number; y: number }[] = [];

  sortedNodes.forEach((node, i) => {
    const row = Math.floor(i / cols);
    const colInRow = i % cols;
    const col = row % 2 === 0 ? colInRow : cols - 1 - colInRow;
    const cx = leftMargin + col * cellW + cellW / 2;
    const cy = topMargin + row * cellH + cellH / 2;
    const ox = ((i * 37) % 17 - 8) * 2;
    const oy = ((i * 23) % 13 - 6) * 2;

    prelimPositions.push({ node, x: cx + ox, y: cy + oy });
  });

  const minGapX = 210;
  const minGapY = 170;

  for (let pass = 0; pass < 10; pass++) {
    for (let i = 0; i < prelimPositions.length; i++) {
      for (let j = i + 1; j < prelimPositions.length; j++) {
        const a = prelimPositions[i];
        const b = prelimPositions[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const overlapX = minGapX - Math.abs(dx);
        const overlapY = minGapY - Math.abs(dy);

        if (overlapX > 0 && overlapY > 0) {
          const pushX = overlapX / 2 + 8;
          const pushY = overlapY / 2 + 8;
          if (overlapX < overlapY) {
            a.x -= Math.sign(dx || 1) * pushX;
            b.x += Math.sign(dx || 1) * pushX;
          } else {
            a.y -= Math.sign(dy || 1) * pushY;
            b.y += Math.sign(dy || 1) * pushY;
          }
        }
      }
    }
  }

  return prelimPositions.map((pos, i) => {
    const color = getStickyColor(i, pos.node.depth);
    const [width, height] = NOTE_DIMS[color];
    const minLeft = Math.min(leftMargin, Math.max(0, safeBoardWidth - width));
    const maxLeft = Math.max(minLeft, safeBoardWidth - rightMargin - width);
    const left = Math.max(minLeft, Math.min(pos.x, maxLeft));
    const visualHeight = height + NOTE_VISUAL_HEIGHT_BUFFER;
    const maxTop = canvasHeight - bottomMargin - visualHeight;
    const row = Math.floor(i / cols);
    const rowOffset = ((i * 23) % 13 - 6) * 2;
    const layoutTopMargin = Math.min(96, Math.max(NOTE_TOP_SAFE_PX + 48, canvasHeight * 0.12));
    const rowRatio = rows > 1 ? row / (rows - 1) : 0.5;
    const intendedTop =
      rows > 1
        ? layoutTopMargin + rowRatio * Math.max(0, maxTop - layoutTopMargin) + rowOffset
        : topMargin + Math.max(0, (canvasHeight - topMargin - bottomMargin - visualHeight) / 2);
    const top = Math.max(topMargin, Math.min(intendedTop, maxTop));

    return {
      id: pos.node.id,
      title: pos.node.label,
      depth: pos.node.depth,
      detail: pos.node.description.brief,
      tag: getLabel(pos.node.type),
      tagClass: getTagClass(pos.node.type),
      color,
      top,
      left,
      rotate: rotations[i % rotations.length],
      width,
      height,
    };
  });
}

export function getPushpinAnchor(note: StickyNote): [number, number] {
  return [note.left + note.width / 2, note.top - 2];
}

export function buildEdgePath(
  sx: number,
  sy: number,
  tx: number,
  ty: number,
  strength: number
): { d: string; opacity: number; width: number } {
  if (![sx, sy, tx, ty, strength].every(Number.isFinite)) {
    return { d: "", opacity: 0, width: 0 };
  }

  const dx = tx - sx;
  const dy = ty - sy;
  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);
  const dist = Math.sqrt(dx * dx + dy * dy);
  const cpOffset = Math.min(Math.max(absDx, absDy) * 0.4, 120);
  const sag = Math.min(dist * 0.15, 40) * Math.sign(dy === 0 ? 1 : dy);

  let c1x: number;
  let c1y: number;
  let c2x: number;
  let c2y: number;

  if (absDy > absDx * 1.5) {
    c1x = sx;
    c1y = sy + cpOffset * Math.sign(dy) + sag * 0.3;
    c2x = tx;
    c2y = ty - cpOffset * Math.sign(dy) + sag * 0.3;
  } else if (absDx > absDy * 1.5) {
    c1x = sx + cpOffset * Math.sign(dx);
    c1y = sy + sag * 0.4;
    c2x = tx - cpOffset * Math.sign(dx);
    c2y = ty + sag * 0.4;
  } else {
    c1x = sx + cpOffset * 0.7 * Math.sign(dx);
    c1y = sy + cpOffset * 0.3 * Math.sign(dy) + sag * 0.5;
    c2x = tx - cpOffset * 0.7 * Math.sign(dx);
    c2y = ty - cpOffset * 0.3 * Math.sign(dy) + sag * 0.5;
  }

  return {
    d: `M ${sx} ${sy} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${tx} ${ty}`,
    opacity: 0.35 + strength * 0.35,
    width: 1 + strength * 1.5,
  };
}

export function computeCausalStrings(
  notes: StickyNote[],
  edges: ChainEdge[]
): CausalStringPath[] {
  const noteMap = new Map(notes.map((n) => [n.id, n]));
  const paths: CausalStringPath[] = [];

  for (const edge of edges) {
    const source = noteMap.get(edge.source);
    const target = noteMap.get(edge.target);
    if (!source || !target) continue;

    const [sx, sy] = getPushpinAnchor(source);
    const [tx, ty] = getPushpinAnchor(target);
    const strength = Number.isFinite(edge.strength) ? edge.strength : 0;
    const path = buildEdgePath(sx, sy, tx, ty, strength);
    if (!path.d) continue;

    paths.push({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      ...path,
    });
  }

  return paths;
}
