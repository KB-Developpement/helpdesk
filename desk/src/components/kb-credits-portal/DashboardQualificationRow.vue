<template>
  <!-- A qualification line on the agent dashboard: ticket, customer, code, weight. -->
  <div class="space-y-0.5">
    <div class="flex items-center justify-between gap-2">
      <router-link
        :to="{ name: 'TicketAgent', params: { ticketId: q.ticket } }"
        class="text-base font-medium text-ink-gray-9 hover:underline truncate"
      >
        #{{ q.ticket }}
        <span v-if="q.customer" class="font-normal text-ink-gray-6">— {{ q.customer }}</span>
      </router-link>
      <span class="shrink-0 text-p-sm tabular-nums text-ink-gray-8">
        <span class="font-semibold">{{ q.grid_code }}</span>
        · {{ weightLabel }}
      </span>
    </div>
    <p class="text-p-sm text-ink-gray-5">
      <slot name="meta" />
    </p>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { computed } from "vue";
import type { DashboardQualification } from "./types";
import { formatCredits } from "./utils";

const props = defineProps<{ q: DashboardQualification }>();

const weightLabel = computed(() => {
  const w = Number(props.q.announced_weight || 0);
  return w >= 2 ? __("{0} credits", formatCredits(w)) : __("{0} credit", formatCredits(w));
});
</script>
