<script setup lang="ts">
import {
  Building2,
  Briefcase,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  Settings,
  ShieldCheck,
  UserCircle,
  Zap,
} from "lucide-vue-next"
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { RouterView, useRouter } from "vue-router"

import { LOCALES, setLocale } from "@/i18n"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()
const { locale } = useI18n()

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

function logout() {
  auth.logout()
  router.push({ name: "login" })
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-muted/30">
    <aside class="flex w-60 shrink-0 flex-col border-r bg-card">
      <div class="flex h-14 shrink-0 items-center gap-2 border-b px-5">
        <div class="h-7 w-7 rounded-md bg-primary text-primary-foreground grid place-items-center text-sm font-bold">AR</div>
        <span class="font-semibold">AI Resume</span>
      </div>
      <nav class="flex-1 overflow-y-auto p-3 space-y-1">
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
      <div class="shrink-0 border-t p-3">
        <!-- Language switcher -->
        <div class="mb-2 flex gap-1 px-1">
          <button
            v-for="l in LOCALES"
            :key="l.code"
            class="flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors"
            :class="locale === l.code ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent/50'"
            @click="setLocale(l.code)"
          >
            {{ l.label }}
          </button>
        </div>
        <RouterLink
          :to="{ name: 'profile' }"
          class="mb-1 block rounded-md px-3 py-2 hover:bg-accent"
          active-class="bg-accent"
        >
          <p class="truncate text-sm font-medium">{{ auth.user?.full_name }}</p>
          <p class="truncate text-xs text-muted-foreground">{{ auth.user?.email }}</p>
        </RouterLink>
        <button
          class="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          @click="logout"
        >
          <LogOut class="h-4 w-4" /> {{ $t("common.signOut") }}
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
