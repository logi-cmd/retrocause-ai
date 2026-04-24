import type { MouseEvent } from "react";

export type StickyCardNote = {
  id: string;
  title: string;
  depth: number;
  detail: string;
  tag: string;
  tagClass: string;
  color: string;
  top: number;
  left: number;
  rotate: number;
  width: number;
  height: number;
};

type StickyCardProps = {
  note: StickyCardNote;
  isSelected: boolean;
  isDragging: boolean;
  depthLabel: string;
  onClick: () => void;
  onMouseDown: (event: MouseEvent<HTMLDivElement>) => void;
};

function Pushpin() {
  return (
    <svg
      className="absolute pointer-events-none"
      style={{
        top: "-10px",
        left: "50%",
        transform: "translateX(-50%)",
        width: "22px",
        height: "22px",
        filter: "drop-shadow(1px 2px 3px rgba(60, 40, 20, 0.35))",
        zIndex: 20,
      }}
      viewBox="0 0 24 24"
    >
      <defs>
        <linearGradient id="pinRed" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: "#e05555" }} />
          <stop offset="45%" style={{ stopColor: "#c03535" }} />
          <stop offset="100%" style={{ stopColor: "#8a2020" }} />
        </linearGradient>
        <radialGradient id="pinHead3D" cx="35%" cy="30%" r="65%">
          <stop offset="0%" style={{ stopColor: "#f07070" }} />
          <stop offset="50%" style={{ stopColor: "#b83030" }} />
          <stop offset="100%" style={{ stopColor: "#701818" }} />
        </radialGradient>
        <linearGradient id="pinMetal" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style={{ stopColor: "#d4c4a4" }} />
          <stop offset="40%" style={{ stopColor: "#f0e0c0" }} />
          <stop offset="60%" style={{ stopColor: "#c8b898" }} />
          <stop offset="100%" style={{ stopColor: "#a89878" }} />
        </linearGradient>
      </defs>
      <circle cx="12" cy="8" r="7" fill="url(#pinHead3D)" />
      <ellipse cx="9.5" cy="5.5" rx="2.5" ry="1.8" fill="rgba(255,255,255,0.45)" />
      <circle cx="14" cy="10.5" r="1.2" fill="rgba(0,0,0,0.15)" />
      <rect x="11.2" y="14" width="1.6" height="7" rx="0.8" fill="url(#pinMetal)" />
    </svg>
  );
}

export function StickyCard({
  note,
  isSelected,
  isDragging,
  depthLabel,
  onClick,
  onMouseDown,
}: StickyCardProps) {
  return (
    <div
      className={`sticky-card ${note.color} ${isSelected ? "ring-2 ring-[#a0503c]/40" : ""}`}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      data-testid={`sticky-card-${note.id}`}
      style={{
        position: "absolute",
        top: note.top,
        left: note.left,
        width: `${note.width}px`,
        padding: "22px 14px 14px",
        rotate: `${note.rotate}deg`,
        cursor: isDragging ? "grabbing" : "grab",
        transition: isDragging ? "none" : "box-shadow 0.18s ease, transform 0.18s ease",
        zIndex: isDragging ? 40 : isSelected ? 28 : 18,
        transform: isDragging ? "scale(1.02)" : undefined,
        willChange: isDragging ? "top, left, transform" : undefined,
      }}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
      onMouseDown={onMouseDown}
    >
      <Pushpin />
      <div className="tape-strip tape-left" />
      <div className="tape-strip tape-right" />
      <div
        className="paper-texture"
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "2px",
          pointerEvents: "none",
          overflow: "hidden",
        }}
      />
      <div style={{ transform: `rotate(${-note.rotate}deg)`, position: "relative", zIndex: 1 }}>
        <div className="card-title">{note.title}</div>
        <div className="card-subtitle">
          {depthLabel} {note.depth}
        </div>
        <div className="card-detail">{note.detail}</div>
        <span className={`card-tag ${note.tagClass}`}>{note.tag}</span>
      </div>
    </div>
  );
}
