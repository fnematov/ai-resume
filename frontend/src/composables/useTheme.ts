import { ref } from "vue"

export type Theme = "system" | "light" | "dark"

const KEY = "ar_theme"
const media = window.matchMedia("(prefers-color-scheme: dark)")
const theme = ref<Theme>(((): Theme => {
  const saved = localStorage.getItem(KEY)
  return saved === "light" || saved === "dark" || saved === "system" ? saved : "system"
})())

function isDark(t: Theme): boolean {
  return t === "dark" || (t === "system" && media.matches)
}

function apply() {
  document.documentElement.classList.toggle("dark", isDark(theme.value))
}

// Follow the OS when the user picked "system".
media.addEventListener("change", () => {
  if (theme.value === "system") apply()
})
apply()

export function useTheme() {
  function setTheme(t: Theme) {
    theme.value = t
    localStorage.setItem(KEY, t)
    apply()
  }
  return { theme, setTheme }
}
