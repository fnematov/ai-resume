<script setup lang="ts">
import { Check, Monitor, Moon, Sun } from "lucide-vue-next"
import { onBeforeUnmount, onMounted, ref } from "vue"

import { type Theme, useTheme } from "@/composables/useTheme"

const { theme, setTheme } = useTheme()
const open = ref(false)
const root = ref<HTMLElement | null>(null)

const OPTIONS: { value: Theme; label: string; icon: typeof Monitor }[] = [
  { value: "system", label: "theme.system", icon: Monitor },
  { value: "light", label: "theme.light", icon: Sun },
  { value: "dark", label: "theme.dark", icon: Moon },
]
const ICON = { system: Monitor, light: Sun, dark: Moon }

function choose(t: Theme) {
  setTheme(t)
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
      class="grid h-8 w-8 place-items-center rounded-md border hover:bg-accent"
      :title="$t('theme.label')"
      @click="open = !open"
    >
      <component :is="ICON[theme]" class="h-4 w-4" />
    </button>
    <div
      v-if="open"
      class="absolute right-0 z-50 mt-1 w-40 overflow-hidden rounded-md border bg-popover py-1 shadow-md"
    >
      <button
        v-for="o in OPTIONS"
        :key="o.value"
        class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
        @click="choose(o.value)"
      >
        <component :is="o.icon" class="h-4 w-4 text-muted-foreground" />
        <span class="flex-1 text-left">{{ $t(o.label) }}</span>
        <Check v-if="theme === o.value" class="h-4 w-4 text-primary" />
      </button>
    </div>
  </div>
</template>
