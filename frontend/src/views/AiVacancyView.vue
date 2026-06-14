<script setup lang="ts">
import { ArrowLeft } from "lucide-vue-next"
import { useRouter } from "vue-router"

import type { VacancyDraft } from "@/api/types"
import AiVacancyChat from "@/components/AiVacancyChat.vue"
import { Card } from "@/components/ui"
import { useVacancyDraftStore } from "@/stores/vacancyDraft"

const router = useRouter()
const draftStore = useVacancyDraftStore()

function onApply(draft: VacancyDraft) {
  // Hand the draft to the Vacancies create form for final review + save.
  draftStore.set(draft)
  router.push({ name: "vacancies" })
}
</script>

<template>
  <div class="space-y-4">
    <button
      class="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      @click="router.push({ name: 'vacancies' })"
    >
      <ArrowLeft class="h-4 w-4" /> {{ $t("nav.vacancies") }}
    </button>
    <Card class="h-[calc(100vh-12rem)] overflow-hidden">
      <AiVacancyChat storage-key="ar_ai_vacancy_new" @apply="onApply" />
    </Card>
  </div>
</template>
