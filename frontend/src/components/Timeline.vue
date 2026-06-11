<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query"
import {
  Bot,
  CalendarCheck,
  CheckCircle2,
  FileCheck,
  MessageSquare,
  Send,
  Shield,
  Star,
  UserX,
} from "lucide-vue-next"
import type { Component } from "vue"

import { applicationApi } from "@/api/endpoints"
import { Spinner } from "@/components/ui"
import { formatDate } from "@/lib/utils"

const props = defineProps<{ applicationId: number }>()

const { data: items, isLoading } = useQuery({
  queryKey: ["app-timeline", props.applicationId],
  queryFn: () => applicationApi.timeline(props.applicationId),
})

const ICONS: Record<string, Component> = {
  application_created: FileCheck,
  ai_scored: Bot,
  stage_changed: Star,
  message_sent: Send,
  message_received: MessageSquare,
  test_submitted: FileCheck,
  test_graded: CheckCircle2,
  interview_scheduled: CalendarCheck,
  offer_sent: Star,
  rejected: UserX,
  consent_given: Shield,
}
</script>

<template>
  <div>
    <div v-if="isLoading" class="grid place-items-center py-8"><Spinner /></div>
    <p v-else-if="!items?.length" class="py-8 text-center text-sm text-muted-foreground">No activity yet.</p>
    <ol v-else class="space-y-4">
      <li v-for="a in items" :key="a.id" class="flex gap-3">
        <div class="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-muted">
          <component :is="ICONS[a.type] || Star" class="h-3.5 w-3.5 text-muted-foreground" />
        </div>
        <div class="min-w-0">
          <p class="text-sm">{{ a.summary }}</p>
          <p class="text-xs text-muted-foreground">{{ a.actor }} · {{ formatDate(a.created_at) }}</p>
        </div>
      </li>
    </ol>
  </div>
</template>
