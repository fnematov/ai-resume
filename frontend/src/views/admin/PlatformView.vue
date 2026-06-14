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
      <p class="text-muted-foreground">{{ $t("admin.platformSubtitle") }}</p>
    </div>
    <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>
    <template v-else-if="data">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard :label="$t('admin.organizations')" :value="data.total_organizations" :icon="Building2" />
        <StatCard :label="$t('admin.pendingApproval')" :value="data.pending_organizations" :icon="Clock" />
        <StatCard :label="$t('admin.users')" :value="data.total_users" :icon="Users" />
        <StatCard :label="$t('admin.applications')" :value="data.total_applications" :icon="FileText" :hint="$t('admin.vacancies', { n: data.total_vacancies })" />
      </div>
      <RouterLink to="/admin/organizations" class="inline-block text-sm text-primary hover:underline">
        {{ $t("admin.reviewOrgs") }}
      </RouterLink>
    </template>
  </div>
</template>
