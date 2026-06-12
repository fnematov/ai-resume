<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"

import { apiError } from "@/api/client"
import { authApi } from "@/api/endpoints"
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, Spinner } from "@/components/ui"

const router = useRouter()
const form = ref({ organization_name: "", full_name: "", email: "", password: "" })
const error = ref("")
const loading = ref(false)
const done = ref(false)

async function submit() {
  error.value = ""
  loading.value = true
  try {
    await authApi.register(form.value)
    done.value = true
  } catch (e) {
    error.value = apiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen grid place-items-center bg-muted/40 p-4">
    <Card class="w-full max-w-md">
      <CardHeader>
        <CardTitle class="text-2xl">{{ $t("auth.registerTitle") }}</CardTitle>
        <CardDescription>{{ $t("auth.registerSubtitle") }}</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="done" class="space-y-4 text-center">
          <p class="text-sm">🎉 {{ $t("auth.pendingApproval") }}</p>
          <Button class="w-full" @click="router.push({ name: 'login' })">{{ $t("auth.goToSignIn") }}</Button>
        </div>
        <form v-else class="space-y-4" @submit.prevent="submit">
          <div class="space-y-2">
            <Label>{{ $t("auth.orgName") }}</Label>
            <Input v-model="form.organization_name" placeholder="Acme Corp" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("auth.yourName") }}</Label>
            <Input v-model="form.full_name" placeholder="Jane Boss" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("auth.email") }}</Label>
            <Input v-model="form.email" type="email" placeholder="you@company.com" />
          </div>
          <div class="space-y-2">
            <Label>{{ $t("auth.password") }}</Label>
            <Input v-model="form.password" type="password" placeholder="••••••••" />
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" class="w-full" :disabled="loading"><Spinner v-if="loading" /> {{ $t("auth.createAccount") }}</Button>
        </form>
        <p v-if="!done" class="mt-4 text-center text-sm text-muted-foreground">
          {{ $t("auth.haveAccount") }}
          <RouterLink to="/login" class="text-primary underline-offset-4 hover:underline">{{ $t("auth.signIn") }}</RouterLink>
        </p>
      </CardContent>
    </Card>
  </div>
</template>
