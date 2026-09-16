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
            <span v-if="q.layer_factor && q.layer_factor !== 1">
              (×{{ q.layer_factor }})
            </span>
          </template>
        </p>
      </div>

      <div class="text-right shrink-0">
        <p class="text-ink-gray-9 text-sm font-semibold tabular-nums">
          {{ weightLabel }}
        </p>
        <Badge :theme="statusTheme" variant="subtle" size="sm" class="mt-1">
          {{ q.status }}
        </Badge>
      </div>
    </div>

    <!-- weight breakdown, only when a multiplier or layer actually changed it -->
    <p
      v-if="showBreakdown"
      class="text-ink-gray-5 text-xs mt-1.5 tabular-nums"
    >
      {{ q.base_weight }}
      <template v-if="q.multiplier && q.multiplier !== 1">
        × {{ q.multiplier }} ({{ __("outside working hours") }})
      </template>
      <template v-if="q.layer_factor && q.layer_factor !== 1">
        × {{ q.layer_factor }}
      </template>
      = {{ q.announced_weight }}
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
      {{ q.surcharge_note }}
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
import type { Qualification } from "./types";

const props = defineProps<{
  q: Qualification;
  canQualify: boolean;
  isManager: boolean;
  busy?: string | null;
}>();

const emit = defineEmits<{
  settle: [q: Qualification];
  requalify: [q: Qualification];
  lowerCategory: [q: Qualification];
}>();

const isFinal = computed(() =>
  ["Décomptée", "Annulée"].includes(props.q.status)
);

const weightLabel = computed(() => {
  const q = props.q;
  if (q.is_free) return __("Free");
  // once settled, the final weight is the number that actually hit the ledger
  const w = q.status === "Décomptée" ? q.final_weight : q.announced_weight;
  return `${w} ${Number(w) === 1 ? __("credit") : __("credits")}`;
});

const showBreakdown = computed(
  () =>
    !props.q.is_free &&
    ((props.q.multiplier && props.q.multiplier !== 1) ||
      (props.q.layer_factor && props.q.layer_factor !== 1))
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
  if (q.status !== "Annoncée" || !q.tacit_deadline) return "";
  const d = dayjs(q.tacit_deadline);
  const verb = d.isBefore(dayjs()) ? __("tacitly accepted since {0}") : __("tacit acceptance on {0}");
  return verb.replace("{0}", d.format("DD/MM/YYYY"));
});

const actions = computed(() => {
  const out: { label: string; event: string; theme?: string }[] = [];
  if (isFinal.value || !props.canQualify) return out;
  if (props.q.status !== "Sur devis")
    out.push({ label: __("Settle"), event: "settle" });
  out.push({ label: __("Requalify"), event: "requalify" });
  // RB-4: only the support manager may resolve doubt in the customer's favour
  if (props.isManager)
    out.push({ label: __("Lower category"), event: "lowerCategory" });
  return out;
});
</script>
