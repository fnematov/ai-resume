<script setup lang="ts">
import {
  Building2,
  Briefcase,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  Settings,
  ShieldCheck,
  Zap,
} from "lucide-vue-next"
import { computed } from "vue"
import { RouterView, useRouter } from "vue-router"

import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()

const orgNav = [
  { name: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { name: "vacancies", label: "Vacancies", icon: Briefcase },
  { name: "templates", label: "Templates", icon: MessageSquareText },
  { name: "automation", label: "Automation", icon: Zap },
  { name: "settings", label: "Settings", icon: Settings },
]
const adminNav = [
  { name: "admin-platform", label: "Platform", icon: ShieldCheck },
  { name: "admin-orgs", label: "Organizations", icon: Building2 },
]
const nav = computed(() => (auth.isSuperadmin ? adminNav : orgNav))

function logout() {
  auth.logout()
  router.push({ name: "login" })
}
</script>

<template>
  <div class="min-h-screen flex bg-muted/30">
    <aside class="w-60 shrink-0 border-r bg-card flex flex-col">
      <div class="h-14 flex items-center gap-2 px-5 border-b">
        <div class="h-7 w-7 rounded-md bg-primary text-primary-foreground grid place-items-center text-sm font-bold">AR</div>
        <span class="font-semibold">AI Resume</span>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <RouterLink
          v-for="item in nav"
          :key="item.name"
          :to="{ name: item.name }"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          active-class="bg-accent text-accent-foreground"
        >
          <component :is="item.icon" class="h-4 w-4" />
          {{ item.label }}
        </RouterLink>
      </nav>
      <div class="p-3 border-t">
        <div class="px-3 py-2 mb-1">
          <p class="text-sm font-medium truncate">{{ auth.user?.full_name }}</p>
          <p class="text-xs text-muted-foreground truncate">{{ auth.user?.email }}</p>
        </div>
        <button
          class="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          @click="logout"
        >
          <LogOut class="h-4 w-4" /> Sign out
        </button>
      </div>
    </aside>

    <main class="flex-1 overflow-auto">
      <div class="mx-auto max-w-6xl p-8">
        <RouterView />
      </div>
    </main>
  </div>
</template>
