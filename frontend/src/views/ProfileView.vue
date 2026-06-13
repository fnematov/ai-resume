<script setup lang="ts">
import { useMutation, useQuery } from "@tanstack/vue-query"
import { computed, ref } from "vue"

import { apiError } from "@/api/client"
import { authApi, orgApi } from "@/api/endpoints"
import {
  Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner,
} from "@/components/ui"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()

// --- Edit name ---
const fullName = ref(auth.user?.full_name ?? "")
const nameOk = ref(false)
const nameErr = ref("")
const saveName = useMutation({
  mutationFn: () => authApi.updateMe(fullName.value),
  onSuccess: (u) => {
    auth.user = u
    nameOk.value = true
    nameErr.value = ""
  },
  onError: (e) => ((nameErr.value = apiError(e)), (nameOk.value = false)),
})

// --- Change password ---
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

const { data: org } = useQuery({
  queryKey: ["org"],
  queryFn: orgApi.me,
  enabled: computed(() => auth.isOrgUser),
})
</script>

<template>
  <div class="max-w-2xl space-y-6">
    <h1 class="text-2xl font-bold tracking-tight">{{ $t("account.title") }}</h1>

    <!-- Account info -->
    <Card>
      <CardHeader><CardTitle>{{ $t("account.info") }}</CardTitle></CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <Label>{{ $t("account.fullName") }}</Label>
          <div class="flex gap-2">
            <Input v-model="fullName" class="flex-1" />
            <Button :disabled="saveName.isPending.value || !fullName" @click="saveName.mutate()">
              <Spinner v-if="saveName.isPending.value" /> {{ $t("common.save") }}
            </Button>
          </div>
          <p v-if="nameErr" class="text-sm text-destructive">{{ nameErr }}</p>
          <p v-if="nameOk" class="text-sm text-green-600">{{ $t("account.saved") }}</p>
        </div>
        <div class="space-y-2">
          <Label>{{ $t("auth.email") }}</Label>
          <Input :model-value="auth.user?.email" disabled />
        </div>
        <div class="flex flex-wrap gap-6 pt-1 text-sm">
          <div>
            <p class="text-xs text-muted-foreground">{{ $t("account.role") }}</p>
            <Badge variant="secondary">{{ auth.user?.role }}</Badge>
          </div>
          <div v-if="org">
            <p class="text-xs text-muted-foreground">{{ $t("account.organization") }}</p>
            <p class="font-medium">{{ org.name }} <Badge :variant="org.status === 'active' ? 'success' : 'warning'">{{ org.status }}</Badge></p>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Change password -->
    <Card>
      <CardHeader><CardTitle>{{ $t("account.changePassword") }}</CardTitle></CardHeader>
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
