<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Plus, Trash2 } from "lucide-vue-next"
import { computed, ref } from "vue"

import { apiError } from "@/api/client"
import { automationApi, templateApi } from "@/api/endpoints"
import type { AutomationRule } from "@/api/types"
import { useOrg } from "@/composables/useOrg"
import PendingBanner from "@/components/PendingBanner.vue"
import { Badge, Button, Card, CardContent, Input, Label, Modal, Spinner } from "@/components/ui"

const qc = useQueryClient()
const { isActive } = useOrg()
const { data: rules, isLoading } = useQuery({
  queryKey: ["automation-rules"],
  queryFn: automationApi.list,
  enabled: isActive,
})
const { data: templates } = useQuery({
  queryKey: ["templates"],
  queryFn: templateApi.list,
  enabled: isActive,
})

const ACTION_LABELS: Record<string, string> = {
  reject: "Auto-reject",
  shortlist: "Auto-shortlist",
  send_template: "Send message",
  set_stage: "Set stage",
}
const templateName = (id: number | null) =>
  id ? templates.value?.find((t) => t.id === id)?.name ?? "—" : "—"

const invalidate = () => qc.invalidateQueries({ queryKey: ["automation-rules"] })
const open = ref(false)
const error = ref("")
const form = ref<Partial<AutomationRule>>({ name: "", min_score: 0, max_score: 30, action: "reject", template_id: null })

function openNew() {
  form.value = { name: "", min_score: 0, max_score: 30, action: "reject", template_id: null }
  error.value = ""
  open.value = true
}

const create = useMutation({
  mutationFn: () => automationApi.create(form.value),
  onSuccess: () => {
    invalidate()
    open.value = false
  },
  onError: (e) => (error.value = apiError(e)),
})
const remove = useMutation({ mutationFn: (id: number) => automationApi.remove(id), onSuccess: invalidate })
const toggle = useMutation({
  mutationFn: (r: AutomationRule) => automationApi.update(r.id, { enabled: !r.enabled }),
  onSuccess: invalidate,
})

const hasRules = computed(() => (rules.value?.length ?? 0) > 0)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">{{ $t("automation.title") }}</h1>
        <p class="text-muted-foreground">{{ $t("automation.subtitle") }}</p>
      </div>
      <Button :disabled="!isActive" @click="openNew"><Plus class="h-4 w-4" /> {{ $t("automation.new") }}</Button>
    </div>

    <PendingBanner />

    <Card>
      <CardContent class="p-0">
        <div v-if="isLoading" class="grid place-items-center py-16"><Spinner class="h-6 w-6" /></div>
        <div v-else-if="!hasRules" class="py-16 text-center text-muted-foreground">
          No automation rules yet. Add one to auto-reject or auto-shortlist by score.
        </div>
        <table v-else class="w-full text-sm">
          <thead class="border-b text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-4 py-3 font-medium">Name</th>
              <th class="px-4 py-3 font-medium">Condition</th>
              <th class="px-4 py-3 font-medium">Action</th>
              <th class="px-4 py-3 font-medium">Template</th>
              <th class="px-4 py-3 font-medium">Status</th>
              <th class="px-4 py-3 font-medium text-right"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rules" :key="r.id" class="border-b last:border-0 hover:bg-accent/40">
              <td class="px-4 py-3 font-medium">{{ r.name || ACTION_LABELS[r.action] }}</td>
              <td class="px-4 py-3 text-muted-foreground">score {{ r.min_score }}–{{ r.max_score }}%</td>
              <td class="px-4 py-3">{{ ACTION_LABELS[r.action] }}</td>
              <td class="px-4 py-3 text-muted-foreground">{{ templateName(r.template_id) }}</td>
              <td class="px-4 py-3">
                <Badge :variant="r.enabled ? 'success' : 'muted'" class="cursor-pointer" @click="toggle.mutate(r)">
                  {{ r.enabled ? "on" : "off" }}
                </Badge>
              </td>
              <td class="px-4 py-3 text-right">
                <Button variant="ghost" size="icon" :disabled="remove.isPending.value" @click="remove.mutate(r.id)">
                  <Trash2 class="h-4 w-4" />
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>

    <Modal :open="open" title="New automation rule" @close="open = false">
      <form class="space-y-4" @submit.prevent="create.mutate()">
        <div class="space-y-2">
          <Label>Name (optional)</Label>
          <Input v-model="form.name" placeholder="e.g. Auto-reject weak applicants" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-2">
            <Label>Min score %</Label>
            <Input v-model.number="form.min_score" type="number" min="0" max="100" />
          </div>
          <div class="space-y-2">
            <Label>Max score %</Label>
            <Input v-model.number="form.max_score" type="number" min="0" max="100" />
          </div>
        </div>
        <div class="space-y-2">
          <Label>Action</Label>
          <select v-model="form.action" class="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm">
            <option value="reject">Auto-reject</option>
            <option value="shortlist">Auto-shortlist</option>
            <option value="send_template">Send message only</option>
          </select>
        </div>
        <div class="space-y-2">
          <Label>Message template (optional)</Label>
          <select v-model="form.template_id" class="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm">
            <option :value="null">— none —</option>
            <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <p class="text-xs text-muted-foreground">If set, this message is sent to the candidate automatically.</p>
        </div>
        <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
        <div class="flex justify-end gap-2">
          <Button type="button" variant="ghost" @click="open = false">Cancel</Button>
          <Button type="submit" :disabled="create.isPending.value"><Spinner v-if="create.isPending.value" /> Add rule</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>
