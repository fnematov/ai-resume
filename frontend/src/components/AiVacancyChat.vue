<script setup lang="ts">
import { useMutation } from "@tanstack/vue-query"
import { RotateCcw, Send, Sparkles, X } from "lucide-vue-next"
import { nextTick, onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"

import { apiError } from "@/api/client"
import { vacancyApi } from "@/api/endpoints"
import type { AiChatMessage, VacancyDraft } from "@/api/types"
import { Button, Spinner } from "@/components/ui"

const props = defineProps<{
  storageKey: string
  current?: VacancyDraft | null
  showClose?: boolean
}>()
const emit = defineEmits<{ (e: "close"): void; (e: "apply", draft: VacancyDraft): void }>()

const { locale } = useI18n()

const messages = ref<AiChatMessage[]>([])
const quickReplies = ref<string[]>([])
const latestDraft = ref<VacancyDraft | null>(null)
const complete = ref(false)
const input = ref("")
const error = ref("")
const scroller = ref<HTMLElement | null>(null)

function persist() {
  localStorage.setItem(
    props.storageKey,
    JSON.stringify({
      messages: messages.value,
      draft: latestDraft.value,
      complete: complete.value,
      quickReplies: quickReplies.value,
    }),
  )
}
function load() {
  try {
    const raw = localStorage.getItem(props.storageKey)
    if (!raw) return
    const s = JSON.parse(raw)
    messages.value = s.messages ?? []
    latestDraft.value = s.draft ?? null
    complete.value = !!s.complete
    quickReplies.value = s.quickReplies ?? []
  } catch {
    /* ignore corrupt state */
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
  })
}

const turn = useMutation({
  mutationFn: () => vacancyApi.aiDraft(messages.value, locale.value, props.current ?? undefined),
  onSuccess: (res) => {
    messages.value.push({ role: "assistant", content: res.message })
    quickReplies.value = res.quick_replies
    complete.value = res.complete
    if (res.draft && (res.draft.title || res.draft.description || res.draft.requirements)) {
      latestDraft.value = res.draft
    }
    error.value = ""
    persist()
    scrollToBottom()
  },
  onError: (e) => (error.value = apiError(e)),
})

function send(text: string) {
  const v = text.trim()
  if (!v || turn.isPending.value) return
  messages.value.push({ role: "user", content: v })
  quickReplies.value = []
  input.value = ""
  persist()
  scrollToBottom()
  turn.mutate()
}

function clearChat() {
  messages.value = []
  quickReplies.value = []
  latestDraft.value = null
  complete.value = false
  error.value = ""
  localStorage.removeItem(props.storageKey)
}

function applyDraft() {
  if (latestDraft.value) emit("apply", latestDraft.value)
}

onMounted(() => {
  load()
  scrollToBottom()
})
</script>

<template>
  <div class="flex h-full flex-col overflow-hidden">
    <!-- Header -->
    <div class="flex shrink-0 items-center justify-between border-b px-4 py-3">
      <div class="flex items-center gap-2">
        <Sparkles class="h-5 w-5 text-primary" />
        <h2 class="font-semibold">{{ $t("aiVacancy.title") }}</h2>
      </div>
      <div class="flex items-center gap-1">
        <button
          v-if="messages.length"
          class="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
          @click="clearChat"
        >
          <RotateCcw class="h-3.5 w-3.5" /> {{ $t("aiVacancy.clear") }}
        </button>
        <button v-if="showClose" class="rounded-md p-1 text-muted-foreground hover:bg-accent" @click="emit('close')">
          <X class="h-5 w-5" />
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div ref="scroller" class="flex-1 space-y-3 overflow-y-auto p-4">
      <!-- Static intro (UI only, never sent to the AI) -->
      <div class="flex justify-start">
        <div class="max-w-[85%] whitespace-pre-wrap rounded-2xl bg-muted px-4 py-2 text-sm">
          {{ $t("aiVacancy.intro") }}
        </div>
      </div>
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="flex"
        :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm"
          :class="m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'"
        >
          {{ m.content }}
        </div>
      </div>
      <div v-if="turn.isPending.value" class="flex justify-start">
        <div class="flex items-center gap-2 rounded-2xl bg-muted px-4 py-2 text-sm text-muted-foreground">
          <Spinner class="h-4 w-4" /> {{ $t("aiVacancy.thinking") }}
        </div>
      </div>
      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    </div>

    <!-- Quick replies -->
    <div v-if="quickReplies.length && !turn.isPending.value" class="flex shrink-0 flex-wrap gap-2 px-4 pb-2">
      <button
        v-for="(q, i) in quickReplies"
        :key="i"
        class="rounded-full border px-3 py-1.5 text-sm hover:bg-accent"
        @click="send(q)"
      >
        {{ q }}
      </button>
    </div>

    <!-- Draft ready -->
    <div v-if="complete && latestDraft" class="shrink-0 border-t bg-primary/5 px-4 py-3">
      <p class="mb-2 text-sm font-medium">{{ $t("aiVacancy.draftReady") }}</p>
      <Button class="w-full" @click="applyDraft">
        <Sparkles class="h-4 w-4" /> {{ $t("aiVacancy.confirm") }}
      </Button>
    </div>

    <!-- Input -->
    <form class="flex shrink-0 items-end gap-2 border-t p-3" @submit.prevent="send(input)">
      <textarea
        v-model="input"
        :rows="1"
        :placeholder="$t('aiVacancy.placeholder')"
        class="max-h-28 flex-1 resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        @keydown.enter.exact.prevent="send(input)"
      />
      <Button type="submit" size="icon" :disabled="!input.trim() || turn.isPending.value">
        <Send class="h-4 w-4" />
      </Button>
    </form>
  </div>
</template>
