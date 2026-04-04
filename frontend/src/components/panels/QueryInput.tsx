
"use client";

import React from "react";
import { useI18n } from "@/lib/i18n";

interface QueryInputProps {
  value?: string;
  onChange?: (value: string) => void;
  onSubmit?: () => void;
}

export default function QueryInput({
  value = "",
  onChange,
  onSubmit,
}: QueryInputProps) {
  const { t } = useI18n();
  return (
    <div className="p-4 mb-4">
      <label className="block text-xs uppercase tracking-widest text-[var(--ink-400)] mb-3 font-semibold">
        {t("query.label")}
      </label>
      <textarea
        className="w-full min-h-24 resize-none py-3 text-sm mb-3 px-4 rounded-lg border border-[var(--paper-border)] bg-[var(--paper-white)] text-[var(--ink-700)] placeholder:text-[var(--ink-300)] focus:border-[var(--marker-blue)] focus:ring-2 focus:ring-[var(--marker-blue)]/10 outline-none transition-all"
        placeholder={t("query.placeholderExample")}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
      />
      <p className="text-xs text-[var(--ink-400)] mb-3 leading-relaxed">
        {t("query.helper")}
      </p>
      <button
        className="neo-btn w-full py-3 font-semibold"
        style={{ color: "var(--marker-blue)" }}
        onClick={onSubmit}
      >
        {t("query.submit")}
      </button>
    </div>
  );
}
