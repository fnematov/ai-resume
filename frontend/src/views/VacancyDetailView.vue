<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Copy, LayoutGrid, Upload } from "lucide-vue-next"
import { computed, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { apiError } from "@/api/client"
import { applicationApi, vacancyApi } from "@/api/endpoints"
import type { ApplicationStatus } from "@/api/types"
import { Badge, Button, Card, CardContent, ScoreBar, Spinner } from "@/components/ui"
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
      <div class="mt-2 flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">{{ vacancy?.title }}</h1>
          <p class="text-muted-foreground">{{ vacancy?.application_count }} applicants · {{ vacancy?.status }}</p>
        </div>
        <Button variant="outline" @click="router.push({ name: 'pipeline', params: { id } })">
          <LayoutGrid class="h-4 w-4" /> Pipeline board
        </Button>
      </div>
    </div>

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
