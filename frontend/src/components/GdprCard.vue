<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { ref, watch } from "vue"

import { apiError } from "@/api/client"
import { orgApi } from "@/api/endpoints"
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, Spinner, Textarea } from "@/components/ui"

const qc = useQueryClient()
const { data: org } = useQuery({ queryKey: ["org"], queryFn: orgApi.me })

const retentionDays = ref<number | null>(null)
const privacyNotice = ref("")
const error = ref("")
const ok = ref(false)

watch(
  org,
  (o) => {
    if (o) {
      retentionDays.value = o.retention_days ?? null
      privacyNotice.value = o.privacy_notice ?? ""
    }
  },
  { immediate: true },
)

const save = useMutation({
  mutationFn: () => orgApi.setGdpr(retentionDays.value || null, privacyNotice.value || null),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["org"] })
    error.value = ""
    ok.value = true
  },
  onError: (e) => (error.value = apiError(e)),
})
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Privacy & data retention (GDPR)</CardTitle>
      <CardDescription>
        Candidates consent when they apply and can send <code>/forget</code> to delete their data.
        Set an auto-deletion window and a privacy notice shown on application.
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-3">
      <div class="space-y-2">
        <Label>Auto-delete candidate data after (days)</Label>
        <Input v-model.number="retentionDays" type="number" min="0" placeholder="e.g. 180 (blank = keep)" class="w-56" />
      </div>
      <div class="space-y-2">
        <Label>Privacy notice (shown to candidates)</Label>
        <Textarea v-model="privacyNotice" :rows="3" placeholder="By applying you agree to…" />
      </div>
      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
      <p v-if="ok" class="text-sm text-green-600">Saved.</p>
      <Button :disabled="save.isPending.value" @click="save.mutate()">
        <Spinner v-if="save.isPending.value" /> Save
      </Button>
    </CardContent>
  </Card>
</template>
