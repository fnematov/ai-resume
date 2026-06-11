<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Plus } from "lucide-vue-next"
import { ref } from "vue"

import { apiError } from "@/api/client"
import { vacancyApi } from "@/api/endpoints"
import type { Vacancy, VacancyStatus } from "@/api/types"
import {
  Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner, Textarea,
} from "@/components/ui"

const qc = useQueryClient()
const { data: vacancies, isLoading } = useQuery({ queryKey: ["vacancies"], queryFn: vacancyApi.list })

const showForm = ref(false)
const error = ref("")
const form = ref({ title: "", description: "", requirements: "", employment_type: "", location: "", status: "open" as VacancyStatus })

const create = useMutation({
  mutationFn: () => vacancyApi.create(form.value),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["vacancies"] })
    showForm.value = false
    form.value = { title: "", description: "", requirements: "", employment_type: "", location: "", status: "open" }
  },
  onError: (e) => (error.value = apiError(e)),
})

const statusVariant: Record<VacancyStatus, "success" | "muted" | "secondary"> = {
  open: "success",
  draft: "secondary",
  closed: "muted",
}
function badge(v: Vacancy) {
  return statusVariant[v.status]
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Vacancies</h1>
        <p class="text-muted-foreground">Create roles and share their Telegram links.</p>
      </div>
      <Button @click="showForm = !showForm"><Plus class="h-4 w-4" /> New vacancy</Button>
    </div>

    <Card v-if="showForm">
      <CardHeader><CardTitle>New vacancy</CardTitle></CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="create.mutate()">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2 sm:col-span-2">
              <Label>Title</Label>
              <Input v-model="form.title" placeholder="PHP / Laravel Developer" />
            </div>
            <div class="space-y-2">
              <Label>Employment type</Label>
              <Input v-model="form.employment_type" placeholder="Full-time" />
            </div>
            <div class="space-y-2">
              <Label>Location</Label>
              <Input v-model="form.location" placeholder="Remote" />
            </div>
          </div>
          <div class="space-y-2">
            <Label>Description</Label>
            <Textarea v-model="form.description" :rows="3" placeholder="What the role involves…" />
          </div>
          <div class="space-y-2">
            <Label>Requirements / must-haves</Label>
            <Textarea v-model="form.requirements" :rows="3" placeholder="PHP, Laravel, MySQL, 3+ years…" />
          </div>
          <div class="space-y-2">
            <Label>Status</Label>
            <select v-model="form.status" class="h-9 w-40 rounded-md border border-input bg-transparent px-3 text-sm">
              <option value="open">Open</option>
              <option value="draft">Draft</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <div class="flex gap-2">
            <Button type="submit" :disabled="create.isPending.value"><Spinner v-if="create.isPending.value" /> Create</Button>
            <Button type="button" variant="ghost" @click="showForm = false">Cancel</Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>
    <Card v-else-if="!vacancies?.length">
      <CardContent class="py-16 text-center text-muted-foreground">
        No vacancies yet. Create your first role to start collecting resumes.
      </CardContent>
    </Card>
    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink v-for="v in vacancies" :key="v.id" :to="{ name: 'vacancy', params: { id: v.id } }">
        <Card class="h-full transition-colors hover:border-primary/40">
          <CardContent class="p-5 space-y-2">
            <div class="flex items-start justify-between gap-2">
              <h3 class="font-semibold leading-tight">{{ v.title }}</h3>
              <Badge :variant="badge(v)">{{ v.status }}</Badge>
            </div>
            <p class="text-sm text-muted-foreground line-clamp-2">{{ v.description || "No description" }}</p>
            <p class="text-xs text-muted-foreground pt-2">{{ v.application_count }} applicants</p>
          </CardContent>
        </Card>
      </RouterLink>
    </div>
  </div>
</template>
