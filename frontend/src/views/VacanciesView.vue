<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { ImagePlus, Plus, Sparkles, Upload, X } from "lucide-vue-next"
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import { apiError } from "@/api/client"
import { vacancyApi } from "@/api/endpoints"
import type { Vacancy, VacancyDraft, VacancyStatus } from "@/api/types"
import AiVacancyChat from "@/components/AiVacancyChat.vue"
import PendingBanner from "@/components/PendingBanner.vue"
import { useOrg } from "@/composables/useOrg"
import { useVacancyDraftStore } from "@/stores/vacancyDraft"
import {
  Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner, Textarea,
} from "@/components/ui"

const qc = useQueryClient()
const router = useRouter()
const draftStore = useVacancyDraftStore()
const { isActive } = useOrg()
const { data: vacancies, isLoading } = useQuery({
  queryKey: ["vacancies"],
  queryFn: vacancyApi.list,
  enabled: isActive,
})

const showForm = ref(false)
const showFormAi = ref(false)
const error = ref("")
const emptyForm = () => ({
  title: "",
  description: "",
  requirements: "",
  employment_type: "",
  location: "",
  ai_instructions: "",
  status: "open" as VacancyStatus,
})
const form = ref(emptyForm())

// Optional banner image (uploaded after the vacancy is created).
const imageFile = ref<File | null>(null)
const imagePreview = ref("")
const imgInput = ref<HTMLInputElement | null>(null)
function onImagePick(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0] ?? null
  imageFile.value = f
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imagePreview.value = f ? URL.createObjectURL(f) : ""
}
function clearImage() {
  imageFile.value = null
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imagePreview.value = ""
  if (imgInput.value) imgInput.value.value = ""
}

const create = useMutation({
  mutationFn: async () => {
    const v = await vacancyApi.create(form.value)
    if (imageFile.value) await vacancyApi.setImage(v.id, imageFile.value)
    return v
  },
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["vacancies"] })
    showForm.value = false
    form.value = emptyForm()
    clearImage()
  },
  onError: (e) => (error.value = apiError(e)),
})

const statusVariant: Record<VacancyStatus, "success" | "muted" | "secondary"> = {
  open: "success",
  draft: "secondary",
  closed: "muted",
}
function badge(v: Vacancy) {
  return statusVariant[v.status]
}

// Current form values handed to the in-form AI helper so it doesn't re-ask.
const currentDraft = computed<VacancyDraft>(() => ({
  title: form.value.title,
  description: form.value.description,
  requirements: form.value.requirements,
  employment_type: form.value.employment_type,
  location: form.value.location,
  ai_instructions: form.value.ai_instructions,
}))

// Dedicated AI builder page handoff: prefill a fresh create form.
// Default to "open" — the recruiter still reviews and clicks Create before it saves.
function applyDraft(d: VacancyDraft) {
  form.value = { ...d, status: "open" }
  showForm.value = true
  clearImage()
}

// In-form AI helper: merge the AI draft into the open form (keep empty values intact).
function applyFormDraft(d: VacancyDraft) {
  form.value.title = d.title || form.value.title
  form.value.description = d.description || form.value.description
  form.value.requirements = d.requirements || form.value.requirements
  form.value.employment_type = d.employment_type || form.value.employment_type
  form.value.location = d.location || form.value.location
  form.value.ai_instructions = d.ai_instructions || form.value.ai_instructions
  showFormAi.value = false
}

// A draft produced on the dedicated AI page lands here.
onMounted(() => {
  const d = draftStore.take()
  if (d) applyDraft(d)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-muted-foreground">{{ $t("vacancy.subtitle") }}</p>
      </div>
      <div class="flex gap-2">
        <Button :disabled="!isActive" @click="router.push({ name: 'vacancy-ai' })">
          <Sparkles class="h-4 w-4" /> {{ $t("aiVacancy.button") }}
        </Button>
        <Button variant="outline" :disabled="!isActive" @click="showForm = !showForm">
          <Plus class="h-4 w-4" /> {{ $t("vacancy.new") }}
        </Button>
      </div>
    </div>

    <PendingBanner />

    <!-- In-form AI helper: fills/refines the open form, seeded with current values -->
    <div
      v-if="showFormAi"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      @click.self="showFormAi = false"
    >
      <div class="h-[80vh] w-full max-w-xl overflow-hidden rounded-lg border bg-card shadow-xl">
        <AiVacancyChat
          storage-key="ar_ai_vacancy_form"
          :current="currentDraft"
          show-close
          @close="showFormAi = false"
          @apply="applyFormDraft"
        />
      </div>
    </div>

    <Card v-if="showForm">
      <CardHeader class="flex flex-row items-center justify-between space-y-0">
        <CardTitle>{{ $t("vacancy.new") }}</CardTitle>
        <Button type="button" variant="outline" size="sm" @click="showFormAi = true">
          <Sparkles class="h-4 w-4" /> {{ $t("aiVacancy.fillButton") }}
        </Button>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="create.mutate()">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2 sm:col-span-2">
              <Label>{{ $t("vacancy.titleField") }}</Label>
              <Input v-model="form.title" placeholder="PHP / Laravel Developer" />
            </div>
            <div class="space-y-2">
              <Label>{{ $t("vacancy.employmentType") }}</Label>
              <Input v-model="form.employment_type" placeholder="Full-time" />
            </div>
            <div class="space-y-2">
              <Label>{{ $t("vacancy.location") }}</Label>
              <Input v-model="form.location" placeholder="Remote" />
            </div>
          </div>
          <div class="space-y-2">
            <Label>{{ $t("vacancy.description") }}</Label>
            <Textarea v-model="form.description" :rows="3" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("vacancy.requirements") }}</Label>
            <Textarea v-model="form.requirements" :rows="3" placeholder="PHP, Laravel, MySQL, 3+ years…" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("vacancy.aiInstructions") }}</Label>
            <Textarea v-model="form.ai_instructions" :rows="3" />
            <p class="text-xs text-muted-foreground">{{ $t("vacancy.aiInstructionsHint") }}</p>
          </div>
          <div class="flex flex-wrap items-center gap-4 rounded-md border p-4">
            <img v-if="imagePreview" :src="imagePreview" alt="" class="h-24 w-40 rounded-md border object-cover" />
            <div v-else class="grid h-24 w-40 place-items-center rounded-md border border-dashed text-muted-foreground">
              <ImagePlus class="h-6 w-6" />
            </div>
            <div class="flex-1 min-w-[200px] space-y-1">
              <p class="text-sm font-medium">{{ $t("vacancy.image") }}</p>
              <p class="text-xs text-muted-foreground">{{ $t("vacancy.imageHint") }}</p>
            </div>
            <input ref="imgInput" type="file" class="hidden" accept="image/png,image/jpeg,image/webp,image/gif" @change="onImagePick" />
            <div class="flex gap-2">
              <Button type="button" variant="secondary" size="sm" @click="imgInput?.click()">
                <Upload class="h-4 w-4" /> {{ imagePreview ? $t("common.edit") : $t("common.add") }}
              </Button>
              <Button v-if="imagePreview" type="button" variant="ghost" size="sm" @click="clearImage">
                <X class="h-4 w-4" /> {{ $t("vacancy.removeImage") }}
              </Button>
            </div>
          </div>
          <div class="space-y-2">
            <Label>{{ $t("common.status") }}</Label>
            <select v-model="form.status" class="h-9 w-40 rounded-md border border-input bg-transparent px-3 text-sm">
              <option value="open">{{ $t("vacancyStatus.open") }}</option>
              <option value="draft">{{ $t("vacancyStatus.draft") }}</option>
              <option value="closed">{{ $t("vacancyStatus.closed") }}</option>
            </select>
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <div class="flex gap-2">
            <Button type="submit" :disabled="create.isPending.value"><Spinner v-if="create.isPending.value" /> {{ $t("common.create") }}</Button>
            <Button type="button" variant="ghost" @click="showForm = false">{{ $t("common.cancel") }}</Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>
    <Card v-else-if="!vacancies?.length">
      <CardContent class="py-16 text-center text-muted-foreground">
        No vacancies yet. Create your first role to start collecting resumes.
      </CardContent>
    </Card>
    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink v-for="v in vacancies" :key="v.id" :to="{ name: 'vacancy', params: { id: v.id } }">
        <Card class="h-full transition-colors hover:border-primary/40">
          <CardContent class="p-5 space-y-2">
            <div class="flex items-start justify-between gap-2">
              <h3 class="font-semibold leading-tight">{{ v.title }}</h3>
              <Badge :variant="badge(v)">{{ v.status }}</Badge>
            </div>
            <p class="text-sm text-muted-foreground line-clamp-2">{{ v.description || "No description" }}</p>
            <p class="text-xs text-muted-foreground pt-2">{{ v.application_count }} applicants</p>
          </CardContent>
        </Card>
      </RouterLink>
    </div>
  </div>
</template>
