<script setup lang="ts">
import { useMutation, useQueryClient } from "@tanstack/vue-query"
import { computed, ref, watch } from "vue"

import { apiError } from "@/api/client"
import { applicationApi } from "@/api/endpoints"
import type { Template, TemplateType } from "@/api/types"
import { Button, Label, Modal, Spinner, Textarea, Input } from "@/components/ui"

const props = defineProps<{
  open: boolean
  action: "test_task" | "interview" | "offer" | "reject" | null
  applicationId: number
  templates: Template[]
  schedulingConfigured?: boolean
}>()
const emit = defineEmits<{ (e: "close"): void; (e: "sent"): void }>()

const qc = useQueryClient()
const error = ref("")
const body = ref("")
const selectedTemplateId = ref<number | null>(null)
const variables = ref<Record<string, string>>({})

const ACTION_META: Record<string, { title: string; type: TemplateType; cta: string; vars: { key: string; label: string; textarea?: boolean }[] }> = {
  test_task: { title: "Send test task", type: "test_task", cta: "Send test task", vars: [
    { key: "test_task", label: "Test task instructions", textarea: true },
    { key: "deadline", label: "Deadline" },
  ] },
  interview: { title: "Invite to interview", type: "interview", cta: "Send invitation", vars: [] },
  offer: { title: "Send offer", type: "offer", cta: "Send offer", vars: [
    { key: "salary", label: "Salary" },
    { key: "start_date", label: "Start date" },
  ] },
  reject: { title: "Reject candidate", type: "rejection", cta: "Send rejection", vars: [] },
}

// Build a literal "{{name}}" string at runtime (can't write it inline in a Vue template).
const ph = (s: string) => `{{${s}}}`

const meta = computed(() => (props.action ? ACTION_META[props.action] : null))
const relevantTemplates = computed(() =>
  meta.value ? props.templates.filter((t) => t.type === meta.value!.type) : [],
)

watch(
  () => [props.open, props.action],
  () => {
    if (!props.open || !meta.value) return
    error.value = ""
    variables.value = {}
    const first = relevantTemplates.value[0]
    selectedTemplateId.value = first?.id ?? null
    body.value = first?.body ?? ""
  },
  { immediate: true },
)

watch(selectedTemplateId, (id) => {
  const t = props.templates.find((x) => x.id === id)
  if (t) body.value = t.body
})

const send = useMutation({
  mutationFn: () =>
    applicationApi.runAction(props.applicationId, props.action!, {
      template_id: selectedTemplateId.value,
      body: body.value,
      variables: variables.value,
    }),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["application", props.applicationId] })
    qc.invalidateQueries({ queryKey: ["app-messages", props.applicationId] })
    qc.invalidateQueries({ queryKey: ["app-timeline", props.applicationId] })
    emit("sent")
    emit("close")
  },
  onError: (e) => (error.value = apiError(e)),
})
</script>

<template>
  <Modal :open="open" :title="meta?.title" subtitle="The candidate receives this in Telegram." @close="emit('close')">
    <div v-if="meta" class="space-y-4">
      <div v-if="action === 'interview' && !schedulingConfigured" class="rounded-md bg-amber-50 p-3 text-sm text-amber-800">
        ⚠️ No Calendly link configured. Add one in Settings so <code>{{ ph('scheduling_link') }}</code> resolves.
      </div>

      <div v-if="relevantTemplates.length > 1" class="space-y-2">
        <Label>Template</Label>
        <select v-model="selectedTemplateId" class="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm">
          <option v-for="t in relevantTemplates" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
      </div>

      <div v-for="v in meta.vars" :key="v.key" class="space-y-2">
        <Label>{{ v.label }}</Label>
        <Textarea v-if="v.textarea" v-model="variables[v.key]" :rows="3" />
        <Input v-else v-model="variables[v.key]" />
      </div>

      <div class="space-y-2">
        <Label>Message</Label>
        <Textarea v-model="body" :rows="7" />
        <p class="text-xs text-muted-foreground">
          <code>{{ ph('candidate_name') }}</code>, <code>{{ ph('job_title') }}</code>,
          <code>{{ ph('company') }}</code> are filled automatically.
        </p>
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="emit('close')">Cancel</Button>
        <Button :variant="action === 'reject' ? 'destructive' : 'default'" :disabled="send.isPending.value" @click="send.mutate()">
          <Spinner v-if="send.isPending.value" /> {{ meta.cta }}
        </Button>
      </div>
    </div>
  </Modal>
</template>
