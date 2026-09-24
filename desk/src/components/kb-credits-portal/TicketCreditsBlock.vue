<template>
  <!-- F2 on the customer ticket page. Renders nothing at all when the ticket
       has no customer, the customer has no credit account, or kb_credits is
       not reachable: a missing block is a normal state, not an error. -->
  <div
    v-if="visible"
    class="flex flex-col gap-3 px-5 py-3 border-b shrink-0 max-h-[55vh] overflow-y-auto"
  >
    <div class="flex items-center justify-between gap-2">
      <span class="text-base font-semibold text-ink-gray-8">
        {{ __("Intervention credits") }}
      </span>
      <router-link
        :to="{ name: 'CustomerCredits' }"
        class="text-p-sm text-ink-gray-5 hover:text-ink-gray-8 hover:underline"
      >
        {{ __("My credits") }}
      </router-link>
    </div>

    <!-- balance in one line; the full gauge lives on the "My credits" page -->
    <div
      v-if="data?.summary?.has_account"
      class="flex items-center justify-between text-p-sm"
    >
      <span class="text-ink-gray-5">{{ __("Current balance") }}</span>
      <span
        class="font-semibold tabular-nums"
        :class="(data.summary.balance ?? 0) < 0 ? 'text-ink-red-4' : 'text-ink-gray-9'"
      >
        {{ __("{0} / {1} credits", formatCredits(data.summary.balance), formatCredits(data.summary.consumption_base ?? data.summary.allocated)) }}
      </span>
    </div>

    <!-- art. 5.7 : le SLA appliqué à CE ticket (KB L-DEG / KB XL-DEG) fait foi -->
    <SlaDegradedBadge
      v-if="data?.summary?.has_account"
      :summary="degradation"
      compact
    />

    <p
      v-if="data?.legal_p1"
      class="flex items-start gap-1.5 rounded bg-surface-red-1 px-2 py-1.5 text-p-sm text-ink-red-4"
    >
      <LucideGavel class="size-3.5 shrink-0 mt-0.5" />
      <span>
        {{ __("Critical priority (P1) granted automatically: payroll or legal declaration blocked before a deadline.") }}
        <template v-if="data.legal_deadline">
          {{ __("Deadline: {0}", formatDate(data.legal_deadline)) }}
        </template>
      </span>
    </p>

    <p
      v-if="data?.on_quote"
      class="rounded bg-surface-gray-2 px-2 py-1.5 text-p-sm text-ink-gray-7"
    >
      {{ __("This request is handled on a separate quote: no credit is consumed.") }}
    </p>

    <QualificationList
      v-if="data?.qualifications.length"
      :items="data.qualifications"
      :readonly="data.can_qualify"
      @changed="reload"
    />
    <p v-else class="text-p-sm text-ink-gray-5">
      {{ __("This ticket has not been qualified yet. The weight will be announced to you before any intervention.") }}
    </p>

    <div
      v-if="data?.settled_total"
      class="flex items-center justify-between text-p-sm"
    >
      <span class="text-ink-gray-5">{{ __("Credits counted on this ticket") }}</span>
      <span class="font-semibold tabular-nums text-ink-gray-9">
        {{ formatCredits(data.settled_total) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import { computed, ref, watch } from "vue";
import LucideGavel from "~icons/lucide/gavel";
import QualificationList from "./QualificationList.vue";
import SlaDegradedBadge from "./SlaDegradedBadge.vue";
import type { PortalTicketCredits } from "./types";
import { formatCredits, formatDate } from "./utils";

const props = defineProps<{
  ticket: string | undefined;
  customer: string | null | undefined;
  /** SLA Helpdesk du ticket (ex. « KB XL-DEG ») */
  sla?: string | null;
}>();

const failed = ref(false);

const resource = createResource({
  url: "kb_credits.api.get_ticket_credits",
  makeParams: () => ({ ticket: props.ticket }),
  auto: false,
  onError() {
    // any failure (app absent, no customer, permission) hides the block
    failed.value = true;
  },
});

const data = computed(() => resource.data as PortalTicketCredits | undefined);

const degradation = computed(() => ({
  ...(data.value?.summary || {}),
  // le nom du SLA du ticket ne sert que s'il dit « dégradé » : un SLA
  // nominal sur un vieux ticket ne prouve rien sur l'état actuel du compte
  ...(props.sla && /-DEG$/i.test(props.sla.trim()) ? { sla: props.sla } : {}),
}));

const visible = computed(() => {
  if (failed.value || !props.customer || !data.value) return false;
  return Boolean(data.value.summary?.has_account || data.value.qualifications?.length);
});

function reload() {
  if (!props.ticket || !props.customer) return;
  failed.value = false;
  // onError already hid the block; swallow the re-thrown rejection
  Promise.resolve(resource.fetch()).catch(() => {});
}

watch(
  () => [props.ticket, props.customer],
  () => reload(),
  { immediate: true }
);
</script>
