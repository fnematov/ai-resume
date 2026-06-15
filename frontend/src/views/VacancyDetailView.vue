<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Copy, ImagePlus, LayoutGrid, Pencil, Upload, X } from "lucide-vue-next"
import { computed, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

import { apiError } from "@/api/client"
import { applicationApi, vacancyApi } from "@/api/endpoints"
import type { ApplicationStatus, VacancyStatus } from "@/api/types"
import { Badge, Button, Card, CardContent, Input, Label, ScoreBar, Spinner, Textarea } from "@/components/ui"
import { formatDate } from "@/lib/utils"

const route = useRoute()
const router = useRouter()
const qc = useQueryClient()
const id = computed(() => Number(route.params.id))

const sort = ref("score_desc")
const statusFilter = ref<"" | ApplicationStatus>("")
const minScore = ref(0)
const copied = ref(false)
const uploadError = ref("")
const fileInput = ref<HTMLInputElement | null>(null)

const { data: vacancy } = useQuery({ queryKey: ["vacancy", id], queryFn: () => vacancyApi.get(id.value) })

const appsQuery = useQuery({
  queryKey: ["applications", id, sort, statusFilter, minScore],
  queryFn: () =>
    applicationApi.list({
      vacancy_id: id.value,
      sort: sort.value,
      status: statusFilter.value || undefined,
      min_score: minScore.value || undefined,
    }),
})

const upload = useMutation({
  mutationFn: (file: File) => applicationApi.upload(id.value, file),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["applications", id] })
    qc.invalidateQueries({ queryKey: ["vacancy", id] })
  },
  onError: (e) => (uploadError.value = apiError(e)),
})

function copyLink() {
  if (!vacancy.value?.deep_link_url) return
  navigator.clipboard.writeText(vacancy.value.deep_link_url)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) {
    uploadError.value = ""
    upload.mutate(f)
  }
}

// --- Vacancy banner image ---
const imgInput = ref<HTMLInputElement | null>(null)
const imageUrl = ref("")
watch(
  vacancy,
  async (v) => {
    if (imageUrl.value) {
      URL.revokeObjectURL(imageUrl.value)
      imageUrl.value = ""
    }
    if (v?.has_image) {
      try {
        imageUrl.value = URL.createObjectURL(await vacancyApi.image(v.id))
      } catch {
        imageUrl.value = ""
      }
    }
  },
  { immediate: true },
)
const setImage = useMutation({
  mutationFn: (file: File) => vacancyApi.setImage(id.value, file),
  onSuccess: () => qc.invalidateQueries({ queryKey: ["vacancy", id] }),
  onError: (e) => (uploadError.value = apiError(e)),
})
const removeImage = useMutation({
  mutationFn: () => vacancyApi.removeImage(id.value),
  onSuccess: () => qc.invalidateQueries({ queryKey: ["vacancy", id] }),
})
function onImage(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) {
    uploadError.value = ""
    setImage.mutate(f)
  }
}

// --- Vacancy info editing ---
const editing = ref(false)
const editError = ref("")
const editForm = ref({
  title: "",
  employment_type: "",
  location: "",
  description: "",
  requirements: "",
  ai_instructions: "",
  status: "open" as VacancyStatus,
})
function startEdit() {
  const v = vacancy.value
  if (!v) return
  editForm.value = {
    title: v.title,
    employment_type: v.employment_type ?? "",
    location: v.location ?? "",
    description: v.description ?? "",
    requirements: v.requirements ?? "",
    ai_instructions: v.ai_instructions ?? "",
    status: v.status,
  }
  editError.value = ""
  editing.value = true
}
const saveEdit = useMutation({
  mutationFn: () =>
    vacancyApi.update(id.value, {
      title: editForm.value.title,
      employment_type: editForm.value.employment_type || null,
      location: editForm.value.location || null,
      description: editForm.value.description,
      requirements: editForm.value.requirements,
      ai_instructions: editForm.value.ai_instructions || null,
      status: editForm.value.status,
    }),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["vacancy", id] })
    qc.invalidateQueries({ queryKey: ["vacancies"] })
    editing.value = false
  },
  onError: (e) => (editError.value = apiError(e)),
})

// Quick status change from the header (draft ↔ open ↔ closed).
const changeStatus = useMutation({
  mutationFn: (status: VacancyStatus) => vacancyApi.update(id.value, { status }),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["vacancy", id] })
    qc.invalidateQueries({ queryKey: ["vacancies"] })
  },
})
function onStatusChange(e: Event) {
  changeStatus.mutate((e.target as HTMLSelectElement).value as VacancyStatus)
}

const vacancyStatusVariant: Record<VacancyStatus, "success" | "secondary" | "muted"> = {
  open: "success",
  draft: "secondary",
  closed: "muted",
}

const statusVariant: Record<ApplicationStatus, "success" | "warning" | "muted" | "destructive"> = {
  scored: "success",
  processing: "warning",
  pending: "warning",
  failed: "destructive",
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <button class="text-sm text-muted-foreground hover:text-foreground" @click="router.push({ name: 'vacancies' })">
        ← Vacancies
      </button>
      <div class="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">{{ vacancy?.title }}</h1>
          <p class="text-muted-foreground">{{ vacancy?.application_count }} applicants</p>
        </div>
        <div class="flex items-center gap-2">
          <label class="flex items-center gap-2 text-sm text-muted-foreground">
            {{ $t("common.status") }}
            <select
              v-if="vacancy"
              :value="vacancy.status"
              :disabled="changeStatus.isPending.value"
              class="h-9 rounded-md border border-input bg-transparent px-3 text-sm text-foreground"
              @change="onStatusChange"
            >
              <option value="open">{{ $t("vacancyStatus.open") }}</option>
              <option value="draft">{{ $t("vacancyStatus.draft") }}</option>
              <option value="closed">{{ $t("vacancyStatus.closed") }}</option>
            </select>
          </label>
          <Button variant="outline" @click="router.push({ name: 'pipeline', params: { id } })">
            <LayoutGrid class="h-4 w-4" /> Pipeline board
          </Button>
        </div>
      </div>
    </div>

    <!-- Vacancy details + inline edit -->
    <Card>
      <CardContent class="p-5">
        <!-- Read-only view -->
        <div v-if="!editing" class="space-y-4">
          <div class="flex items-start justify-between gap-3">
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
              <span v-if="vacancy?.employment_type" class="flex items-center gap-1">💼 {{ vacancy.employment_type }}</span>
              <span v-if="vacancy?.location" class="flex items-center gap-1">📍 {{ vacancy.location }}</span>
              <Badge v-if="vacancy" :variant="vacancyStatusVariant[vacancy.status]">{{ vacancy.status }}</Badge>
            </div>
            <Button variant="outline" size="sm" @click="startEdit">
              <Pencil class="h-4 w-4" /> {{ $t("common.edit") }}
            </Button>
          </div>
          <div v-if="vacancy?.description" class="space-y-1">
            <p class="text-xs font-medium text-muted-foreground">{{ $t("vacancy.description") }}</p>
            <p class="whitespace-pre-wrap text-sm">{{ vacancy.description }}</p>
          </div>
          <div v-if="vacancy?.requirements" class="space-y-1">
            <p class="text-xs font-medium text-muted-foreground">{{ $t("vacancy.requirements") }}</p>
            <p class="whitespace-pre-wrap text-sm">{{ vacancy.requirements }}</p>
          </div>
          <div v-if="vacancy?.ai_instructions" class="space-y-1">
            <p class="text-xs font-medium text-muted-foreground">{{ $t("vacancy.aiInstructions") }}</p>
            <p class="whitespace-pre-wrap text-sm">{{ vacancy.ai_instructions }}</p>
          </div>
          <p v-if="vacancy && !vacancy.description && !vacancy.requirements" class="text-sm text-muted-foreground">
            {{ $t("vacancy.noDescription") }}
          </p>
        </div>

        <!-- Edit form -->
        <form v-else class="space-y-4" @submit.prevent="saveEdit.mutate()">
          <div class="space-y-2">
            <Label>{{ $t("vacancy.titleField") }}</Label>
            <Input v-model="editForm.title" />
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2">
              <Label>{{ $t("vacancy.employmentType") }}</Label>
              <Input v-model="editForm.employment_type" placeholder="Full-time" />
            </div>
            <div class="space-y-2">
              <Label>{{ $t("vacancy.location") }}</Label>
              <Input v-model="editForm.location" placeholder="Remote" />
            </div>
          </div>
          <div class="space-y-2">
            <Label>{{ $t("vacancy.description") }}</Label>
            <Textarea v-model="editForm.description" :rows="3" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("vacancy.requirements") }}</Label>
            <Textarea v-model="editForm.requirements" :rows="3" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("vacancy.aiInstructions") }}</Label>
            <Textarea v-model="editForm.ai_instructions" :rows="3" />
            <p class="text-xs text-muted-foreground">{{ $t("vacancy.aiInstructionsHint") }}</p>
          </div>
          <div class="space-y-2">
            <Label>{{ $t("common.status") }}</Label>
            <select v-model="editForm.status" class="h-9 w-40 rounded-md border border-input bg-transparent px-3 text-sm">
              <option value="open">{{ $t("vacancyStatus.open") }}</option>
              <option value="draft">{{ $t("vacancyStatus.draft") }}</option>
              <option value="closed">{{ $t("vacancyStatus.closed") }}</option>
            </select>
          </div>
          <p v-if="editError" class="text-sm text-destructive">{{ editError }}</p>
          <div class="flex gap-2">
            <Button type="submit" :disabled="saveEdit.isPending.value || editForm.title.length < 2">
              <Spinner v-if="saveEdit.isPending.value" /> {{ $t("common.save") }}
            </Button>
            <Button type="button" variant="ghost" @click="editing = false">{{ $t("common.cancel") }}</Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <!-- Telegram link -->
    <Card>
      <CardContent class="p-4 flex flex-wrap items-center gap-3">
        <div class="flex-1 min-w-[260px]">
          <p class="text-xs font-medium text-muted-foreground mb-1">Telegram application link</p>
          <code v-if="vacancy?.deep_link_url" class="text-sm break-all">{{ vacancy.deep_link_url }}</code>
          <p v-else class="text-sm text-amber-600">
            Connect a Telegram bot in <RouterLink to="/settings" class="underline">Settings</RouterLink> to generate the link.
          </p>
        </div>
        <Button v-if="vacancy?.deep_link_url" variant="outline" size="sm" @click="copyLink">
          <Copy class="h-4 w-4" /> {{ copied ? "Copied!" : "Copy" }}
        </Button>
        <div>
          <input ref="fileInput" type="file" class="hidden" accept=".pdf,.png,.jpg,.jpeg,.webp,.doc,.docx" @change="onFile" />
          <Button variant="secondary" size="sm" :disabled="upload.isPending.value" @click="fileInput?.click()">
            <Spinner v-if="upload.isPending.value" /><Upload v-else class="h-4 w-4" /> Manual upload
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Vacancy banner image -->
    <Card>
      <CardContent class="p-4 flex flex-wrap items-center gap-4">
        <img v-if="imageUrl" :src="imageUrl" alt="" class="h-24 w-40 rounded-md border object-cover" />
        <div v-else class="grid h-24 w-40 place-items-center rounded-md border border-dashed text-muted-foreground">
          <ImagePlus class="h-6 w-6" />
        </div>
        <div class="flex-1 min-w-[200px] space-y-1">
          <p class="text-sm font-medium">{{ $t("vacancy.image") }}</p>
          <p class="text-xs text-muted-foreground">{{ $t("vacancy.imageHint") }}</p>
        </div>
        <input ref="imgInput" type="file" class="hidden" accept="image/png,image/jpeg,image/webp,image/gif" @change="onImage" />
        <div class="flex gap-2">
          <Button variant="secondary" size="sm" :disabled="setImage.isPending.value" @click="imgInput?.click()">
            <Spinner v-if="setImage.isPending.value" /><Upload v-else class="h-4 w-4" />
            {{ vacancy?.has_image ? $t("common.save") : $t("common.create") }}
          </Button>
          <Button v-if="vacancy?.has_image" variant="ghost" size="sm" :disabled="removeImage.isPending.value" @click="removeImage.mutate()">
            <X class="h-4 w-4" /> {{ $t("vacancy.removeImage") }}
          </Button>
        </div>
      </CardContent>
    </Card>
    <p v-if="uploadError" class="text-sm text-destructive">{{ uploadError }}</p>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3">
      <select v-model="sort" class="h-9 rounded-md border border-input bg-transparent px-3 text-sm">
        <option value="score_desc">Best match first</option>
        <option value="score_asc">Worst match first</option>
        <option value="newest">Newest</option>
        <option value="oldest">Oldest</option>
      </select>
      <select v-model="statusFilter" class="h-9 rounded-md border border-input bg-transparent px-3 text-sm">
        <option value="">All statuses</option>
        <option value="scored">Scored</option>
        <option value="pending">Pending</option>
        <option value="processing">Processing</option>
        <option value="failed">Failed</option>
      </select>
      <label class="flex items-center gap-2 text-sm text-muted-foreground">
        Min score
        <input v-model.number="minScore" type="range" min="0" max="100" step="5" class="w-32" />
        <span class="w-8 tabular-nums">{{ minScore }}%</span>
      </label>
    </div>

    <!-- Table -->
    <Card>
      <CardContent class="p-0">
        <div v-if="appsQuery.isLoading.value" class="grid place-items-center py-16"><Spinner class="h-6 w-6" /></div>
        <div v-else-if="!appsQuery.data.value?.length" class="py-16 text-center text-muted-foreground">
          No applications match these filters.
        </div>
        <table v-else class="w-full text-sm">
          <thead class="border-b text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-4 py-3 font-medium">Candidate</th>
              <th class="px-4 py-3 font-medium">Match</th>
              <th class="px-4 py-3 font-medium">Status</th>
              <th class="px-4 py-3 font-medium">Source</th>
              <th class="px-4 py-3 font-medium">Submitted</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="a in appsQuery.data.value"
              :key="a.id"
              class="border-b last:border-0 cursor-pointer hover:bg-accent/50"
              @click="router.push({ name: 'application', params: { id: a.id } })"
            >
              <td class="px-4 py-3">
                <p class="font-medium">{{ a.candidate?.full_name || a.candidate?.telegram_username || "Candidate" }}</p>
                <p class="text-xs text-muted-foreground">{{ a.original_filename }}</p>
              </td>
              <td class="px-4 py-3 w-[200px]"><ScoreBar :value="a.match_percentage" /></td>
              <td class="px-4 py-3"><Badge :variant="statusVariant[a.status]">{{ a.status }}</Badge></td>
              <td class="px-4 py-3 text-muted-foreground">{{ a.source }}</td>
              <td class="px-4 py-3 text-muted-foreground">{{ formatDate(a.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>
  </div>
</template>
