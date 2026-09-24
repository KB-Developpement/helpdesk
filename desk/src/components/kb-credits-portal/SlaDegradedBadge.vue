<template>
  <!-- Art. 5.7 : un pack L / XL sans exercice d'astreinte co-signé tourne sous
       SLA dégradé (KB L-DEG / KB XL-DEG). Le nom du pack seul (« Continuité
       24/7 ») laisserait croire au P1 nominal : on le dit en clair. -->
  <p
    v-if="isSlaDegraded(summary)"
    class="flex items-start gap-1.5 rounded bg-surface-amber-1 text-ink-amber-3"
    :class="compact ? 'px-2 py-1.5 text-xs leading-snug' : 'px-3 py-2 text-p-sm'"
    role="status"
  >
    <LucideShieldAlert class="shrink-0 mt-px" :class="compact ? 'size-3.5' : 'size-4'" />
    <span>
      {{
        __(
          "Degraded SLA: P1 at 8 working hours until the standby exercise has been carried out"
        )
      }}
    </span>
  </p>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import LucideShieldAlert from "~icons/lucide/shield-alert";
import type { SlaDegradationFields } from "./types";
import { isSlaDegraded } from "./utils";

withDefaults(
  defineProps<{
    summary: SlaDegradationFields | null | undefined;
    compact?: boolean;
  }>(),
  { compact: false }
);
</script>
