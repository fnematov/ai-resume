import { useQuery } from "@tanstack/vue-query"
import { computed } from "vue"

import { orgApi } from "@/api/endpoints"
import { useAuthStore } from "@/stores/auth"

/**
 * Shared organization state. `organizations/me` is readable even for a pending org,
 * so the panel can show the awaiting-approval banner and gate actions/data behind
 * `isActive`.
 */
export function useOrg() {
  const auth = useAuthStore()
  const query = useQuery({
    queryKey: ["org"],
    queryFn: orgApi.me,
    enabled: computed(() => auth.isOrgUser),
  })
  const org = query.data
  const isActive = computed(() => org.value?.status === "active")
  const isPending = computed(() => !!org.value && org.value.status !== "active")
  return { org, isActive, isPending, query }
}
