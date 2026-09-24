<template>
  <!-- F3: the customer's ledger, newest first. The ledger is the only source
       of truth, so every row is shown as posted, zero-credit ones included
       (they are the trace of what was offered: D0, E0). -->
  <div class="space-y-3">
    <div v-if="rows.length" class="overflow-x-auto rounded-lg border border-outline-gray-2">
      <table class="w-full min-w-[720px] text-base">
        <thead class="bg-surface-gray-1 text-left text-p-sm text-ink-gray-5">
          <tr>
            <th class="px-3 py-2 font-medium">{{ __("Date") }}</th>
            <th class="px-3 py-2 font-medium">{{ __("Movement") }}</th>
            <th class="px-3 py-2 font-medium">{{ __("Ticket") }}</th>
            <th class="px-3 py-2 font-medium">{{ __("Code") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Credits") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Balance after") }}</th>
            <th class="px-3 py-2 font-medium">{{ __("Detail") }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1">
          <tr v-for="m in rows" :key="m.name" class="align-top">
            <td class="px-3 py-2 whitespace-nowrap text-ink-gray-7 tabular-nums">
              {{ formatDateTime(m.posting_datetime) }}
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-ink-gray-8">
              {{ m.entry_type }}
            </td>
            <td class="px-3 py-2 whitespace-nowrap">
              <router-link
                v-if="m.ticket"
                :to="ticketRoute(m.ticket)"
                class="text-ink-gray-8 hover:underline"
              >
                #{{ m.ticket }}
              </router-link>
              <span v-else class="text-ink-gray-4">—</span>
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-ink-gray-7">
              {{ m.grid_code || "—" }}
            </td>
            <td
              class="px-3 py-2 whitespace-nowrap text-right font-semibold tabular-nums"
              :class="movementTheme(Number(m.credits))"
            >
              <template v-if="Number(m.credits) === 0">{{ __("Offered") }}</template>
              <template v-else>{{ formatSignedCredits(m.credits) }}</template>
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-right tabular-nums text-ink-gray-7">
              {{ formatCredits(m.balance_after) }}
            </td>
            <td class="px-3 py-2 text-p-sm text-ink-gray-6 max-w-[280px]">
              <span v-if="m.reason">{{ frenchifyText(m.reason) }}</span>
              <span v-if="m.expires_on" class="block text-ink-gray-5">
                {{ __("Valid until {0}", formatDate(m.expires_on)) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else-if="!loading" class="text-p-sm text-ink-gray-5">
      {{ __("No movement yet.") }}
    </p>

    <ErrorMessage :message="error" />

    <div v-if="hasMore || loading" class="flex justify-center">
      <Button
        :label="__('Show more')"
        :loading="loading"
        :disabled="!hasMore"
        @click="more"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, call, ErrorMessage } from "frappe-ui";
import { onMounted, ref } from "vue";
import type { Movement } from "./types";
import {
  errorText,
  formatCredits,
  formatDate,
  formatDateTime,
  formatSignedCredits,
  frenchifyText,
  movementTheme,
} from "./utils";

const props = withDefaults(
  defineProps<{ customer?: string | null; pageSize?: number; agentView?: boolean }>(),
  { customer: null, pageSize: 25, agentView: false }
);

const rows = ref<Movement[]>([]);
const limit = ref(props.pageSize);
const loading = ref(false);
const hasMore = ref(false);
const error = ref("");

// get_movements only takes a limit: page by growing it
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const data: Movement[] =
      (await call("kb_credits.api.get_movements", {
        customer: props.customer || undefined,
        limit: limit.value,
      })) || [];
    rows.value = data;
    hasMore.value = data.length >= limit.value;
  } catch (e) {
    error.value = errorText(e);
  } finally {
    loading.value = false;
  }
}

function more() {
  limit.value += props.pageSize;
  load();
}

function ticketRoute(ticket: string) {
  return props.agentView
    ? { name: "TicketAgent", params: { ticketId: ticket } }
    : { name: "TicketCustomer", params: { ticketId: ticket } };
}

onMounted(load);
defineExpose({ reload: load });
</script>
