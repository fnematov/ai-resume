<script setup lang="ts">
import { Plus } from "lucide-vue-next"
import { nextTick, ref } from "vue"

import { cn } from "@/lib/utils"

const props = defineProps<{
  modelValue: string
  rows?: number
  variables?: { key: string; label: string }[]
}>()
const emit = defineEmits<{ (e: "update:modelValue", v: string): void }>()

// Variable → friendly meaning (so authors know what each one inserts).
const DEFAULT_VARS = [
  { key: "candidate_name", label: "Candidate name" },
  { key: "job_title", label: "Job title" },
  { key: "company", label: "Company name" },
  { key: "scheduling_link", label: "Calendly link" },
  { key: "test_task", label: "Test task text" },
  { key: "deadline", label: "Deadline" },
  { key: "salary", label: "Salary" },
  { key: "start_date", label: "Start date" },
]
const vars = props.variables ?? DEFAULT_VARS
const ph = (s: string) => `{{${s}}}`
const el = ref<HTMLTextAreaElement | null>(null)

function insert(key: string) {
  const token = ph(key)
  const node = el.value
  const cur = props.modelValue ?? ""
  if (!node) {
    emit("update:modelValue", cur + token)
    return
  }
  const start = node.selectionStart ?? cur.length
  const end = node.selectionEnd ?? start
  emit("update:modelValue", cur.slice(0, start) + token + cur.slice(end))
  nextTick(() => {
    node.focus()
    const pos = start + token.length
    node.setSelectionRange(pos, pos)
  })
}
</script>

<template>
  <div class="space-y-2">
    <div class="flex flex-wrap gap-1.5">
      <button
        v-for="v in vars"
        :key="v.key"
        type="button"
        class="inline-flex items-center gap-1 rounded-md border bg-muted/50 px-2 py-1 text-xs transition-colors hover:bg-accent"
        :title="`Insert ${ph(v.key)} — ${v.label}`"
        @click="insert(v.key)"
      >
        <Plus class="h-3 w-3 text-muted-foreground" />
        <span class="font-medium">{{ v.label }}</span>
        <code class="text-[10px] text-muted-foreground">{{ ph(v.key) }}</code>
      </button>
    </div>
    <textarea
      ref="el"
      :value="modelValue"
      :rows="rows || 8"
      :class="cn('flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring')"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <p class="text-xs text-muted-foreground">Click a variable to insert it where your cursor is.</p>
  </div>
</template>
