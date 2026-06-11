<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query"
import { Building2, Clock, FileText, Users } from "lucide-vue-next"

import { analyticsApi } from "@/api/endpoints"
import StatCard from "@/components/StatCard.vue"
import { Spinner } from "@/components/ui"

const { data, isLoading } = useQuery({ queryKey: ["platform"], queryFn: analyticsApi.platform })
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Platform overview</h1>
      <p class="text-muted-foreground">Super-admin analytics across all organizations.</p>
    </div>
    <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>
    <template v-else-if="data">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Organizations" :value="data.total_organizations" :icon="Building2" :hint="`${data.active_organizations} active`" />
        <StatCard label="Pending approval" :value="data.pending_organizations" :icon="Clock" />
        <StatCard label="Users" :value="data.total_users" :icon="Users" />
        <StatCard label="Applications" :value="data.total_applications" :icon="FileText" :hint="`${data.total_vacancies} vacancies`" />
      </div>
      <RouterLink to="/admin/organizations" class="inline-block text-sm text-primary hover:underline">
        Review organizations →
      </RouterLink>
    </template>
  </div>
</template>
