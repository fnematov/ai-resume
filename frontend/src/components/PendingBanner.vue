<script setup lang="ts">
import { useOrg } from "@/composables/useOrg"

const { isPending } = useOrg()
</script>

<template>
  <div
    v-if="isPending"
    class="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900"
  >
    {{ $t("common.pendingBanner") }}
  </div>
</template>
