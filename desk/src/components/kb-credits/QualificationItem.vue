<template>
  <li class="py-3 first:pt-0 last:pb-0">
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0">
        <p class="text-ink-gray-9 text-sm font-medium truncate">
          {{ q.grid_label || q.grid_code }}
        </p>
        <p class="text-ink-gray-5 text-xs mt-0.5">
          {{ q.grid_code }}
          <template v-if="q.responsibility_layer">
            · {{ __("Layer") }} {{ shortLayer }}
          </template>
        </p>
      </div>

      <div class="text-right shrink-0">
        <p class="text-ink-gray-9 text-sm font-semibold tabular-nums">
          {{ weightLabel }}
        </p>
        <!-- after a downward requalification the announced weight stays the ceiling -->
        <p v-if="ceilingLabel" class="text-ink-gray-5 text-xs tabular-nums">
          {{ ceilingLabel }}
        </p>
        <Badge :theme="statusTheme" variant="subtle" size="sm" class="mt-1">
          {{ q.status }}
        </Badge>
      </div>
    </div>

    <!-- weight breakdown, only when a multiplier, layer or surcharge changed it.
         A layer factor of 0 (layer 2, KB's own customisations) is the case that
         most needs explaining: the line then weighs 0 credit. -->
    <p
      v-if="showBreakdown"
      class="text-ink-gray-5 text-xs mt-1.5 tabular-nums"
    >
      {{ formatCredits(q.base_weight) }}
      <template v-if="multiplierChangesWeight">
        × {{ formatCredits(q.multiplier) }}
        <template v-if="q.intervention_at">
          ({{ __("outside working hours, intervention on {0}", dayjs(q.intervention_at).format("DD/MM/YYYY HH:mm")) }})
        </template>
        <template v-else>({{ __("outside working hours") }})</template>
      </template>
      <template v-if="layerChangesWeight">
        × {{ formatCredits(q.layer_factor) }} ({{ __("Layer") }} {{ shortLayer }})
      </template>
      <template v-if="surchargeFactor">
        × {{ formatCredits(surchargeFactor) }} ({{ __("unfounded P1 surcharge") }})
      </template>
      = {{ formatCredits(breakdownResult) }}
      <template v-if="cappedByCeiling">
        — {{ __("capped at the announced weight: {0}", formatCredits(effectiveWeight)) }}
      </template>
    </p>

    <!-- flags that change how the line is read -->
    <div v-if="flags.length" class="flex flex-wrap gap-1 mt-1.5">
      <Badge
        v-for="f in flags"
        :key="f.label"
        :theme="f.theme"
        variant="outline"
        size="sm"
      >
        {{ f.label }}
      </Badge>
    </div>

    <p v-if="q.surcharge_note" class="text-ink-gray-6 text-xs mt-1.5 italic">
      {{ frenchifyText(q.surcharge_note) }}
    </p>

    <!-- a contest is the customer talking back: never hide it -->
    <div
      v-if="q.status === 'Contestée' && q.contest_reason"
      class="mt-2 rounded bg-surface-amber-1 px-2 py-1.5"
    >
      <p class="text-ink-amber-3 text-xs leading-snug">
        <span class="font-medium">{{ __("Contested") }}:</span>
        {{ q.contest_reason }}
      </p>
    </div>

    <p v-if="tacitLabel" class="text-ink-gray-5 text-xs mt-1.5">
      {{ tacitLabel }}
    </p>

    <div v-if="actions.length" class="flex flex-wrap gap-2 mt-2">
      <Button
        v-for="a in actions"
        :key="a.event"
        size="sm"
        variant="subtle"
        :theme="a.theme"
        :loading="busy === a.event"
        @click="emit(a.event as any, q)"
      >
        {{ a.label }}
      </Button>
    </div>
  </li>
</template>

<script setup lang="ts">
import { Badge, Button, dayjs } from "frappe-ui";
import { computed } from "vue";
import { frenchifyText } from "@/components/kb-credits-portal/format";
import { canSettle, formatCredits } from "./grid";
import type { Qualification } from "./types";

const props = defineProps<{
  q: Qualification;
  canQualify: boolean;
  isManager: boolean;
  busy?: string | null;
  /** RB-1: lines at or under this weight need no customer validation */
  validationThreshold?: number;
}>();

const emit = defineEmits<{
  settle: [q: Qualification];
  requalify: [q: Qualification];
  lowerCategory: [q: Qualification];
}>();

const isFinal = computed(() =>
  ["Décomptée", "Annulée"].includes(props.q.status)
);

// Once settled, the final weight is what hit the ledger; after a downward
// requalification of an announced line it is what will hit it (the server keeps
// announced_weight as the ceiling and writes the new weight to final_weight).
// Otherwise — including a line on quote — the announced weight.
// A layer contest (art. 4.2) also sets final_weight without downgraded_from:
// `has_final_weight` is the server's own marker that a final weight exists.
const hasFinalWeight = computed(() => {
  const q = props.q;
  if (q.status === "Sur devis") return false;
  return (
    q.status === "Décomptée" ||
    Boolean(Number(q.has_final_weight || 0)) ||
    (Boolean(q.downgraded_from) && Number(q.announced_weight || 0) > 0)
  );
});

const effectiveWeight = computed(() => {
  const q = props.q;
  if (hasFinalWeight.value) return Number(q.final_weight || 0);
  return Number(q.announced_weight || 0);
});

const weightLabel = computed(() => {
  const q = props.q;
  if (q.is_free) return __("Free");
  const w = effectiveWeight.value;
  // French grammar: 0 and 1 are singular (« 0 crédit »)
  return `${formatCredits(w)} ${Math.abs(w) <= 1 ? __("credit") : __("credits")}`;
});

const ceilingLabel = computed(() => {
  const q = props.q;
  if (q.is_free || !hasFinalWeight.value || q.status === "Décomptée") return "";
  if (Number(q.announced_weight || 0) === effectiveWeight.value) return "";
  return __("announced {0}").replace("{0}", formatCredits(q.announced_weight));
});

// `layer_factor && layer_factor !== 1` used to treat a factor of 0 as "no
// factor" and hid exactly the breakdown that explains a 0-credit line.
const layerChangesWeight = computed(() => {
  const f = props.q.layer_factor;
  return (
    Boolean(props.q.responsibility_layer) &&
    f !== undefined &&
    f !== null &&
    Number(f) !== 1
  );
});

const multiplierChangesWeight = computed(() => {
  const m = props.q.multiplier;
  return m !== undefined && m !== null && Number(m) !== 0 && Number(m) !== 1;
});

// art. 6.4 surcharge is applied at announcement; a requalification recomputes
// base × multiplier × layer without it (qualification.requalify)
const surchargeApplies = computed(
  () =>
    Boolean(props.q.unfounded_p1) && !props.q.is_free && !props.q.downgraded_from
);

// base × multiplier × layer, then the art. 6.4 surcharge when it explains the
// displayed weight: the equation always ends on what is (or will be) debited.
const baseProduct = computed(() => {
  const q = props.q;
  const mult = multiplierChangesWeight.value ? Number(q.multiplier) : 1;
  const layer = layerChangesWeight.value ? Number(q.layer_factor) : 1;
  return Number(q.base_weight || 0) * mult * layer;
});

const surchargeFactor = computed(() => {
  if (!surchargeApplies.value) return 0;
  const product = baseProduct.value;
  const w = effectiveWeight.value;
  return product > 0 && w > product + 0.005 ? Math.round((w / product) * 100) / 100 : 0;
});

const breakdownResult = computed(() => {
  const product = baseProduct.value * (surchargeFactor.value || 1);
  return Math.round(product * 100) / 100;
});

const cappedByCeiling = computed(
  () => Math.abs(breakdownResult.value - effectiveWeight.value) >= 0.005
);

const showBreakdown = computed(
  () =>
    !props.q.is_free &&
    props.q.status !== "Sur devis" &&
    (multiplierChangesWeight.value ||
      layerChangesWeight.value ||
      surchargeApplies.value)
);

const shortLayer = computed(
  () => (props.q.responsibility_layer || "").split("—")[0].trim()
);

const statusTheme = computed(() => {
  switch (props.q.status) {
    case "Validée":
    case "Acceptation tacite":
      return "green";
    case "Contestée":
      return "orange";
    case "Décomptée":
      return "blue";
    case "Sur devis":
      return "violet";
    case "Annulée":
      return "gray";
    case "Annoncée":
      return "blue";
    default:
      return "gray";
  }
});

const flags = computed(() => {
  const q = props.q;
  const out: { label: string; theme: string }[] = [];
  if (q.is_regularisation) out.push({ label: __("Regularisation"), theme: "gray" });
  if (q.unfounded_p1) out.push({ label: __("Unfounded P1"), theme: "red" });
  if (q.onsite) out.push({ label: __("On-site"), theme: "gray" });
  if (q.travel_fee) out.push({ label: __("Travel fee"), theme: "gray" });
  if (q.downgraded_from)
    out.push({ label: __("Downgraded from {0}").replace("{0}", q.downgraded_from), theme: "gray" });
  return out;
});

const tacitLabel = computed(() => {
  const q = props.q;
  if (q.status !== "Annoncée") return "";
  if (q.awaiting_notification)
    return __("Customer not notified yet: the 48 h tacit period has not started.");
  if (!q.tacit_deadline) return "";
  const d = dayjs(q.tacit_deadline);
  const verb = d.isBefore(dayjs()) ? __("tacitly accepted since {0}") : __("tacit acceptance on {0}");
  return verb.replace("{0}", d.format("DD/MM/YYYY"));
});

const actions = computed(() => {
  const out: { label: string; event: string; theme?: string }[] = [];
  if (isFinal.value || !props.canQualify) return out;
  // RB-1: an « Annoncée » line above the threshold is refused by the server —
  // offer the button only where settle() will actually accept it.
  if (canSettle(props.q, props.validationThreshold ?? 1))
    out.push({ label: __("Settle"), event: "settle" });
  out.push({ label: __("Requalify"), event: "requalify" });
  // RB-4: only the support manager may resolve doubt in the customer's favour
  if (props.isManager)
    out.push({ label: __("Lower category"), event: "lowerCategory" });
  return out;
});
</script>
