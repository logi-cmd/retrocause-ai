
"use client";

import React from "react";
import { Agent } from "@/data/mockData";

interface AgentListProps {
  agents: Agent[];
}

const stanceStyles: Record<string, string> = {
  support: "text-[var(--thread-success)] bg-[var(--success-bg)]",
  oppose: "text-[var(--marker-red)] bg-[var(--error-bg)]",
  neutral: "text-[var(--ink-500)] bg-[var(--paper-aged)]",
};

export default function AgentList({ agents }: AgentListProps) {
  return (
    <div className="p-5 rounded-lg bg-[var(--paper-white)] border border-[var(--paper-border)] shadow-[var(--paper-shadow)] mb-4">
      <h4 className="text-xs uppercase tracking-widest text-[var(--ink-400)] mb-4 font-semibold">
        参与 Agent
      </h4>
      <div className="space-y-3">
        {agents.map((a) => (
          <div
            key={a.id}
            className="flex items-center justify-between p-3 bg-[var(--paper-aged)] rounded-lg border border-[var(--paper-border)]"
          >
            <div>
              <span className="text-sm font-semibold text-[var(--ink-700)]">{a.name}</span>
              <span className="text-xs text-[var(--marker-blue)] ml-2 bg-[var(--info-bg)] px-2 py-0.5 rounded-full">
                {a.role}
              </span>
            </div>
            <span className={`badge border-none px-3 py-1 rounded-md font-medium shadow-sm ${stanceStyles[a.stance]}`}>
              {a.stance === "support" ? "支持" : a.stance === "oppose" ? "反对" : "中立"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

