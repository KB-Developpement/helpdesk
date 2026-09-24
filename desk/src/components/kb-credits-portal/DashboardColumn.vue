<template>
  <!-- One column of the agent credits dashboard (manuel support §7). -->
  <section
    class="flex flex-col rounded-lg border bg-surface-white min-h-[160px]"
    :class="highlight && count ? 'border-outline-red-1' : 'border-outline-gray-2'"
  >
    <header
      class="flex items-center justify-between gap-2 px-4 py-3 border-b"
      :class="highlight && count ? 'border-outline-red-1 bg-surface-red-1' : 'border-outline-gray-1'"
    >
      <div class="flex items-center gap-2 min-w-0">
        <component :is="icon" v-if="icon" class="size-4 shrink-0 text-ink-gray-6" />
        <h3 class="text-base font-semibold text-ink-gray-9 truncate">{{ title }}</h3>
      </div>
      <Badge :theme="count ? (highlight ? 'red' : 'blue') : 'gray'" variant="subtle">
        {{ count }}
      </Badge>
    </header>
    <p v-if="hint" class="px-4 pt-2 text-p-sm text-ink-gray-5">{{ hint }}</p>
    <div class="flex-1 px-4 py-2">
      <slot v-if="count" />
      <p v-else class="py-4 text-center text-p-sm text-ink-gray-4">{{ emptyText }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Badge } from "frappe-ui";
import type { Component } from "vue";

defineProps<{
  title: string;
  count: number;
  emptyText: string;
  hint?: string;
  highlight?: boolean;
  icon?: Component;
}>();
</script>
