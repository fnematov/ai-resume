<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { CheckCircle2 } from "lucide-vue-next"
import { ref } from "vue"

import { apiError } from "@/api/client"
import { orgApi, schedulingApi } from "@/api/endpoints"
import type { EventType } from "@/api/types"
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, Spinner } from "@/components/ui"

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
        Interview scheduling (Calendly)
        <Badge v-if="org?.calendly_configured" variant="success"><CheckCircle2 class="mr-1 h-3 w-3" /> Connected</Badge>
      </CardTitle>
      <CardDescription>
        Paste a Calendly Personal Access Token, pick an event type. Connect your Google Calendar
        inside Calendly so bookings auto-create the calendar event + Meet link.
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-3">
      <div v-if="org?.calendly_configured" class="rounded-md bg-green-50 p-3 text-sm text-green-800">
        ✓ Connected. Scheduling link active:
        <a :href="org.calendly_scheduling_url || '#'" target="_blank" class="break-all underline">{{ org.calendly_scheduling_url }}</a>
        <p class="mt-1 text-green-700">Paste a token below only to reconnect or change the event type.</p>
      </div>

      <div class="space-y-2">
        <Label>Calendly Personal Access Token</Label>
        <div class="flex gap-2">
          <Input v-model="token" type="password" :placeholder="org?.calendly_configured ? '•••••••• (saved)' : 'eyJ…'" class="flex-1" />
          <Button variant="secondary" :disabled="!token || loadTypes.isPending.value" @click="loadTypes.mutate()">
            <Spinner v-if="loadTypes.isPending.value" /> Load events
          </Button>
        </div>
      </div>

      <div v-if="eventTypes.length" class="space-y-2">
        <Label>Event type</Label>
        <select v-model="selected" class="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm">
          <option v-for="t in eventTypes" :key="t.uri" :value="t.uri">
            {{ t.name }}{{ t.duration ? ` · ${t.duration} min` : "" }}
          </option>
        </select>
        <Button :disabled="connect.isPending.value" @click="connect.mutate()">
          <Spinner v-if="connect.isPending.value" /> Connect
        </Button>
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
      <p v-if="ok" class="text-sm text-green-600">Calendly connected. Interview invites now include your link.</p>
    </CardContent>
  </Card>
</template>
