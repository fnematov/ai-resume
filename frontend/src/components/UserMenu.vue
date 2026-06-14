<script setup lang="ts">
import { ChevronDown, LogOut, UserCircle } from "lucide-vue-next"
import { onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()
const open = ref(false)
const root = ref<HTMLElement | null>(null)

function goProfile() {
  open.value = false
  router.push({ name: "profile" })
}
function logout() {
  open.value = false
  auth.logout()
  router.push({ name: "login" })
}
function onClickOutside(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false
}
onMounted(() => document.addEventListener("click", onClickOutside))
onBeforeUnmount(() => document.removeEventListener("click", onClickOutside))
</script>

<template>
  <div ref="root" class="relative">
    <button
      class="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-accent"
      @click="open = !open"
    >
      <span class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
        {{ (auth.user?.full_name || auth.user?.email || "?").charAt(0).toUpperCase() }}
      </span>
      <span class="hidden text-right leading-tight sm:block">
        <span class="block max-w-[12rem] truncate text-sm font-medium">{{ auth.user?.full_name }}</span>
        <span class="block max-w-[12rem] truncate text-xs text-muted-foreground">{{ auth.user?.email }}</span>
      </span>
      <ChevronDown class="h-3.5 w-3.5 text-muted-foreground" />
    </button>
    <div
      v-if="open"
      class="absolute right-0 z-50 mt-1 w-48 overflow-hidden rounded-md border bg-popover py-1 shadow-md"
    >
      <div class="border-b px-3 py-2 sm:hidden">
        <p class="truncate text-sm font-medium">{{ auth.user?.full_name }}</p>
        <p class="truncate text-xs text-muted-foreground">{{ auth.user?.email }}</p>
      </div>
      <button class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent" @click="goProfile">
        <UserCircle class="h-4 w-4 text-muted-foreground" /> {{ $t("nav.profile") }}
      </button>
      <button class="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent" @click="logout">
        <LogOut class="h-4 w-4 text-muted-foreground" /> {{ $t("common.signOut") }}
      </button>
    </div>
  </div>
</template>
