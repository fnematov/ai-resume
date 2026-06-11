<script setup lang="ts">
import { cn } from "@/lib/utils"

defineProps<{ modelValue?: string; placeholder?: string; rows?: number; disabled?: boolean; class?: string }>()
defineEmits<{ (e: "update:modelValue", value: string): void }>()
</script>

<template>
  <textarea
    :value="modelValue"
    :placeholder="placeholder"
    :rows="rows || 4"
    :disabled="disabled"
    :class="cn('flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50', $props.class)"
    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
  />
</template>
