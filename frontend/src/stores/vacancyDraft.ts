import { defineStore } from "pinia"
import { ref } from "vue"

import type { VacancyDraft } from "@/api/types"

// Hands an AI-generated draft from the dedicated builder page to the Vacancies
// create form (which lives on another route).
export const useVacancyDraftStore = defineStore("vacancyDraft", () => {
  const pending = ref<VacancyDraft | null>(null)

  function set(draft: VacancyDraft) {
    pending.value = draft
  }
  function take(): VacancyDraft | null {
    const d = pending.value
    pending.value = null
    return d
  }

  return { pending, set, take }
})
