<script setup lang="ts">
import { Check, ChevronDown } from "lucide-vue-next"
import { onBeforeUnmount, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"

import { LOCALES, setLocale } from "@/i18n"
import type { Locale } from "@/i18n/messages"

const FLAGS: Record<Locale, string> = { uz: "🇺🇿", ru: "🇷🇺" }

const { locale } = useI18n()
const open = ref(false)
const root = ref<HTMLElement | null>(null)

function choose(code: Locale) {
  setLocale(code)
  open.value = false
}

function onClickOutside(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false
}
onMounted(() => document.addEventListener("click", onClickOutside))
onBeforeUnmount(() => document.removeEventListener("click", onClickOutside))
</script>

<template>
  <div ref="root" class="relative">
    <button
      class="flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-sm font-medium hover:bg-accent"
      @click="open = !open"
    >
      <span class="text-base leading-none">{{ FLAGS[locale as Locale] }}</span>
      <span class="hidden sm:inline">{{ LOCALES.find((l) => l.code === locale)?.label }}</span>
      <ChevronDown class="h-3.5 w-3.5 text-muted-foreground" />
    </button>
    <div
      v-if="open"
      class="absolute right-0 z-50 mt-1 w-44 overflow-hidden rounded-md border bg-popover py-1 shadow-md"
    >
      <button
        v-for="l in LOCALES"
        :key="l.code"
        class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
        @click="choose(l.code)"
      >
        <span class="text-base leading-none">{{ FLAGS[l.code] }}</span>
        <span class="flex-1 text-left">{{ l.label }}</span>
        <Check v-if="locale === l.code" class="h-4 w-4 text-primary" />
      </button>
    </div>
  </div>
</template>
