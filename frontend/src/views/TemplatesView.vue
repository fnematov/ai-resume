<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Pencil, Plus, Trash2 } from "lucide-vue-next"
import { ref } from "vue"

import { apiError } from "@/api/client"
import { templateApi } from "@/api/endpoints"
import type { Template, TemplateType } from "@/api/types"
import VariableTextarea from "@/components/VariableTextarea.vue"
import { Badge, Button, Card, CardContent, Input, Label, Modal, Spinner } from "@/components/ui"

const qc = useQueryClient()
const { data: templates, isLoading } = useQuery({ queryKey: ["templates"], queryFn: templateApi.list })

const TYPE_LABELS: Record<string, string> = {
  test_task: "Test task",
  interview: "Interview",
  offer: "Offer",
  rejection: "Rejection",
  custom: "Custom",
}
const ph = (s: string) => `{{${s}}}`

const open = ref(false)
const editing = ref<Template | null>(null)
const form = ref<{ type: TemplateType; name: string; body: string }>({ type: "custom", name: "", body: "" })
const error = ref("")

function openNew() {
  editing.value = null
  form.value = { type: "custom", name: "", body: "" }
  error.value = ""
  open.value = true
}
function openEdit(t: Template) {
  editing.value = t
  form.value = { type: t.type, name: t.name, body: t.body }
  error.value = ""
  open.value = true
}

const save = useMutation({
  mutationFn: () =>
    editing.value
      ? templateApi.update(editing.value.id, { name: form.value.name, body: form.value.body })
      : templateApi.create(form.value),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["templates"] })
    open.value = false
  },
  onError: (e) => (error.value = apiError(e)),
})

const remove = useMutation({
  mutationFn: (id: number) => templateApi.remove(id),
  onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Message templates</h1>
        <p class="text-muted-foreground">
          Sent to candidates via Telegram. Variables like <code>{{ ph("candidate_name") }}</code>,
          <code>{{ ph("job_title") }}</code>, <code>{{ ph("scheduling_link") }}</code> fill in automatically.
        </p>
      </div>
      <Button @click="openNew"><Plus class="h-4 w-4" /> New template</Button>
    </div>

    <Card>
      <CardContent class="p-0">
        <div v-if="isLoading" class="grid place-items-center py-16"><Spinner class="h-6 w-6" /></div>
        <table v-else class="w-full text-sm">
          <thead class="border-b text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-4 py-3 font-medium">Type</th>
              <th class="px-4 py-3 font-medium">Name</th>
              <th class="px-4 py-3 font-medium">Preview</th>
              <th class="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in templates" :key="t.id" class="border-b last:border-0 hover:bg-accent/40">
              <td class="px-4 py-3"><Badge variant="secondary">{{ TYPE_LABELS[t.type] || t.type }}</Badge></td>
              <td class="px-4 py-3 font-medium">{{ t.name }}</td>
              <td class="max-w-md truncate px-4 py-3 text-muted-foreground">{{ t.body }}</td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-1">
                  <Button variant="ghost" size="icon" @click="openEdit(t)"><Pencil class="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" :disabled="remove.isPending.value" @click="remove.mutate(t.id)">
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>

    <Modal :open="open" :title="editing ? 'Edit template' : 'New template'" @close="open = false">
      <form class="space-y-4" @submit.prevent="save.mutate()">
        <div v-if="!editing" class="space-y-2">
          <Label>Type</Label>
          <select v-model="form.type" class="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm">
            <option value="test_task">Test task</option>
            <option value="interview">Interview</option>
            <option value="offer">Offer</option>
            <option value="rejection">Rejection</option>
            <option value="custom">Custom</option>
          </select>
        </div>
        <div class="space-y-2">
          <Label>Name</Label>
          <Input v-model="form.name" placeholder="e.g. Test task" />
        </div>
        <div class="space-y-2">
          <Label>Message body</Label>
          <VariableTextarea v-model="form.body" :rows="8" />
        </div>
        <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
        <div class="flex justify-end gap-2">
          <Button type="button" variant="ghost" @click="open = false">Cancel</Button>
          <Button type="submit" :disabled="save.isPending.value"><Spinner v-if="save.isPending.value" /> Save</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>
