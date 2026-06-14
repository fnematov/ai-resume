<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { ref, watch } from "vue"

import { apiError } from "@/api/client"
import { authApi, orgApi } from "@/api/endpoints"
import {
  Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle,
  Input, Label, Spinner, Textarea,
} from "@/components/ui"
import { useAuthStore } from "@/stores/auth"
import { useOrg } from "@/composables/useOrg"

const auth = useAuthStore()
const qc = useQueryClient()
const { isActive } = useOrg()

// --- Company profile (org users only) ---
const { data: org } = useQuery({ queryKey: ["org"], queryFn: orgApi.me, enabled: auth.isOrgUser })
const form = ref({ name: "", about: "", website: "" })
const profOk = ref(false)
const profErr = ref("")
watch(
  org,
  (o) => {
    if (o) form.value = { name: o.name ?? "", about: o.about ?? "", website: o.website ?? "" }
  },
  { immediate: true },
)
const saveProfile = useMutation({
  mutationFn: () =>
    orgApi.setProfile({
      name: form.value.name,
      about: form.value.about || null,
      website: form.value.website || null,
    }),
  onSuccess: () => {
    qc.invalidateQueries({ queryKey: ["org"] })
    profOk.value = true
    profErr.value = ""
  },
  onError: (e) => ((profErr.value = apiError(e)), (profOk.value = false)),
})

// --- Change password (all users) ---
const pw = ref({ old: "", new_: "" })
const pwOk = ref(false)
const pwErr = ref("")
const changePw = useMutation({
  mutationFn: () => authApi.changePassword(pw.value.old, pw.value.new_),
  onSuccess: () => {
    pwOk.value = true
    pwErr.value = ""
    pw.value = { old: "", new_: "" }
  },
  onError: (e) => ((pwErr.value = apiError(e)), (pwOk.value = false)),
})
</script>

<template>
  <div class="max-w-2xl space-y-6">
    <!-- Company profile -->
    <Card v-if="auth.isOrgUser">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          {{ $t("profile.title") }}
          <Badge v-if="org" :variant="org.status === 'active' ? 'success' : 'warning'">{{ org.status }}</Badge>
        </CardTitle>
        <CardDescription>{{ $t("profile.hint") }}</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <Label>{{ $t("profile.name") }}</Label>
          <Input v-model="form.name" class="max-w-md" />
        </div>
        <div class="space-y-2">
          <Label>{{ $t("profile.about") }}</Label>
          <Textarea v-model="form.about" :rows="4" :placeholder="$t('profile.aboutPlaceholder')" />
        </div>
        <div class="space-y-2">
          <Label>{{ $t("profile.website") }}</Label>
          <Input v-model="form.website" placeholder="https://example.com" class="max-w-md" />
        </div>
        <p v-if="profErr" class="text-sm text-destructive">{{ profErr }}</p>
        <p v-if="profOk" class="text-sm text-green-600">{{ $t("profile.saved") }}</p>
        <Button :disabled="saveProfile.isPending.value || !isActive || form.name.length < 2" @click="saveProfile.mutate()">
          <Spinner v-if="saveProfile.isPending.value" /> {{ $t("common.save") }}
        </Button>
      </CardContent>
    </Card>

    <!-- Change password -->
    <Card>
      <CardHeader>
        <CardTitle>{{ $t("account.changePassword") }}</CardTitle>
        <CardDescription>{{ auth.user?.email }}</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-3" @submit.prevent="changePw.mutate()">
          <div class="space-y-2">
            <Label>{{ $t("account.currentPassword") }}</Label>
            <Input v-model="pw.old" type="password" class="max-w-sm" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("account.newPassword") }}</Label>
            <Input v-model="pw.new_" type="password" placeholder="••••••••" class="max-w-sm" />
          </div>
          <p v-if="pwErr" class="text-sm text-destructive">{{ pwErr }}</p>
          <p v-if="pwOk" class="text-sm text-green-600">{{ $t("account.passwordChanged") }}</p>
          <Button type="submit" :disabled="changePw.isPending.value || !pw.old || !pw.new_">
            <Spinner v-if="changePw.isPending.value" /> {{ $t("account.changePassword") }}
          </Button>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
