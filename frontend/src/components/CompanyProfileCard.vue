<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { ref, watch } from "vue"

import { apiError } from "@/api/client"
import { orgApi } from "@/api/endpoints"
import { useOrg } from "@/composables/useOrg"
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, Spinner, Textarea } from "@/components/ui"

const qc = useQueryClient()
const { data: org } = useQuery({ queryKey: ["org"], queryFn: orgApi.me })
const { isActive } = useOrg()

const about = ref("")
const website = ref("")
const error = ref("")
const ok = ref(false)

watch(
  org,
  (o) => {
    if (o) {
      about.value = o.about ?? ""
      website.value = o.website ?? ""
    }
  },
  { immediate: true },
)

const save = useMutation({
  mutationFn: () => orgApi.setProfile(about.value || null, website.value || null),
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
      <CardTitle>{{ $t("profile.title") }}</CardTitle>
      <CardDescription>{{ $t("profile.hint") }}</CardDescription>
    </CardHeader>
    <CardContent class="space-y-3">
      <div class="space-y-2">
        <Label>{{ $t("profile.about") }}</Label>
        <Textarea v-model="about" :rows="4" :placeholder="$t('profile.aboutPlaceholder')" />
      </div>
      <div class="space-y-2">
        <Label>{{ $t("profile.website") }}</Label>
        <Input v-model="website" placeholder="https://example.com" class="max-w-md" />
      </div>
      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
      <p v-if="ok" class="text-sm text-green-600">{{ $t("profile.saved") }}</p>
      <Button :disabled="save.isPending.value || !isActive" @click="save.mutate()">
        <Spinner v-if="save.isPending.value" /> {{ $t("common.save") }}
      </Button>
    </CardContent>
  </Card>
</template>
