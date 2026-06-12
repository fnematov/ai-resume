<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Briefcase, Check, Download, FileText, RefreshCw, Send, UserX, X } from "lucide-vue-next"
import { computed, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import { applicationApi, orgApi, templateApi } from "@/api/endpoints"
import ActionModal from "@/components/ActionModal.vue"
import ConversationThread from "@/components/ConversationThread.vue"
import StageStepper from "@/components/StageStepper.vue"
import Timeline from "@/components/Timeline.vue"
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Spinner } from "@/components/ui"
import { formatDate, scoreColor } from "@/lib/utils"

const route = useRoute()
const router = useRouter()
const qc = useQueryClient()
const id = computed(() => Number(route.params.id))

const { data: app, isLoading } = useQuery({
  queryKey: ["application", id],
  queryFn: () => applicationApi.get(id.value),
  refetchInterval: (q) => {
    const s = (q.state.data as any)?.status
    return s === "pending" || s === "processing" ? 2500 : false
  },
})

const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: templateApi.list })
const { data: org } = useQuery({ queryKey: ["org"], queryFn: orgApi.me })
const { data: submissions } = useQuery({
  queryKey: ["app-submissions", id],
  queryFn: () => applicationApi.submissions(id.value),
  refetchInterval: (q) => {
    const arr = q.state.data as { status: string }[] | undefined
    return arr?.some((s) => s.status === "pending" || s.status === "processing") ? 3000 : false
  },
})
const { data: interviews } = useQuery({
  queryKey: ["app-interviews", id],
  queryFn: () => applicationApi.interviews(id.value),
})

const rescore = useMutation({
  mutationFn: () => applicationApi.rescore(id.value),
  onSuccess: () => qc.invalidateQueries({ queryKey: ["application", id] }),
})

const r = computed(() => app.value?.ai_result ?? null)
const resumeUrl = computed(() => applicationApi.resumeUrl(id.value))

const tab = ref<"chat" | "timeline">("chat")
const actionOpen = ref(false)
const action = ref<"test_task" | "interview" | "offer" | "reject" | null>(null)
function openAction(a: typeof action.value) {
  action.value = a
  actionOpen.value = true
}

const ACTIONS = [
  { key: "test_task", label: "application.actionTestTask", icon: FileText },
  { key: "interview", label: "application.actionInterview", icon: Briefcase },
  { key: "offer", label: "application.actionOffer", icon: Check },
  { key: "reject", label: "application.actionReject", icon: UserX },
] as const
</script>

<template>
  <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>
  <div v-else-if="app" class="space-y-6">
    <button class="text-sm text-muted-foreground hover:text-foreground" @click="router.back()">← Back</button>

    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">
          {{ app.candidate?.full_name || app.candidate?.telegram_username || "Candidate" }}
        </h1>
        <p class="text-muted-foreground">
          {{ app.original_filename }} · {{ app.source }} · {{ formatDate(app.created_at) }}
        </p>
        <p v-if="app.candidate?.telegram_username" class="text-sm">
          <a :href="`https://t.me/${app.candidate.telegram_username}`" target="_blank" class="text-primary hover:underline">
            @{{ app.candidate.telegram_username }}
          </a>
        </p>
      </div>
      <div class="flex gap-2">
        <a :href="resumeUrl" target="_blank">
          <Button variant="outline"><Download class="h-4 w-4" /> {{ $t("application.resume") }}</Button>
        </a>
        <Button variant="secondary" :disabled="rescore.isPending.value" @click="rescore.mutate()">
          <Spinner v-if="rescore.isPending.value" /><RefreshCw v-else class="h-4 w-4" /> {{ $t("application.rescore") }}
        </Button>
      </div>
    </div>

    <!-- Pipeline stage + recruiter actions -->
    <Card>
      <CardContent class="space-y-4 p-4">
        <StageStepper :stage="app.stage" />
        <div class="flex flex-wrap gap-2">
          <Button
            v-for="a in ACTIONS"
            :key="a.key"
            size="sm"
            :variant="a.key === 'reject' ? 'outline' : 'default'"
            @click="openAction(a.key)"
          >
            <component :is="a.icon" class="h-4 w-4" /> {{ $t(a.label) }}
          </Button>
        </div>
        <p v-if="app.decision_reason && app.stage === 'rejected'" class="text-xs text-muted-foreground">
          {{ $t("application.decisionNote", { note: app.decision_reason }) }}
        </p>
      </CardContent>
    </Card>

    <!-- Cover letter -->
    <Card v-if="app.cover_letter_text || app.cover_letter_filename">
      <CardHeader class="pb-2">
        <CardTitle class="flex items-center gap-2 text-base">
          {{ $t("application.coverLetter") }}
          <a v-if="app.cover_letter_filename" :href="applicationApi.coverLetterUrl(id)" target="_blank">
            <Button variant="outline" size="sm"><Download class="h-4 w-4" /> {{ app.cover_letter_filename }}</Button>
          </a>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p v-if="app.cover_letter_text" class="whitespace-pre-wrap text-sm leading-relaxed">{{ app.cover_letter_text }}</p>
        <p v-else class="text-sm text-muted-foreground">{{ $t("application.coverLetterFile") }}</p>
      </CardContent>
    </Card>

    <!-- Interview -->
    <Card v-if="interviews?.length">
      <CardHeader class="pb-2"><CardTitle class="text-base">{{ $t("application.interview") }}</CardTitle></CardHeader>
      <CardContent class="space-y-2">
        <div v-for="iv in interviews" :key="iv.id" class="rounded-md border p-3 text-sm">
          <div class="flex items-center gap-2">
            <span class="font-medium">{{ formatDate(iv.scheduled_at) }}</span>
            <Badge :variant="iv.status === 'scheduled' ? 'success' : 'muted'">{{ iv.status }}</Badge>
          </div>
          <a v-if="iv.join_url" :href="iv.join_url" target="_blank" class="text-primary hover:underline">
            🎥 Join (Google Meet)
          </a>
          <p v-else-if="iv.location" class="text-muted-foreground">📍 {{ iv.location }}</p>
        </div>
      </CardContent>
    </Card>

    <!-- Test-task submissions -->
    <Card v-if="submissions?.length">
      <CardHeader class="pb-2"><CardTitle class="text-base">{{ $t("application.testSubmissions") }}</CardTitle></CardHeader>
      <CardContent class="space-y-3">
        <div v-for="s in submissions" :key="s.id" class="flex items-start justify-between gap-4 rounded-md border p-3">
          <div class="min-w-0">
            <p class="text-sm font-medium">{{ s.original_filename || "Submission" }}</p>
            <p class="text-xs text-muted-foreground">{{ formatDate(s.created_at) }} · {{ s.status }}</p>
            <p v-if="s.ai_feedback?.summary" class="mt-1 text-sm">{{ s.ai_feedback.summary }}</p>
            <p v-else-if="s.status === 'failed'" class="mt-1 text-sm text-destructive">{{ s.error }}</p>
          </div>
          <div v-if="s.ai_score != null" class="shrink-0 text-2xl font-bold" :class="scoreColor(s.ai_score)">{{ s.ai_score }}%</div>
          <Spinner v-else-if="s.status === 'pending' || s.status === 'processing'" class="mt-1" />
        </div>
      </CardContent>
    </Card>

    <Card v-if="app.status === 'failed'" class="border-destructive/40 bg-destructive/5">
      <CardContent class="p-4 text-sm text-destructive">
        Scoring failed: {{ app.error || "unknown error" }}
      </CardContent>
    </Card>
    <Card v-else-if="app.status !== 'scored'">
      <CardContent class="p-8 text-center text-muted-foreground flex flex-col items-center gap-3">
        <Spinner class="h-6 w-6" /> {{ $t("application.reviewing") }} ({{ $t(`statuses.${app.status}`) }})
      </CardContent>
    </Card>

    <template v-else-if="r">
      <div class="grid gap-6 lg:grid-cols-3">
        <Card class="lg:col-span-1">
          <CardContent class="p-6 flex flex-col items-center text-center gap-2">
            <div class="text-5xl font-bold tabular-nums" :class="scoreColor(r.match_percentage)">{{ r.match_percentage }}%</div>
            <p class="text-sm text-muted-foreground">{{ $t("application.matchScore") }}</p>
            <Badge :variant="r.recommended ? 'success' : 'muted'" class="mt-2">
              <Check v-if="r.recommended" class="h-3 w-3 mr-1" /><X v-else class="h-3 w-3 mr-1" />
              {{ r.recommended ? $t("application.recommended") : $t("application.notRecommended") }}
            </Badge>
            <p class="mt-1 text-sm font-medium">{{ r.verdict }}</p>
          </CardContent>
        </Card>

        <Card class="lg:col-span-2">
          <CardHeader><CardTitle>{{ $t("application.summary") }}</CardTitle></CardHeader>
          <CardContent><p class="text-sm leading-relaxed">{{ r.summary }}</p></CardContent>
        </Card>
      </div>

      <div class="grid gap-6 sm:grid-cols-2">
        <Card>
          <CardHeader><CardTitle class="text-base text-green-700">{{ $t("application.matchedSkills") }}</CardTitle></CardHeader>
          <CardContent class="flex flex-wrap gap-2">
            <Badge v-for="s in r.matched_skills" :key="s" variant="success">{{ s }}</Badge>
            <span v-if="!r.matched_skills.length" class="text-sm text-muted-foreground">None identified.</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle class="text-base text-red-700">{{ $t("application.missingSkills") }}</CardTitle></CardHeader>
          <CardContent class="flex flex-wrap gap-2">
            <Badge v-for="s in r.missing_skills" :key="s" variant="destructive">{{ s }}</Badge>
            <span v-if="!r.missing_skills.length" class="text-sm text-muted-foreground">None.</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle class="text-base">{{ $t("application.strengths") }}</CardTitle></CardHeader>
          <CardContent>
            <ul class="space-y-1 text-sm list-disc pl-5">
              <li v-for="s in r.strengths" :key="s">{{ s }}</li>
            </ul>
            <span v-if="!r.strengths.length" class="text-sm text-muted-foreground">—</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle class="text-base">{{ $t("application.concerns") }}</CardTitle></CardHeader>
          <CardContent>
            <ul class="space-y-1 text-sm list-disc pl-5">
              <li v-for="s in r.concerns" :key="s">{{ s }}</li>
            </ul>
            <span v-if="!r.concerns.length" class="text-sm text-muted-foreground">—</span>
          </CardContent>
        </Card>
      </div>
      <p class="text-xs text-muted-foreground">{{ $t("application.scoredBy", { provider: app.ai_provider }) }} · {{ formatDate(app.scored_at) }}</p>
    </template>

    <!-- Communication: conversation + activity timeline -->
    <Card>
      <CardHeader class="pb-0">
        <div class="flex gap-1">
          <button
            class="rounded-md px-3 py-1.5 text-sm font-medium"
            :class="tab === 'chat' ? 'bg-accent' : 'text-muted-foreground hover:bg-accent/50'"
            @click="tab = 'chat'"
          >
            {{ $t("application.conversation") }}
          </button>
          <button
            class="rounded-md px-3 py-1.5 text-sm font-medium"
            :class="tab === 'timeline' ? 'bg-accent' : 'text-muted-foreground hover:bg-accent/50'"
            @click="tab = 'timeline'"
          >
            {{ $t("application.activity") }}
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <ConversationThread v-if="tab === 'chat'" :application-id="id" :chat-open="app.chat_open" />
        <Timeline v-else :application-id="id" />
      </CardContent>
    </Card>

    <ActionModal
      :open="actionOpen"
      :action="action"
      :application-id="id"
      :templates="templates || []"
      :scheduling-configured="!!org?.calendly_configured"
      @close="actionOpen = false"
      @sent="qc.invalidateQueries({ queryKey: ['application', id] })"
    />
  </div>
</template>
