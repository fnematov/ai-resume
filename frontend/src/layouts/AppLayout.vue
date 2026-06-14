<script setup lang="ts">
import {
  Building2,
  Briefcase,
  LayoutDashboard,
  MessageSquareText,
  Settings,
  ShieldCheck,
  UserCircle,
  Zap,
} from "lucide-vue-next"
import { computed } from "vue"
import { RouterView, useRoute } from "vue-router"

import LanguageSelector from "@/components/LanguageSelector.vue"
import ThemeSelector from "@/components/ThemeSelector.vue"
import UserMenu from "@/components/UserMenu.vue"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const route = useRoute()

const orgNav = [
  { name: "dashboard", label: "nav.dashboard", icon: LayoutDashboard },
  { name: "vacancies", label: "nav.vacancies", icon: Briefcase },
  { name: "templates", label: "nav.templates", icon: MessageSquareText },
  { name: "automation", label: "nav.automation", icon: Zap },
  { name: "settings", label: "nav.settings", icon: Settings },
  { name: "profile", label: "nav.profile", icon: UserCircle },
]
const adminNav = [
  { name: "admin-platform", label: "nav.platform", icon: ShieldCheck },
  { name: "admin-orgs", label: "nav.organizations", icon: Building2 },
  { name: "profile", label: "nav.profile", icon: UserCircle },
]
const nav = computed(() => (auth.isSuperadmin ? adminNav : orgNav))

// Map every route to the i18n key shown in the top header. Detail pages fall
// back to their parent section so the header always names the current area.
const TITLE_KEYS: Record<string, string> = {
  dashboard: "nav.dashboard",
  vacancies: "nav.vacancies",
  vacancy: "nav.vacancies",
  pipeline: "nav.vacancies",
  application: "nav.vacancies",
  templates: "nav.templates",
  automation: "nav.automation",
  settings: "nav.settings",
  profile: "nav.profile",
  "admin-platform": "nav.platform",
  "admin-orgs": "nav.organizations",
}
const titleKey = computed(() => TITLE_KEYS[String(route.name)] ?? "")
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-muted/30">
    <aside class="flex w-60 shrink-0 flex-col border-r bg-card">
      <div class="flex h-14 shrink-0 items-center gap-2 border-b px-5">
        <div class="grid h-7 w-7 place-items-center rounded-md bg-primary text-sm font-bold text-primary-foreground">AR</div>
        <span class="font-semibold">AI Resume</span>
      </div>
      <nav class="flex-1 space-y-1 overflow-y-auto p-3">
        <RouterLink
          v-for="item in nav"
          :key="item.name"
          :to="{ name: item.name }"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          active-class="bg-accent text-accent-foreground"
        >
          <component :is="item.icon" class="h-4 w-4" />
          {{ $t(item.label) }}
        </RouterLink>
      </nav>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <!-- Top header -->
      <header class="flex h-14 shrink-0 items-center justify-between gap-4 border-b bg-card px-6">
        <h1 class="truncate text-lg font-semibold">{{ titleKey ? $t(titleKey) : "" }}</h1>
        <div class="flex items-center gap-2">
          <ThemeSelector />
          <LanguageSelector />
          <UserMenu />
        </div>
      </header>

      <main class="flex-1 overflow-auto">
        <div class="mx-auto max-w-6xl p-8">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>
