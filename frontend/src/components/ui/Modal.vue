<script setup lang="ts">
import { X } from "lucide-vue-next"

defineProps<{ open: boolean; title?: string; subtitle?: string }>()
defineEmits<{ (e: "close"): void }>()
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition" enter-from-class="opacity-0"
      leave-active-class="transition" leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-black/40 p-4"
        @click.self="$emit('close')"
      >
        <div class="w-full max-w-lg rounded-xl border bg-card shadow-lg">
          <div class="flex items-start justify-between border-b p-4">
            <div>
              <h3 class="font-semibold">{{ title }}</h3>
              <p v-if="subtitle" class="text-sm text-muted-foreground">{{ subtitle }}</p>
            </div>
            <button class="text-muted-foreground hover:text-foreground" @click="$emit('close')">
              <X class="h-5 w-5" />
            </button>
          </div>
          <div class="p-4"><slot /></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
