<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"

import { apiError } from "@/api/client"
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, Spinner } from "@/components/ui"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()
const email = ref("")
const password = ref("")
const error = ref("")
const loading = ref(false)

async function submit() {
  error.value = ""
  loading.value = true
  try {
    const user = await auth.login(email.value, password.value)
    router.push({ name: user.role === "superadmin" ? "admin-platform" : "dashboard" })
  } catch (e) {
    error.value = apiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen grid place-items-center bg-muted/40 p-4">
    <Card class="w-full max-w-sm">
      <CardHeader>
        <CardTitle class="text-2xl">{{ $t("auth.welcomeBack") }}</CardTitle>
        <CardDescription>{{ $t("auth.signInSubtitle") }}</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="submit">
          <div class="space-y-2">
            <Label for="email">{{ $t("auth.email") }}</Label>
            <Input id="email" v-model="email" type="email" placeholder="you@company.com" />
          </div>
          <div class="space-y-2">
            <Label for="password">{{ $t("auth.password") }}</Label>
            <Input id="password" v-model="password" type="password" placeholder="••••••••" />
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" class="w-full" :disabled="loading">
            <Spinner v-if="loading" /> {{ $t("auth.signIn") }}
          </Button>
        </form>
        <p class="mt-4 text-center text-sm text-muted-foreground">
          {{ $t("auth.noAccount") }}
          <RouterLink to="/register" class="text-primary underline-offset-4 hover:underline">{{ $t("auth.registerOrg") }}</RouterLink>
        </p>
      </CardContent>
    </Card>
  </div>
</template>
