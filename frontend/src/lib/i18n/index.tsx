"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import zh, { type TranslationDict, type TranslationKey } from "./zh";
import en from "./en";
import {
  DEFAULT_LOCALE,
  LOCALE_STORAGE_KEY,
  type Locale,
} from "./types";

type I18nContextValue = {
  locale: Locale;
  setLocale: (next: Locale) => void;
  t: (key: TranslationKey) => string;
  dict: TranslationDict;
};

const I18nContext = createContext<I18nContextValue | null>(null);

const DICTS: Record<Locale, TranslationDict> = { zh, en };

function readStoredLocale(): Locale {
  if (typeof window === "undefined") return DEFAULT_LOCALE;
  try {
    const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    if (stored === "zh" || stored === "en") return stored;
  } catch {
    // localStorage may be blocked in some environments
  }
  return DEFAULT_LOCALE;
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setLocaleState(readStoredLocale());
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    try {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, next);
    } catch {
      // silent — non-critical persistence
    }
  }, []);

  const dict = DICTS[locale];

  const t = useCallback(
    (key: TranslationKey): string => dict[key],
    [dict],
  );

  const value = useMemo<I18nContextValue>(
    () => ({ locale, setLocale, t, dict }),
    [locale, setLocale, t, dict],
  );

  return (
    <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
  );
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within an <I18nProvider>");
  }
  return ctx;
}

export { LOCALES, LOCALE_LABELS, DEFAULT_LOCALE } from "./types";
export type { Locale } from "./types";
export type { TranslationKey } from "./zh";
