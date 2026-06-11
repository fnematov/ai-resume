<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"

import { orgApi } from "@/api/endpoints"
import type { OrgStatus } from "@/api/types"
import { Badge, Button, Card, CardContent, Spinner } from "@/components/ui"

const qc = useQueryClient()
const { data, isLoading } = useQuery({ queryKey: ["admin-orgs"], queryFn: () => orgApi.list() })

const setStatus = useMutation({
  mutationFn: ({ id, status }: { id: number; status: OrgStatus }) => orgApi.setStatus(id, status),
  onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-orgs"] }),
})

const variant: Record<OrgStatus, "success" | "warning" | "destructive"> = {
  active: "success",
  pending: "warning",
  suspended: "destructive",
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Organizations</h1>
      <p class="text-muted-foreground">Approve, suspend, or re-activate organizations.</p>
    </div>

    <div v-if="isLoading" class="grid place-items-center py-20"><Spinner class="h-6 w-6" /></div>
    <Card v-else>
      <CardContent class="p-0">
        <table class="w-full text-sm">
          <thead class="border-b text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-4 py-3 font-medium">Organization</th>
              <th class="px-4 py-3 font-medium">Status</th>
              <th class="px-4 py-3 font-medium">Setup</th>
              <th class="px-4 py-3 font-medium">Users</th>
              <th class="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in data" :key="o.id" class="border-b last:border-0">
              <td class="px-4 py-3">
                <p class="font-medium">{{ o.name }}</p>
                <p class="text-xs text-muted-foreground">{{ o.slug }}</p>
              </td>
              <td class="px-4 py-3"><Badge :variant="variant[o.status]">{{ o.status }}</Badge></td>
              <td class="px-4 py-3">
                <div class="flex gap-1">
                  <Badge :variant="o.telegram_configured ? 'success' : 'muted'">TG</Badge>
                  <Badge :variant="o.ai_configured ? 'success' : 'muted'">AI</Badge>
                </div>
              </td>
              <td class="px-4 py-3 text-muted-foreground">{{ o.user_count }}</td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-2">
                  <Button v-if="o.status !== 'active'" size="sm" :disabled="setStatus.isPending.value" @click="setStatus.mutate({ id: o.id, status: 'active' })">Approve</Button>
                  <Button v-if="o.status === 'active'" size="sm" variant="destructive" :disabled="setStatus.isPending.value" @click="setStatus.mutate({ id: o.id, status: 'suspended' })">Suspend</Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>
  </div>
</template>
