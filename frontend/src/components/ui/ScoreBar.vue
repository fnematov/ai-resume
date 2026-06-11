<script setup lang="ts">
import { computed } from "vue"
import { scoreBg, scoreColor } from "@/lib/utils"

const props = defineProps<{ value: number | null | undefined; showLabel?: boolean }>()
const width = computed(() => `${props.value ?? 0}%`)
</script>

<template>
  <div class="flex items-center gap-2 min-w-[120px]">
    <div class="h-2 flex-1 rounded-full bg-muted overflow-hidden">
      <div class="h-full rounded-full transition-all" :class="scoreBg(value)" :style="{ width }" />
    </div>
    <span v-if="showLabel !== false" class="text-sm font-semibold tabular-nums w-10 text-right" :class="scoreColor(value)">
      {{ value == null ? "—" : `${value}%` }}
    </span>
  </div>
</template>
