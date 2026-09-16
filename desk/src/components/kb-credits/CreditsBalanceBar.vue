<template>
  <div v-if="summary?.has_account" class="space-y-2">
    <div class="flex items-baseline justify-between gap-2">
      <span class="text-ink-gray-7 text-sm font-medium truncate">
        {{ summary.pack_name || summary.pack || __("Credits") }}
      </span>
      <Tooltip :text="__('Remaining / allocated credits for the period')">
        <span class="text-ink-gray-9 text-sm font-semibold shrink-0 tabular-nums">
          {{ format(summary.balance) }} / {{ format(summary.allocated) }}
        </span>
      </Tooltip>
    </div>

    <!-- consumption gauge -->
    <div class="h-1.5 w-full rounded-full bg-surface-gray-2 overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="barClass"
        :style="{ width: Math.min(summary.consumption_pct, 100) + '%' }"
      />
    </div>

    <div class="flex items-center justify-between gap-2">
      <span class="text-ink-gray-5 text-xs">
        {{ __("{0}% consumed").replace("{0}", String(summary.consumption_pct)) }}
      </span>
      <span v-if="periodLabel" class="text-ink-gray-5 text-xs shrink-0">
        {{ periodLabel }}
      </span>
    </div>

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
import { dayjs, Tooltip } from "frappe-ui";
import { computed } from "vue";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";
import type { AccountSummary } from "./types";

const props = defineProps<{ summary: AccountSummary | null }>();

function format(n: number | undefined): string {
  if (n === undefined || n === null) return "–";
  // credits are fractional (0.25 steps); drop noise but keep real decimals
  return Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/\.?0+$/, "");
}

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
  return __("Consumption has passed {0}% of the allocation.").replace(
    "{0}",
    String(threshold ?? "")
  );
});

const periodLabel = computed(() => {
  const s = props.summary;
  if (!s?.period_end) return "";
  return __("until {0}").replace("{0}", dayjs(s.period_end).format("DD/MM/YYYY"));
});
</script>
