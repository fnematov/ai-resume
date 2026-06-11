<script setup lang="ts">
import { useQuery, useQueryClient } from "@tanstack/vue-query"
import { ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import draggable from "vuedraggable"

import { applicationApi, vacancyApi } from "@/api/endpoints"
import type { ApplicationListItem, ApplicationStage } from "@/api/types"
import { STAGE_LABELS, STAGE_ORDER } from "@/api/types"
import { Badge, ScoreBar, Spinner } from "@/components/ui"

const route = useRoute()
const router = useRouter()
const qc = useQueryClient()
const vacancyId = Number(route.params.id)

// Columns shown on the board: the linear pipeline + a Rejected column.
const COLUMNS: ApplicationStage[] = [...STAGE_ORDER, "rejected"]

const { data: vacancy } = useQuery({
  queryKey: ["vacancy", vacancyId],
  queryFn: () => vacancyApi.get(vacancyId),
})
const { data, isLoading } = useQuery({
  queryKey: ["pipeline", vacancyId],
  queryFn: () => applicationApi.list({ vacancy_id: vacancyId, sort: "score_desc" }),
})

// Local reactive board state (draggable mutates these arrays).
const board = ref<Record<string, ApplicationListItem[]>>({})

function rebuild(items: ApplicationListItem[]) {
  const next: Record<string, ApplicationListItem[]> = {}
  for (const col of COLUMNS) next[col] = []
  for (const a of items) {
    const col = COLUMNS.includes(a.stage) ? a.stage : "rejected"
    next[col].push(a)
  }
  board.value = next
}

watch(data, (items) => items && rebuild(items), { immediate: true })

async function onChange(stage: ApplicationStage, evt: any) {
  const added = evt?.added
  if (!added) return
  const app = added.element as ApplicationListItem
  try {
    await applicationApi.updateStage(app.id, stage)
    app.stage = stage
  } catch {
    // revert on failure
    qc.invalidateQueries({ queryKey: ["pipeline", vacancyId] })
  }
}

const stageColor: Record<string, string> = {
  new: "border-t-slate-400",
  screening: "border-t-blue-400",
  shortlisted: "border-t-violet-400",
  test_task: "border-t-amber-400",
  interview: "border-t-cyan-400",
  offer: "border-t-emerald-400",
  hired: "border-t-green-500",
  rejected: "border-t-red-400",
}

function openApp(id: number) {
  router.push({ name: "application", params: { id } })
}
</script>

<template>
  <div class="space-y-5">
    <div>
      <button class="text-sm text-muted-foreground hover:text-foreground" @click="router.push({ name: 'vacancy', params: { id: vacancyId } })">
        ← {{ vacancy?.title || "Vacancy" }}
      </button>
      <div class="mt-1 flex items-center justify-between">
        <h1 class="text-2xl font-bold tracking-tight">Pipeline</h1>
        <RouterLink :to="{ name: 'vacancy', params: { id: vacancyId } }" class="text-sm text-primary hover:underline">
          Ranked list →
        </RouterLink>
      </div>
    </div>

    <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>

    <div v-else class="flex gap-4 overflow-x-auto pb-4">
      <div v-for="col in COLUMNS" :key="col" class="w-72 shrink-0">
        <div class="mb-2 flex items-center justify-between px-1">
          <span class="text-sm font-semibold">{{ STAGE_LABELS[col] }}</span>
          <Badge variant="muted">{{ board[col]?.length || 0 }}</Badge>
        </div>
        <draggable
          :list="board[col]"
          group="apps"
          item-key="id"
          class="min-h-[120px] space-y-2 rounded-lg bg-muted/40 p-2"
          :animation="150"
          @change="(e: any) => onChange(col, e)"
        >
          <template #item="{ element }">
            <div
              class="cursor-grab rounded-md border-t-2 bg-card p-3 shadow-sm hover:shadow active:cursor-grabbing"
              :class="stageColor[col]"
              @click="openApp(element.id)"
            >
              <p class="truncate text-sm font-medium">
                {{ element.candidate?.full_name || element.candidate?.telegram_username || element.original_filename || "Candidate" }}
              </p>
              <div class="mt-2"><ScoreBar :value="element.match_percentage" /></div>
            </div>
          </template>
        </draggable>
      </div>
    </div>
  </div>
</template>
