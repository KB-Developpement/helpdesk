<template>
  <section
    v-if="summary?.has_account"
    class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 sm:p-5 space-y-4"
  >
    <!-- pack + period -->
    <div class="flex flex-wrap items-start justify-between gap-2">
      <div class="min-w-0">
        <p class="text-lg font-semibold text-ink-gray-9 truncate">
          {{ packLabel }}
        </p>
        <p v-if="summary.period_start" class="text-p-sm text-ink-gray-5">
          {{ __("Period from {0} to {1}", formatDate(summary.period_start), formatDate(summary.period_end)) }}
        </p>
      </div>
      <Badge :theme="levelTheme" variant="subtle" size="md">
        {{ levelLabel }}
      </Badge>
    </div>

    <SlaDegradedBadge :summary="summary" />

    <!-- the three numbers the customer looks for -->
    <div class="grid grid-cols-3 gap-3">
      <div class="rounded bg-surface-gray-1 px-3 py-2">
        <!-- compte « Recharge » (Annexe 8, sans pack) : pas de dotation, la base est ce qui a été acheté -->
        <p class="text-xs text-ink-gray-5">
          {{ summary.account_type === "Recharge" ? __("Purchased") : __("Allocated") }}
        </p>
        <p class="text-xl font-semibold tabular-nums text-ink-gray-9">
          {{ formatCredits(summary.consumption_base ?? summary.allocated) }}
        </p>
      </div>
      <div class="rounded bg-surface-gray-1 px-3 py-2">
        <p class="text-xs text-ink-gray-5">{{ __("Consumed") }}</p>
        <p class="text-xl font-semibold tabular-nums text-ink-gray-9">
          {{ formatCredits(summary.consumed) }}
        </p>
      </div>
      <div class="rounded bg-surface-gray-1 px-3 py-2">
        <p class="text-xs text-ink-gray-5">{{ __("Balance") }}</p>
        <p
          class="text-xl font-semibold tabular-nums"
          :class="(summary.balance ?? 0) < 0 ? 'text-ink-red-4' : 'text-ink-gray-9'"
        >
          {{ formatCredits(summary.balance) }}
        </p>
      </div>
    </div>

    <!-- consumption gauge with the 70 % / 90 % marks -->
    <div class="space-y-1.5">
      <div class="relative h-2 w-full rounded-full bg-surface-gray-2 overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-300"
          :class="barClass"
          :style="{ width: Math.min(Math.max(pct, 0), 100) + '%' }"
        />
        <div
          v-for="t in thresholdMarks"
          :key="t"
          class="absolute top-0 h-full w-px bg-surface-gray-5"
          :style="{ left: t + '%' }"
        />
      </div>
      <div class="flex flex-wrap justify-between gap-2 text-p-sm text-ink-gray-6">
        <span>{{ __("{0}% consumed", formatCredits(pct)) }}</span>
        <span v-if="thresholdMarks.length">
          {{ __("Alerts at {0}% and {1}%", formatCredits(summary.thresholds?.warning), formatCredits(summary.thresholds?.danger)) }}
        </span>
      </div>
    </div>

    <div
      v-if="summary.alert_level && summary.alert_level !== 'ok'"
      class="flex items-start gap-2 rounded px-3 py-2"
      :class="summary.alert_level === 'danger' ? 'bg-surface-red-1 text-ink-red-4' : 'bg-surface-amber-1 text-ink-amber-3'"
    >
      <LucideTriangleAlert class="size-4 shrink-0 mt-px" />
      <span class="text-p-sm">
        {{ alertMessage }}
      </span>
    </div>

    <!-- remedies / symmetry: only once something happened -->
    <div
      v-if="summary.remedy_credits || summary.symmetry_credits"
      class="flex flex-wrap gap-x-6 gap-y-1 text-p-sm text-ink-gray-6 border-t border-outline-gray-1 pt-3"
    >
      <span v-if="summary.remedy_credits">
        {{ __("SLA remedy credits received: {0}", formatCredits(summary.remedy_credits)) }}
        <template v-if="summary.remedy_cap">
          / {{ formatCredits(summary.remedy_cap) }}
        </template>
      </span>
      <span v-if="summary.symmetry_credits">
        {{ __("Credits charged for waiting on your reply: {0}", formatCredits(summary.symmetry_credits)) }}
      </span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Badge } from "frappe-ui";
import { computed } from "vue";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";
import SlaDegradedBadge from "./SlaDegradedBadge.vue";
import type { PortalAccountSummary } from "./types";
import { formatCredits, formatDate } from "./utils";

const props = defineProps<{ summary: PortalAccountSummary | null | undefined }>();

const pct = computed(() => Number(props.summary?.consumption_pct || 0));

const packLabel = computed(() => {
  const s = props.summary;
  if (!s) return "";
  if (s.account_type && s.account_type !== "Pack") {
    return s.pack_name || s.account_type;
  }
  return __("Pack {0}", s.pack_name || s.pack || "");
});

const thresholdMarks = computed(() => {
  const t = props.summary?.thresholds;
  if (!t) return [];
  return [t.warning, t.danger].filter((v) => v && v > 0 && v < 100);
});

const barClass = computed(() => {
  switch (props.summary?.alert_level) {
    case "danger":
      return "bg-surface-red-5";
    case "warning":
      return "bg-surface-amber-2";
    default:
      return "bg-surface-green-3";
  }
});

const levelTheme = computed(() => {
  switch (props.summary?.alert_level) {
    case "danger":
      return "red";
    case "warning":
      return "orange";
    default:
      return "green";
  }
});

const levelLabel = computed(() => {
  switch (props.summary?.alert_level) {
    case "danger":
      return __("Critical level");
    case "warning":
      return __("Watch level");
    default:
      return __("Normal level");
  }
});

const alertMessage = computed(() => {
  const s = props.summary;
  if (!s) return "";
  const threshold =
    s.alert_level === "danger" ? s.thresholds?.danger : s.thresholds?.warning;
  return __(
    "Consumption has passed {0}% of the allocation. A 30-credit recharge is available during the year.",
    formatCredits(threshold)
  );
});
</script>
