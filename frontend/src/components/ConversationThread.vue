<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query"
import { Lock, LockOpen, Send } from "lucide-vue-next"
import { ref } from "vue"

import { applicationApi } from "@/api/endpoints"
import { Badge, Button, Spinner, Textarea } from "@/components/ui"
import { formatDate } from "@/lib/utils"

const props = defineProps<{ applicationId: number; chatOpen: boolean }>()
const qc = useQueryClient()
const draft = ref("")

const { data: messages, isLoading } = useQuery({
  queryKey: ["app-messages", props.applicationId],
  queryFn: () => applicationApi.messages(props.applicationId),
  refetchInterval: 8000,
})

const invalidate = () => {
  qc.invalidateQueries({ queryKey: ["app-messages", props.applicationId] })
  qc.invalidateQueries({ queryKey: ["application", props.applicationId] })
}

const send = useMutation({
  mutationFn: () => applicationApi.sendMessage(props.applicationId, draft.value),
  onSuccess: () => {
    draft.value = ""
    invalidate()
  },
})

const toggleChat = useMutation({
  mutationFn: () => applicationApi.setChatOpen(props.applicationId, !props.chatOpen),
  onSuccess: invalidate,
})
</script>

<template>
  <div class="flex h-[420px] flex-col">
    <!-- Chat lock status -->
    <div class="mb-2 flex items-center justify-between border-b pb-2">
      <Badge :variant="chatOpen ? 'success' : 'muted'">
        <component :is="chatOpen ? LockOpen : Lock" class="mr-1 h-3 w-3" />
        {{ chatOpen ? $t("application.chatOpen") : $t("application.chatClosed") }}
      </Badge>
      <Button variant="outline" size="sm" :disabled="toggleChat.isPending.value" @click="toggleChat.mutate()">
        <Spinner v-if="toggleChat.isPending.value" />
        {{ chatOpen ? $t("application.closeChat") : $t("application.openChat") }}
      </Button>
    </div>

    <div class="flex-1 space-y-3 overflow-y-auto p-1">
      <div v-if="isLoading" class="grid place-items-center py-8"><Spinner /></div>
      <p v-else-if="!messages?.length" class="py-8 text-center text-sm text-muted-foreground">
        {{ $t("application.noMessages") }}
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

    <p v-if="!chatOpen" class="mt-2 text-xs text-muted-foreground">{{ $t("application.chatLockedHint") }}</p>
    <form class="mt-2 flex items-end gap-2 border-t pt-2" @submit.prevent="send.mutate()">
      <Textarea v-model="draft" :rows="2" :placeholder="$t('application.writeMessage')" class="flex-1" />
      <Button type="submit" size="icon" :disabled="!draft || send.isPending.value">
        <Spinner v-if="send.isPending.value" /><Send v-else class="h-4 w-4" />
      </Button>
    </form>
  </div>
</template>
