<template>
  <li
    class="rounded-lg border px-3 py-3 space-y-2"
    :class="
      canValidate(q)
        ? 'border-outline-amber-1 bg-surface-amber-1'
        : 'border-outline-gray-2 bg-surface-white'
    "
  >
    <!-- ticket reference (only on the "My credits" page) -->
    <router-link
      v-if="q.ticket && showTicket"
      :to="{ name: 'TicketCustomer', params: { ticketId: q.ticket } }"
      class="flex items-center gap-1 text-p-sm text-ink-gray-6 hover:text-ink-gray-9 hover:underline"
    >
      <LucideTicket class="size-3.5 shrink-0" />
      <span class="truncate">
        {{ __("Ticket #{0}", q.ticket) }}
        <template v-if="q.ticket_subject"> — {{ q.ticket_subject }}</template>
      </span>
    </router-link>

    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-base font-medium text-ink-gray-9">
          <span class="font-semibold">{{ q.grid_code }}</span>
          <template v-if="q.grid_label"> — {{ q.grid_label }}</template>
        </p>
        <p v-if="q.responsibility_layer" class="text-p-sm text-ink-gray-5 mt-0.5">
          {{ __("Responsibility layer: {0}", q.responsibility_layer) }}
        </p>
      </div>
      <div class="text-right shrink-0 space-y-1">
        <p class="text-base font-semibold tabular-nums text-ink-gray-9">
          <template v-if="q.is_free">{{ __("Free") }}</template>
          <template v-else>{{ creditLabel(displayedWeight(q)) }}</template>
        </p>
        <Badge :theme="qualificationTheme(q.status)" variant="subtle" size="sm">
          {{ q.status }}
        </Badge>
      </div>
    </div>

    <!-- how the weight was built, only when something changed it -->
    <p v-if="breakdown" class="text-p-sm text-ink-gray-6 tabular-nums">
      {{ breakdown }}
    </p>

    <p
      v-if="q.announced_balance !== null && q.announced_balance !== undefined && q.status === 'Annoncée'"
      class="text-p-sm text-ink-gray-6"
    >
      {{ __("Projected balance at announcement: {0}", formatCredits(projectedBalance)) }}
    </p>

    <p v-if="q.onsite && q.travel_fee" class="text-p-sm text-ink-gray-6">
      {{ __("On-site intervention — travel fee: {0} (not in credits)", formatDA(q.travel_fee)) }}
    </p>

    <p v-if="q.surcharge_note" class="text-p-sm text-ink-gray-6 italic">
      {{ frenchifyText(q.surcharge_note) }}
    </p>

    <p v-if="q.downgraded_from" class="text-p-sm text-ink-green-3">
      {{ __("Requalified downwards from {0}", q.downgraded_from) }}
      <template v-if="q.resolution_note"> — {{ frenchifyText(q.resolution_note) }}</template>
    </p>

    <!-- tacit acceptance: the 48 working hours only run once notified -->
    <p v-if="q.status === 'Annoncée'" class="flex items-start gap-1.5 text-p-sm text-ink-amber-3">
      <LucideHourglass class="size-3.5 shrink-0 mt-0.5" />
      <span v-if="q.tacit_deadline">
        {{ __("Without a reply from you, this weight is deemed accepted on {0}.", formatDateTime(q.tacit_deadline)) }}
      </span>
      <span v-else>
        {{ __("Without a reply from you, this weight is deemed accepted 48 working hours after you were notified.") }}
      </span>
    </p>

    <p v-if="q.status === 'Contestée' && q.contest_reason" class="rounded bg-surface-red-1 px-2 py-1.5 text-p-sm text-ink-red-4">
      {{ __("Your contest: {0}", q.contest_reason) }}
    </p>

    <p v-if="q.status === 'Sur devis'" class="text-p-sm text-ink-gray-6">
      {{ __("Estimated above 10 credits: this request is handled on a separate quote. No credit is consumed.") }}
    </p>

    <p
      v-if="canContestLayer(q) && q.layer_contest_deadline"
      class="text-p-sm text-ink-gray-5"
    >
      {{ __("Layer can be contested until {0}", formatDateTime(q.layer_contest_deadline)) }}
    </p>

    <div v-if="hasActions" class="flex flex-wrap gap-2 pt-1">
      <Button
        v-if="canValidate(q)"
        size="sm"
        variant="solid"
        theme="green"
        :label="__('Validate')"
        :loading="busy === 'validate'"
        :disabled="Boolean(busy)"
        @click="emit('validate', q)"
      >
        <template #prefix><LucideCheck class="size-3.5" /></template>
      </Button>
      <Button
        v-if="canContestWeight(q)"
        size="sm"
        variant="subtle"
        theme="red"
        :label="__('Contest')"
        :disabled="Boolean(busy)"
        @click="emit('contest', q)"
      />
      <Button
        v-if="canContestLayer(q)"
        size="sm"
        variant="ghost"
        :label="__('Contest the layer')"
        :disabled="Boolean(busy)"
        @click="emit('contestLayer', q)"
      >
        <template #prefix><LucideLayers class="size-3.5" /></template>
      </Button>
    </div>
  </li>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Badge, Button } from "frappe-ui";
import { computed } from "vue";
import LucideCheck from "~icons/lucide/check";
import LucideHourglass from "~icons/lucide/hourglass";
import LucideLayers from "~icons/lucide/layers";
import LucideTicket from "~icons/lucide/ticket";
import type { PortalQualification } from "./types";
import {
  canContestLayer,
  canContestWeight,
  canValidate,
  displayedWeight,
  formatCredits,
  formatDA,
  formatDateTime,
  frenchifyText,
  qualificationTheme,
  weightBreakdown,
} from "./utils";

const props = withDefaults(
  defineProps<{
    q: PortalQualification;
    busy?: string | null;
    showTicket?: boolean;
    readonly?: boolean;
  }>(),
  { busy: null, showTicket: false, readonly: false }
);

const emit = defineEmits<{
  validate: [q: PortalQualification];
  contest: [q: PortalQualification];
  contestLayer: [q: PortalQualification];
}>();

const hasActions = computed(
  () =>
    !props.readonly &&
    (canValidate(props.q) || canContestWeight(props.q) || canContestLayer(props.q))
);

function creditLabel(n: number): string {
  return n >= 2
    ? __("{0} credits", formatCredits(n))
    : __("{0} credit", formatCredits(n));
}

const breakdown = computed(() => weightBreakdown(props.q));

// Solde projeté : calculé à l'annonce ; si un poids final plus bas est arrêté
// depuis (couche contestée, requalification), la différence revient au client.
const projectedBalance = computed(() => {
  const q = props.q;
  const announced = Number(q.announced_weight || 0);
  return Number(q.announced_balance || 0) + (announced - displayedWeight(q));
});
</script>
