<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query"
import { Briefcase, CheckCircle2, FileText, Star } from "lucide-vue-next"
import { computed } from "vue"

import { analyticsApi, orgApi } from "@/api/endpoints"
import StatCard from "@/components/StatCard.vue"
import { Badge, Card, CardContent, CardHeader, CardTitle, ScoreBar, Spinner } from "@/components/ui"
import { formatDate } from "@/lib/utils"

const { data: org } = useQuery({ queryKey: ["org"], queryFn: orgApi.me })
const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: analyticsApi.dashboard })

const maxBucket = computed(() =>
  Math.max(1, ...Object.values(data.value?.score_distribution ?? {})),
)
const pending = computed(() => org.value && org.value.status !== "active")
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
      <p class="text-muted-foreground">{{ org?.name }}</p>
    </div>

    <Card v-if="pending" class="border-amber-300 bg-amber-50">
      <CardContent class="p-4 text-sm text-amber-900">
        ⏳ Your organization is <b>{{ org?.status }}</b>. A platform admin must approve it before
        Telegram intake and scoring are enabled.
      </CardContent>
    </Card>

    <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>

    <template v-else-if="data">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total applications" :value="data.total_applications" :icon="FileText" />
        <StatCard label="Scored" :value="data.scored_applications" :icon="CheckCircle2" :hint="`${data.pending_applications} pending`" />
        <StatCard label="Avg match" :value="data.avg_score != null ? `${data.avg_score}%` : '—'" :icon="Star" />
        <StatCard label="Open vacancies" :value="data.open_vacancies" :icon="Briefcase" :hint="`${data.recommended_count} recommended`" />
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Score distribution</CardTitle></CardHeader>
          <CardContent class="space-y-3">
            <div v-for="(count, bucket) in data.score_distribution" :key="bucket" class="flex items-center gap-3">
              <span class="w-14 text-xs text-muted-foreground tabular-nums">{{ bucket }}%</span>
              <div class="h-5 flex-1 rounded bg-muted overflow-hidden">
                <div class="h-full bg-primary/80 rounded" :style="{ width: `${(count / maxBucket) * 100}%` }" />
              </div>
              <span class="w-8 text-right text-sm tabular-nums">{{ count }}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>By vacancy</CardTitle></CardHeader>
          <CardContent class="space-y-3">
            <div v-if="!data.per_vacancy.length" class="text-sm text-muted-foreground">No vacancies yet.</div>
            <RouterLink
              v-for="v in data.per_vacancy"
              :key="v.vacancy_id"
              :to="{ name: 'vacancy', params: { id: v.vacancy_id } }"
              class="flex items-center justify-between rounded-md p-2 hover:bg-accent"
            >
              <div class="min-w-0">
                <p class="truncate text-sm font-medium">{{ v.title }}</p>
                <p class="text-xs text-muted-foreground">{{ v.application_count }} applicants</p>
              </div>
              <Badge variant="muted">avg {{ v.avg_score ?? "—" }}%</Badge>
            </RouterLink>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Recent applications</CardTitle></CardHeader>
        <CardContent>
          <div v-if="!data.recent.length" class="text-sm text-muted-foreground">Nothing yet.</div>
          <RouterLink
            v-for="a in data.recent"
            :key="a.id"
            :to="{ name: 'application', params: { id: a.id } }"
            class="flex items-center justify-between gap-4 border-b py-3 last:border-0 hover:bg-accent/50 -mx-2 px-2 rounded"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-medium">
                {{ a.candidate?.full_name || a.candidate?.telegram_username || a.original_filename || "Candidate" }}
              </p>
              <p class="text-xs text-muted-foreground">{{ formatDate(a.created_at) }}</p>
            </div>
            <ScoreBar :value="a.match_percentage" class="max-w-[160px]" />
          </RouterLink>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
