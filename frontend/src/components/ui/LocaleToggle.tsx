"use client";

import { useI18n, LOCALE_LABELS, type Locale } from "@/lib/i18n";

export default function LocaleToggle() {
  const { locale, setLocale } = useI18n();

  const nextLocale: Locale = locale === "zh" ? "en" : "zh";

  return (
    <button
      type="button"
      onClick={() => setLocale(nextLocale)}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors duration-200"
      style={{
        color: "var(--ink-500)",
        border: "1px solid var(--paper-border)",
        background: "var(--paper-cream)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.color = "var(--ink-700)";
        e.currentTarget.style.background = "var(--paper-aged)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.color = "var(--ink-500)";
        e.currentTarget.style.background = "var(--paper-cream)";
      }}
      aria-label={`Switch language to ${LOCALE_LABELS[nextLocale]}`}
    >
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M5 8l6 6" />
        <path d="M4 14l6-6 2-3" />
        <path d="M2 5h12" />
        <path d="M14 18h6" />
        <path d="M22 22l-5 10-5 18h6" />
      </svg>
      <span>{LOCALE_LABELS[locale]}</span>
    </button>
  );
}
