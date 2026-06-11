<script setup lang="ts">
import type { Component } from "vue"
import { Card, CardContent } from "@/components/ui"

defineProps<{ label: string; value: string | number; icon?: Component; hint?: string }>()
</script>

<template>
  <Card>
    <CardContent class="p-5">
      <div class="flex items-center justify-between">
        <p class="text-sm font-medium text-muted-foreground">{{ label }}</p>
        <component :is="icon" v-if="icon" class="h-4 w-4 text-muted-foreground" />
      </div>
      <p class="mt-2 text-3xl font-bold tracking-tight">{{ value }}</p>
      <p v-if="hint" class="mt-1 text-xs text-muted-foreground">{{ hint }}</p>
    </CardContent>
  </Card>
</template>
