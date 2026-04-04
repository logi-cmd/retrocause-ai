/** Supported locales */
export type Locale = "zh" | "en";

/** All locale values, useful for iteration */
export const LOCALES: readonly Locale[] = ["zh", "en"] as const;

/** Display names for locale picker UI */
export const LOCALE_LABELS: Record<Locale, string> = {
  zh: "中文",
  en: "English",
};

/** Default locale used when nothing is stored */
export const DEFAULT_LOCALE: Locale = "zh";

/** localStorage key for persisting locale choice */
export const LOCALE_STORAGE_KEY = "retrocause-locale";
