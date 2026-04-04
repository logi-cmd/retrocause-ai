import React from "react";

interface ConsoleLayoutProps {
  leftPanel: React.ReactNode;
  mainCanvas: React.ReactNode;
  rightPanel: React.ReactNode;
}

export default function ConsoleLayout({
  leftPanel,
  mainCanvas,
  rightPanel,
}: ConsoleLayoutProps) {
  return (
    <div 
      className="flex flex-1 overflow-hidden relative"
      style={{ background: 'transparent' }}
    >
      <aside 
        className="shrink-0 overflow-hidden flex flex-col z-50"
        style={{ 
          width: '180px',
          background: 'rgba(250, 246, 238, 0.7)',
          backdropFilter: 'blur(4px)',
          borderRight: '1px solid rgba(160, 140, 110, 0.15)',
        }}
      >
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {leftPanel}
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden relative min-w-0 z-10">
        {mainCanvas}
      </main>

      <aside 
        className="shrink-0 overflow-hidden flex flex-col z-50"
        style={{ 
          width: '180px',
          background: 'rgba(250, 246, 238, 0.7)',
          backdropFilter: 'blur(4px)',
          borderLeft: '1px solid rgba(160, 140, 110, 0.15)',
        }}
      >
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {rightPanel}
        </div>
      </aside>
    </div>
  );
}
