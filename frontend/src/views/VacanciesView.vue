<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Plus, Sparkles, X } from "lucide-vue-next"
import { ref } from "vue"

import { apiError } from "@/api/client"
import { vacancyApi } from "@/api/endpoints"
import type { Vacancy, VacancyDraft, VacancyStatus } from "@/api/types"
import AiVacancyChat from "@/components/AiVacancyChat.vue"
import PendingBanner from "@/components/PendingBanner.vue"
import { useOrg } from "@/composables/useOrg"
import {
  Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner, Textarea,
} from "@/components/ui"

const qc = useQueryClient()
const { isActive } = useOrg()
const { data: vacancies, isLoading } = useQuery({
  queryKey: ["vacancies"],
  queryFn: vacancyApi.list,
  enabled: isActive,
})

const showForm = ref(false)
const showAiChat = ref(false)
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

// AI builder finished: prefill the create form with the draft for review + save.
function applyDraft(d: VacancyDraft) {
  form.value = {
    title: d.title,
    description: d.description,
    requirements: d.requirements,
    employment_type: d.employment_type,
    location: d.location,
    ai_instructions: d.ai_instructions,
    status: "draft",
  }
  showAiChat.value = false
  showForm.value = true
  clearImage()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-muted-foreground">{{ $t("vacancy.subtitle") }}</p>
      </div>
      <div class="flex gap-2">
        <Button :disabled="!isActive" @click="showAiChat = true">
          <Sparkles class="h-4 w-4" /> {{ $t("aiVacancy.button") }}
        </Button>
        <Button variant="outline" :disabled="!isActive" @click="showForm = !showForm">
          <Plus class="h-4 w-4" /> {{ $t("vacancy.new") }}
        </Button>
      </div>
    </div>

    <AiVacancyChat v-if="showAiChat" @close="showAiChat = false" @apply="applyDraft" />

    <PendingBanner />

    <Card v-if="showForm">
      <CardHeader><CardTitle>New vacancy</CardTitle></CardHeader>
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
          <div class="space-y-2">
            <Label>{{ $t("vacancy.image") }}</Label>
            <div v-if="imagePreview" class="flex items-start gap-3">
              <img :src="imagePreview" alt="" class="h-24 w-40 rounded-md border object-cover" />
              <Button type="button" variant="ghost" size="sm" @click="clearImage">
                <X class="h-4 w-4" /> {{ $t("vacancy.removeImage") }}
              </Button>
            </div>
            <input
              v-else
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              class="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-transparent file:px-3 file:py-1.5 file:text-sm file:font-medium hover:file:bg-accent"
              @change="onImagePick"
            />
            <p class="text-xs text-muted-foreground">{{ $t("vacancy.imageHint") }}</p>
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
