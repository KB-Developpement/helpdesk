<template>
  <div v-if="summary?.has_account" class="space-y-2">
    <div class="flex items-baseline justify-between gap-2">
      <span class="text-ink-gray-7 text-sm font-medium truncate">
        {{ summary.pack_name || summary.pack || __("Credits") }}
      </span>
      <Tooltip :text="__('Remaining / allocated credits for the period')">
        <span class="text-ink-gray-9 text-sm font-semibold shrink-0 tabular-nums">
          {{ formatCredits(summary.balance) }} / {{ formatCredits(summary.consumption_base ?? summary.allocated) }}
        </span>
      </Tooltip>
    </div>

    <!-- consumption gauge -->
    <div class="h-1.5 w-full rounded-full bg-surface-gray-2 overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="barClass"
        :style="{ width: Math.min(Number(summary.consumption_pct || 0), 100) + '%' }"
      />
    </div>

    <div class="flex items-center justify-between gap-2">
      <span class="text-ink-gray-5 text-xs">
        {{ __("{0}% consumed", formatCredits(summary.consumption_pct ?? 0)) }}
      </span>
      <span v-if="periodLabel" class="text-ink-gray-5 text-xs shrink-0">
        {{ periodLabel }}
      </span>
    </div>

    <!-- art. 5.7 : P1 dégradé tant que l'exercice d'astreinte n'est pas fait -->
    <SlaDegradedBadge :summary="degradation" compact />

    <!-- only surfaced once a threshold is actually crossed -->
    <div
      v-if="summary.alert_level !== 'ok'"
      class="flex items-start gap-1.5 rounded px-2 py-1.5"
      :class="alertClass"
    >
      <LucideTriangleAlert class="size-3.5 shrink-0 mt-px" />
      <span class="text-xs leading-snug">{{ alertMessage }}</span>
    </div>
  </div>

  <div v-else-if="summary" class="text-ink-gray-5 text-sm">
    {{ __("No credit account for this customer.") }}
  </div>
</template>

<script setup lang="ts">
import SlaDegradedBadge from "@/components/kb-credits-portal/SlaDegradedBadge.vue";
import type { SlaDegradationFields } from "@/components/kb-credits-portal/types";
import { formatCredits, formatDate } from "@/components/kb-credits-portal/format";
import { isSlaDegraded } from "@/components/kb-credits-portal/utils";
import { __ } from "@/translation";
import { call, Tooltip } from "frappe-ui";
import { computed, ref, watch } from "vue";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";
import type { AccountSummary } from "./types";

const props = defineProps<{ summary: AccountSummary | null }>();

// Le résumé du compte ne dit pas toujours si le SLA est dégradé (art. 5.7).
// Côté agent, la fiche KB Credit Account est lisible (rôle Agent) : on y lit
// l'état de l'exercice d'astreinte quand le résumé ne le porte pas.
const accountFields = ref<SlaDegradationFields | null>(null);

function summaryKnowsDegradation(s: AccountSummary | null): boolean {
  if (!s) return true;
  // le champ `sla` du compte porte le SLA nominal (« KB XL ») : seul un nom en
  // « -DEG », le drapeau explicite ou l'état de l'exercice tranchent
  if (isSlaDegraded(s)) return true;
  return [s.sla_degraded, s.standby_test_done].some((v) => v !== undefined && v !== null);
}

watch(
  () => props.summary?.account,
  async (account) => {
    accountFields.value = null;
    const s = props.summary;
    if (!account || summaryKnowsDegradation(s)) return;
    if (!["L", "XL"].includes(String(s?.pack || "").toUpperCase())) return;
    try {
      const row = await call("frappe.client.get_value", {
        doctype: "KB Credit Account",
        filters: { name: account },
        fieldname: ["standby_test_done", "sla", "pack", "account_type"],
      });
      if (props.summary?.account === account) accountFields.value = row || null;
    } catch {
      // pas de droit de lecture : on n'affiche rien plutôt qu'une supposition
    }
  },
  { immediate: true }
);

const degradation = computed<SlaDegradationFields | null>(() => {
  const s = props.summary;
  if (!s) return null;
  return accountFields.value ? { ...s, ...accountFields.value } : s;
});

const barClass = computed(() => {
  switch (props.summary?.alert_level) {
    case "danger":
      return "bg-surface-red-5";
    case "warning":
      return "bg-surface-amber-3";
    default:
      return "bg-surface-green-3";
  }
});

const alertClass = computed(() =>
  props.summary?.alert_level === "danger"
    ? "bg-surface-red-1 text-ink-red-3"
    : "bg-surface-amber-1 text-ink-amber-3"
);

const alertMessage = computed(() => {
  const s = props.summary;
  if (!s) return "";
  const threshold =
    s.alert_level === "danger" ? s.thresholds?.danger : s.thresholds?.warning;
  return __("Consumption has passed {0}% of the allocation.", formatCredits(threshold ?? 0));
});

const periodLabel = computed(() => {
  const s = props.summary;
  if (!s?.period_end) return "";
  return __("until {0}", formatDate(s.period_end));
});
</script>
