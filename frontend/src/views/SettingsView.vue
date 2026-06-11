<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { CheckCircle2 } from "lucide-vue-next"
import { ref, watch } from "vue"

import { apiError } from "@/api/client"
import { orgApi } from "@/api/endpoints"
import CalendlyCard from "@/components/CalendlyCard.vue"
import GdprCard from "@/components/GdprCard.vue"
import {
  Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, Spinner,
} from "@/components/ui"

const tab = ref<"integrations" | "privacy">("integrations")
const TABS = [
  { key: "integrations", label: "Integrations" },
  { key: "privacy", label: "Privacy & data" },
] as const

const qc = useQueryClient()
const { data: org } = useQuery({ queryKey: ["org"], queryFn: orgApi.me })

const botToken = ref("")
const tgError = ref("")
const tgOk = ref(false)
const saveTelegram = useMutation({
  mutationFn: () => orgApi.setTelegram(botToken.value),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["org"] })
    qc.invalidateQueries({ queryKey: ["vacancies"] })
    botToken.value = ""
    tgError.value = ""
    tgOk.value = true
  },
  onError: (e) => ((tgError.value = apiError(e)), (tgOk.value = false)),
})

const ai = ref({ provider: "claude", model: "claude-sonnet-4-6", api_key: "" })
// Pre-fill the non-secret AI fields from the saved org config (the key stays write-only).
watch(
  org,
  (o) => {
    if (o?.ai_provider) ai.value.provider = o.ai_provider
    if (o?.ai_model) ai.value.model = o.ai_model
  },
  { immediate: true },
)
const aiError = ref("")
const aiOk = ref(false)
const saveAI = useMutation({
  mutationFn: () => orgApi.setAI(ai.value.provider, ai.value.model, ai.value.api_key),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["org"] })
    ai.value.api_key = ""
    aiError.value = ""
    aiOk.value = true
  },
  onError: (e) => ((aiError.value = apiError(e)), (aiOk.value = false)),
})

function onProviderChange() {
  ai.value.model = ai.value.provider === "claude" ? "claude-sonnet-4-6" : "gpt-4o"
}
</script>

<template>
  <div class="space-y-6 max-w-2xl">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Settings</h1>
      <p class="text-muted-foreground">Integrations and data settings for your organization.</p>
    </div>

    <Card v-if="org && org.status !== 'active'" class="border-amber-300 bg-amber-50">
      <CardContent class="p-4 text-sm text-amber-900">
        Your organization is <b>{{ org.status }}</b>. Settings save once an admin approves it.
      </CardContent>
    </Card>

    <!-- Tabs -->
    <div class="flex gap-1 border-b">
      <button
        v-for="t in TABS"
        :key="t.key"
        class="-mb-px border-b-2 px-4 py-2 text-sm font-medium"
        :class="tab === t.key ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'"
        @click="tab = t.key"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Integrations tab -->
    <div v-show="tab === 'integrations'" class="space-y-6">
    <!-- Telegram -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          Telegram bot
          <Badge v-if="org?.telegram_configured" variant="success">
            <CheckCircle2 class="h-3 w-3 mr-1" /> @{{ org.telegram_bot_username }}
          </Badge>
        </CardTitle>
        <CardDescription>
          Create a bot with @BotFather, paste its token here. We register the webhook automatically.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-3" @submit.prevent="saveTelegram.mutate()">
          <div class="space-y-2">
            <Label>Bot token</Label>
            <Input v-model="botToken" type="password" :placeholder="org?.telegram_configured ? '•••••••• (saved)' : '123456:ABC-DEF…'" />
            <p v-if="org?.telegram_configured" class="text-xs text-muted-foreground">
              ✓ A bot token is saved (hidden for security). Enter a new token only to replace it.
            </p>
          </div>
          <p v-if="tgError" class="text-sm text-destructive">{{ tgError }}</p>
          <p v-if="tgOk" class="text-sm text-green-600">Bot connected & webhook registered.</p>
          <Button type="submit" :disabled="saveTelegram.isPending.value || !botToken">
            <Spinner v-if="saveTelegram.isPending.value" /> Save bot
          </Button>
        </form>
      </CardContent>
    </Card>

    <!-- AI -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          AI provider
          <Badge v-if="org?.ai_configured" variant="success">
            <CheckCircle2 class="h-3 w-3 mr-1" /> {{ org.ai_provider }} · {{ org.ai_model }}
          </Badge>
        </CardTitle>
        <CardDescription>Bring your own API key. It is encrypted at rest and never shown again.</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-3" @submit.prevent="saveAI.mutate()">
          <div class="grid gap-3 sm:grid-cols-2">
            <div class="space-y-2">
              <Label>Provider</Label>
              <select v-model="ai.provider" class="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm" @change="onProviderChange">
                <option value="claude">Claude (Anthropic)</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div class="space-y-2">
              <Label>Model</Label>
              <Input v-model="ai.model" placeholder="claude-sonnet-4-6" />
            </div>
          </div>
          <div class="space-y-2">
            <Label>API key</Label>
            <Input v-model="ai.api_key" type="password" :placeholder="org?.ai_configured ? '•••••••• (saved)' : 'sk-…'" />
            <p v-if="org?.ai_configured" class="text-xs text-muted-foreground">
              ✓ An API key is saved (hidden). Enter a new one only to replace it.
            </p>
          </div>
          <p v-if="aiError" class="text-sm text-destructive">{{ aiError }}</p>
          <p v-if="aiOk" class="text-sm text-green-600">AI provider saved.</p>
          <Button type="submit" :disabled="saveAI.isPending.value || (!ai.api_key && !org?.ai_configured)">
            <Spinner v-if="saveAI.isPending.value" /> Save AI settings
          </Button>
        </form>
      </CardContent>
    </Card>

    <!-- Calendly scheduling -->
    <CalendlyCard />
    </div>

    <!-- Privacy & data tab -->
    <div v-show="tab === 'privacy'" class="space-y-6">
      <GdprCard />
    </div>
  </div>
</template>
