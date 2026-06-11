import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function scoreColor(pct: number | null | undefined): string {
  if (pct == null) return "text-muted-foreground"
  if (pct >= 75) return "text-green-600"
  if (pct >= 50) return "text-amber-600"
  return "text-red-600"
}

export function scoreBg(pct: number | null | undefined): string {
  if (pct == null) return "bg-muted"
  if (pct >= 75) return "bg-green-500"
  if (pct >= 50) return "bg-amber-500"
  return "bg-red-500"
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}
