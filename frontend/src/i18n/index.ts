import { createI18n } from "vue-i18n"

import { type Locale, messages } from "./messages"

const STORAGE_KEY = "ar_locale"

function initialLocale(): Locale {
  const saved = localStorage.getItem(STORAGE_KEY)
  return saved === "ru" || saved === "uz" ? saved : "uz" // default: Uzbek
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: initialLocale(),
  fallbackLocale: "uz",
  messages,
})

export function setLocale(locale: Locale) {
  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

export const LOCALES: { code: Locale; label: string }[] = [
  { code: "uz", label: "O'zbekcha" },
  { code: "ru", label: "Русский" },
]
