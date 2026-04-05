
"use client";

import React from "react";
import { Agent } from "@/data/mockData";
import { useI18n } from "@/lib/i18n";

interface AgentListProps {
  agents: Agent[];
}

const stanceStyles: Record<string, string> = {
  support: "text-[var(--thread-success)] bg-[var(--success-bg)]",
  oppose: "text-[var(--marker-red)] bg-[var(--error-bg)]",
  neutral: "text-[var(--ink-500)] bg-[var(--paper-aged)]",
};

export default function AgentList({ agents }: AgentListProps) {
  const { t } = useI18n();
  return (
    <div className="p-5 rounded-lg bg-[var(--paper-white)] border border-[var(--paper-border)] shadow-[var(--paper-shadow)] mb-4">
      <h4 className="text-xs uppercase tracking-widest text-[var(--ink-400)] mb-4 font-semibold">
        {t("panel.agents")}
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
              {a.stance === "support" ? t("debate.footer.support") : a.stance === "oppose" ? t("debate.footer.oppose") : t("debate.footer.neutral")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

