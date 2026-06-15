<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { CheckCircle2, ExternalLink } from "lucide-vue-next"
import { ref } from "vue"

import { apiError } from "@/api/client"
import { orgApi, schedulingApi } from "@/api/endpoints"
import type { EventType } from "@/api/types"
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, Spinner } from "@/components/ui"

const CALENDLY_API_URL = "https://calendly.com/integrations/api_webhooks"

const qc = useQueryClient()
const { data: org } = useQuery({ queryKey: ["org"], queryFn: orgApi.me })

const token = ref("")
const eventTypes = ref<EventType[]>([])
const selected = ref<string>("")
const error = ref("")
const ok = ref(false)

const loadTypes = useMutation({
  mutationFn: () => schedulingApi.eventTypes(token.value),
  onSuccess: (types) => {
    eventTypes.value = types
    selected.value = types[0]?.uri ?? ""
    error.value = ""
  },
  onError: (e) => (error.value = apiError(e)),
})

const connect = useMutation({
  mutationFn: () => {
    const et = eventTypes.value.find((t) => t.uri === selected.value)!
    return schedulingApi.connect({
      token: token.value,
      event_type_uri: et.uri,
      scheduling_url: et.scheduling_url,
    })
  },
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["org"] })
    token.value = ""
    eventTypes.value = []
    ok.value = true
  },
  onError: (e) => (error.value = apiError(e)),
})
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        {{ $t("calendly.title") }}
        <Badge v-if="org?.calendly_configured" variant="success"><CheckCircle2 class="mr-1 h-3 w-3" /> {{ $t("calendly.connected") }}</Badge>
      </CardTitle>
      <CardDescription>{{ $t("calendly.hint") }}</CardDescription>
    </CardHeader>
    <CardContent class="space-y-3">
      <div v-if="org?.calendly_configured" class="rounded-md bg-green-50 p-3 text-sm text-green-800">
        {{ $t("calendly.connectedActive") }}
        <a :href="org.calendly_scheduling_url || '#'" target="_blank" class="break-all underline">{{ org.calendly_scheduling_url }}</a>
        <p class="mt-1 text-green-700">{{ $t("calendly.reconnectHint") }}</p>
      </div>

      <!-- How-to guide -->
      <details class="rounded-md border bg-muted/30 p-3 text-sm" :open="!org?.calendly_configured">
        <summary class="cursor-pointer font-medium">{{ $t("calendly.guideTitle") }}</summary>
        <div class="mt-3 space-y-3">
          <a :href="CALENDLY_API_URL" target="_blank" rel="noopener" class="inline-block">
            <Button type="button" variant="secondary" size="sm">
              <ExternalLink class="h-4 w-4" /> {{ $t("calendly.openCalendly") }}
            </Button>
          </a>
          <ol class="list-decimal space-y-1 pl-5 text-muted-foreground">
            <li>{{ $t("calendly.step1") }}</li>
            <li>{{ $t("calendly.step2") }}</li>
            <li>{{ $t("calendly.step3") }}</li>
            <li>{{ $t("calendly.step4") }}</li>
            <li>{{ $t("calendly.step5") }}</li>
          </ol>
          <p class="rounded bg-amber-50 p-2 text-xs text-amber-800">⚠️ {{ $t("calendly.noteScopes") }}</p>
          <p class="text-xs text-muted-foreground">{{ $t("calendly.notePlan") }}</p>
        </div>
      </details>

      <div class="space-y-2">
        <Label>{{ $t("calendly.token") }}</Label>
        <div class="flex gap-2">
          <Input v-model="token" type="password" :placeholder="org?.calendly_configured ? '•••••••• (saved)' : 'eyJ…'" class="flex-1" />
          <Button :disabled="!token || loadTypes.isPending.value" @click="loadTypes.mutate()">
            <Spinner v-if="loadTypes.isPending.value" /> {{ $t("calendly.loadEvents") }}
          </Button>
        </div>
      </div>

      <div v-if="eventTypes.length" class="space-y-2">
        <Label>{{ $t("calendly.eventType") }}</Label>
        <select v-model="selected" class="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm">
          <option v-for="t in eventTypes" :key="t.uri" :value="t.uri">
            {{ t.name }}{{ t.duration ? ` · ${t.duration} min` : "" }}
          </option>
        </select>
        <Button :disabled="connect.isPending.value" @click="connect.mutate()">
          <Spinner v-if="connect.isPending.value" /> {{ $t("calendly.connect") }}
        </Button>
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
      <p v-if="ok" class="text-sm text-green-600">{{ $t("calendly.connectedMsg") }}</p>
    </CardContent>
  </Card>
</template>
