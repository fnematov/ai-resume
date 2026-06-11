<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Send } from "lucide-vue-next"
import { ref } from "vue"

import { applicationApi } from "@/api/endpoints"
import { Button, Spinner, Textarea } from "@/components/ui"
import { formatDate } from "@/lib/utils"

const props = defineProps<{ applicationId: number }>()
const qc = useQueryClient()
const draft = ref("")

const { data: messages, isLoading } = useQuery({
  queryKey: ["app-messages", props.applicationId],
  queryFn: () => applicationApi.messages(props.applicationId),
  refetchInterval: 8000,
})

const send = useMutation({
  mutationFn: () => applicationApi.sendMessage(props.applicationId, draft.value),
  onSuccess: () => {
    draft.value = ""
    qc.invalidateQueries({ queryKey: ["app-messages", props.applicationId] })
  },
})
</script>

<template>
  <div class="flex h-[420px] flex-col">
    <div class="flex-1 space-y-3 overflow-y-auto p-1">
      <div v-if="isLoading" class="grid place-items-center py-8"><Spinner /></div>
      <p v-else-if="!messages?.length" class="py-8 text-center text-sm text-muted-foreground">
        No messages yet. Use the actions above or send a note below.
      </p>
      <div
        v-for="m in messages"
        :key="m.id"
        class="flex"
        :class="m.direction === 'outbound' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[80%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap"
          :class="m.direction === 'outbound' ? 'bg-primary text-primary-foreground' : 'bg-muted'"
        >
          {{ m.body }}
          <div class="mt-1 text-[10px] opacity-70">
            {{ formatDate(m.created_at) }}
            <span v-if="m.status === 'failed'" class="text-red-300"> · failed</span>
          </div>
        </div>
      </div>
    </div>
    <form class="mt-2 flex items-end gap-2 border-t pt-2" @submit.prevent="send.mutate()">
      <Textarea v-model="draft" :rows="2" placeholder="Write a message…" class="flex-1" />
      <Button type="submit" size="icon" :disabled="!draft || send.isPending.value">
        <Spinner v-if="send.isPending.value" /><Send v-else class="h-4 w-4" />
      </Button>
    </form>
  </div>
</template>
