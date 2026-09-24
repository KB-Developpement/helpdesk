<template>
  <!-- G3 / Convention 5.x: shown only while a 72 h legal window is open -->
  <div
    v-if="windows.length"
    class="flex items-start gap-3 rounded-lg border border-outline-red-1 bg-surface-red-1 px-4 py-3"
    role="alert"
  >
    <LucideSnowflake class="size-4 shrink-0 mt-0.5 text-ink-red-4" />
    <div class="min-w-0 space-y-1">
      <p class="text-base font-semibold text-ink-red-4">
        {{ __("Deployment freeze") }}
      </p>
      <p class="text-p-sm text-ink-red-3">
        <template v-if="audience === 'agent'">
          {{
            __(
              "A legal deadline is less than 72 hours away: no non-urgent deployment, on our side or the customer's."
            )
          }}
        </template>
        <template v-else>
          {{
            __(
              "A legal deadline is less than 72 hours away: please do not deploy anything non-urgent in production until it has passed. A blocked payroll or declaration is handled as a critical priority (P1)."
            )
          }}
        </template>
      </p>
      <ul class="text-p-sm text-ink-red-3 space-y-0.5">
        <li v-for="w in windows" :key="w.deadline + w.due_date">
          <span class="font-medium">{{ frenchifyText(w.description || w.deadline) }}</span>
          —
          {{
            __("due {0} ({1} h left)", formatDate(w.due_date), formatHours(w.hours_left))
          }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import LucideSnowflake from "~icons/lucide/snowflake";
import type { LegalWindow } from "./types";
import { formatDate, formatNumber, frenchifyText } from "./utils";

withDefaults(
  defineProps<{ windows: LegalWindow[]; audience?: "customer" | "agent" }>(),
  { audience: "customer" }
);

function formatHours(h: number): string {
  return formatNumber(Math.max(0, Number(h) || 0), 0);
}
</script>
