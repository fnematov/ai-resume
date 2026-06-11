import { defineStore } from "pinia"
import { computed, ref } from "vue"

import { authApi } from "@/api/endpoints"
import { tokenStore } from "@/api/client"
import type { User } from "@/api/types"

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null)
  const ready = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const isSuperadmin = computed(() => user.value?.role === "superadmin")
  const isOrgUser = computed(
    () => user.value != null && user.value.role !== "superadmin" && user.value.org_id != null,
  )

  async function login(email: string, password: string) {
    const res = await authApi.login(email, password)
    tokenStore.set(res.access_token, res.refresh_token)
    user.value = res.user
    return res.user
  }

  async function fetchMe() {
    if (!tokenStore.access) {
      ready.value = true
      return
    }
    try {
      user.value = await authApi.me()
    } catch {
      tokenStore.clear()
      user.value = null
    } finally {
      ready.value = true
    }
  }

  function logout() {
    tokenStore.clear()
    user.value = null
  }

  return { user, ready, isAuthenticated, isSuperadmin, isOrgUser, login, fetchMe, logout }
})
