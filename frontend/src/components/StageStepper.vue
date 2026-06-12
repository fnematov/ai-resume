<script setup lang="ts">
import { Check } from "lucide-vue-next"
import { computed } from "vue"

import type { ApplicationStage } from "@/api/types"
import { STAGE_ORDER } from "@/api/types"

const props = defineProps<{ stage: ApplicationStage }>()

const isTerminalNegative = computed(
  () => props.stage === "rejected" || props.stage === "withdrawn",
)
const currentIndex = computed(() => STAGE_ORDER.indexOf(props.stage))
</script>

<template>
  <div class="flex flex-wrap items-center gap-1">
    <template v-for="(s, i) in STAGE_ORDER" :key="s">
      <div
        class="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium"
        :class="[
          i < currentIndex && !isTerminalNegative ? 'bg-primary/10 text-primary' : '',
          i === currentIndex && !isTerminalNegative ? 'bg-primary text-primary-foreground' : '',
          (i > currentIndex || isTerminalNegative) ? 'bg-muted text-muted-foreground' : '',
        ]"
      >
        <Check v-if="i < currentIndex && !isTerminalNegative" class="h-3 w-3" />
        {{ $t(`stages.${s}`) }}
      </div>
      <span v-if="i < STAGE_ORDER.length - 1" class="text-muted-foreground/40">›</span>
    </template>
    <div v-if="isTerminalNegative" class="ml-2 rounded-full bg-destructive/10 px-3 py-1 text-xs font-medium text-destructive">
      {{ $t(`stages.${stage}`) }}
    </div>
  </div>
</template>
