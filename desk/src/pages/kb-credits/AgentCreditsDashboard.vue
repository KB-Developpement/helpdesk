<template>
  <!-- Agent desk — "Menu → Crédits d'intervention" (manuel support §7), route /kb-credits -->
  <div class="flex flex-col w-full overflow-y-auto">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-ink-gray-9">
          {{ __("Intervention credits") }}
        </div>
      </template>
      <template #right-header>
        <span v-if="lastLoaded" class="hidden sm:inline text-p-sm text-ink-gray-5">
          {{ __("Updated at {0}", lastLoaded) }}
        </span>
        <Button
          variant="ghost"
          :label="__('Refresh')"
          :loading="dashboard.loading"
          @click="reload"
        >
          <template #prefix><LucideRefreshCw class="size-4" /></template>
        </Button>
      </template>
    </LayoutHeader>

    <div class="w-full px-4 sm:px-5 py-5 flex flex-col gap-5">
      <LegalFreezeBanner :windows="data?.legal_windows || []" audience="agent" />

      <ErrorMessage v-if="errorMessage" :message="errorMessage" />

      <div v-if="dashboard.loading && !data" class="text-p-sm text-ink-gray-5">
        {{ __("Loading…") }}
      </div>

      <template v-if="data">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              "Check it at the start of the day. Imminent tacit acceptances and calendar P1s are the two columns that cost money when left unattended."
            )
          }}
        </p>

        <div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-4">
          <!-- 1. awaiting customer validation -->
          <DashboardColumn
            :title="__('Awaiting customer validation')"
            :count="data.pending_validation.length"
            :empty-text="__('No announcement awaiting validation.')"
            :icon="LucideHourglass"
          >
            <ul class="divide-y divide-outline-gray-1">
              <li v-for="q in data.pending_validation" :key="q.name" class="py-2">
                <QualificationRow :q="q">
                  <template #meta>
                    <span v-if="q.tacit_deadline">
                      {{ __("Tacit acceptance on {0}", formatDateTime(q.tacit_deadline)) }}
                    </span>
                    <span v-else class="text-ink-amber-3">
                      {{ __("Customer not notified yet: the 48 h have not started.") }}
                    </span>
                  </template>
                </QualificationRow>
              </li>
            </ul>
          </DashboardColumn>

          <!-- 2. tacit acceptances within 24 h -->
          <DashboardColumn
            :title="__('Imminent tacit acceptances')"
            :hint="__('Less than 24 h before the weight is deemed accepted.')"
            :count="data.tacit_imminent.length"
            :empty-text="__('No imminent tacit acceptance.')"
            :highlight="true"
            :icon="LucideAlarmClock"
          >
            <ul class="divide-y divide-outline-gray-1">
              <li v-for="q in data.tacit_imminent" :key="q.name" class="py-2">
                <QualificationRow :q="q">
                  <template #meta>
                    <span :class="isPast(q.tacit_deadline) ? 'text-ink-red-4' : 'text-ink-amber-3'">
                      {{ deadlineLabel(q.tacit_deadline) }}
                    </span>
                  </template>
                </QualificationRow>
              </li>
            </ul>
          </DashboardColumn>

          <!-- 3. open contests -->
          <DashboardColumn
            :title="__('Open contests')"
            :hint="__('Requalify downwards or apply the lower category: the doubt benefits the customer.')"
            :count="data.contested.length"
            :empty-text="__('No open contest.')"
            :icon="LucideMessageSquareWarning"
          >
            <ul class="divide-y divide-outline-gray-1">
              <li v-for="q in data.contested" :key="q.name" class="py-2">
                <QualificationRow :q="q">
                  <template #meta>
                    <span v-if="q.contest_reason" class="italic">« {{ q.contest_reason }} »</span>
                  </template>
                </QualificationRow>
              </li>
            </ul>
          </DashboardColumn>

          <!-- 3b. contested statements (UI-R3-2): the Support Manager's to-do,
               otherwise only visible in the Frappe desk bell -->
          <DashboardColumn
            :title="__('Contested statements')"
            :hint="__('Answer the customer and correct by a reversing entry if needed: the statement is not deemed accepted while contested.')"
            :count="(data.contested_statements || []).length"
            :empty-text="__('No contested statement.')"
            :highlight="(data.contested_statements || []).length > 0"
            :icon="LucideFileWarning"
          >
            <ul class="divide-y divide-outline-gray-1">
              <li v-for="s in data.contested_statements || []" :key="s.name" class="py-2 space-y-0.5">
                <div class="flex items-center justify-between gap-2">
                  <a
                    :href="'/app/kb-credit-statement/' + encodeURIComponent(s.name)"
                    target="_blank"
                    class="text-base font-medium text-ink-gray-9 hover:underline truncate"
                  >
                    {{ s.customer || s.name }}
                  </a>
                  <span class="text-p-sm text-ink-gray-5 shrink-0">{{ s.name }}</span>
                </div>
                <p class="text-p-sm text-ink-gray-6">
                  {{ formatDate(s.period_start) }} → {{ formatDate(s.period_end) }}
                  <span v-if="s.contested_on">
                    · {{ __("Contested on {0}", formatDateTime(s.contested_on)) }}
                  </span>
                </p>
                <p v-if="s.contest_reason" class="text-p-sm italic text-ink-gray-6">« {{ s.contest_reason }} »</p>
              </li>
            </ul>
          </DashboardColumn>

          <!-- 4. calendar P1 in progress -->
          <DashboardColumn
            :title="__('Calendar P1 in progress')"
            :hint="__('Priority cannot be lowered while the incident is open.')"
            :count="data.legal_p1_tickets.length"
            :empty-text="__('No calendar P1 in progress.')"
            :highlight="true"
            :icon="LucideGavel"
          >
            <ul class="divide-y divide-outline-gray-1">
              <li v-for="t in data.legal_p1_tickets" :key="t.name" class="py-2 space-y-0.5">
                <div class="flex items-center justify-between gap-2">
                  <router-link
                    :to="{ name: 'TicketAgent', params: { ticketId: t.name } }"
                    class="text-base font-medium text-ink-gray-9 hover:underline truncate"
                  >
                    #{{ t.name }} <span v-if="t.subject" class="font-normal">— {{ t.subject }}</span>
                  </router-link>
                  <Badge v-if="t.priority" theme="red" variant="subtle" size="sm">
                    {{ t.priority }}
                  </Badge>
                </div>
                <p class="text-p-sm text-ink-gray-6">
                  <span v-if="t.customer">{{ t.customer }}</span>
                  <span v-if="t.kb_legal_deadline">
                    · {{ __("Legal deadline {0}", formatDate(t.kb_legal_deadline)) }}
                  </span>
                </p>
              </li>
            </ul>
          </DashboardColumn>

          <!-- 5. accounts close to the annual remedy cap -->
          <DashboardColumn
            :title="__('Accounts near the remedy cap')"
            :hint="__('SLA remedy credits received ≥ 80% of the annual cap.')"
            :count="data.accounts_near_remedy_cap.length"
            :empty-text="__('No account near the remedy cap.')"
            :icon="LucideShieldAlert"
          >
            <ul class="divide-y divide-outline-gray-1">
              <li v-for="a in data.accounts_near_remedy_cap" :key="a.name" class="py-2 space-y-1">
                <div class="flex items-center justify-between gap-2">
                  <a
                    :href="'/app/kb-credit-account/' + encodeURIComponent(a.name)"
                    target="_blank"
                    class="text-base font-medium text-ink-gray-9 hover:underline truncate"
                  >
                    {{ a.customer }}
                  </a>
                  <span class="text-p-sm tabular-nums text-ink-gray-8 shrink-0">
                    {{ formatCredits(a.remedy_credits_received) }} / {{ formatCredits(a.remedy_annual_cap) }}
                  </span>
                </div>
                <div class="h-1.5 w-full rounded-full bg-surface-gray-2 overflow-hidden">
                  <div
                    class="h-full rounded-full"
                    :class="remedyRatio(a) >= 100 ? 'bg-surface-red-5' : 'bg-surface-amber-2'"
                    :style="{ width: Math.min(remedyRatio(a), 100) + '%' }"
                  />
                </div>
                <p class="text-p-sm text-ink-gray-5">
                  {{ a.name }}
                  <template v-if="a.consumption_pct !== null && a.consumption_pct !== undefined">
                    · {{ __("{0}% consumed", formatCredits(a.consumption_pct)) }}
                  </template>
                </p>
              </li>
            </ul>
          </DashboardColumn>

          <!-- 6. open legal windows -->
          <DashboardColumn
            :title="__('Open legal windows')"
            :hint="__('Deployment freeze: no non-urgent deployment during these windows.')"
            :count="data.legal_windows.length"
            :empty-text="__('No legal window open.')"
            :icon="LucideLandmark"
          >
            <ul class="divide-y divide-outline-gray-1">
              <li v-for="w in data.legal_windows" :key="w.deadline + w.due_date" class="py-2 space-y-0.5">
                <p class="text-base font-medium text-ink-gray-9">
                  {{ frenchifyText(w.description || w.deadline) }}
                </p>
                <p class="text-p-sm text-ink-gray-6">
                  {{ __("Due {0}", formatDate(w.due_date)) }} ·
                  {{ __("{0} h left", formatCredits(Math.max(0, Math.round(w.hours_left)))) }}
                </p>
              </li>
            </ul>
          </DashboardColumn>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
import DashboardColumn from "@/components/kb-credits-portal/DashboardColumn.vue";
import LegalFreezeBanner from "@/components/kb-credits-portal/LegalFreezeBanner.vue";
import QualificationRow from "@/components/kb-credits-portal/DashboardQualificationRow.vue";
import type { AgentDashboard, DashboardAccount } from "@/components/kb-credits-portal/types";
import {
  errorText,
  formatCredits,
  formatDate,
  formatDateTime,
  frenchifyText,
  isPast,
} from "@/components/kb-credits-portal/utils";
import { __ } from "@/translation";
import { Badge, Button, createResource, dayjs, ErrorMessage, usePageMeta } from "frappe-ui";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import LucideAlarmClock from "~icons/lucide/alarm-clock";
import LucideFileWarning from "~icons/lucide/file-warning";
import LucideGavel from "~icons/lucide/gavel";
import LucideHourglass from "~icons/lucide/hourglass";
import LucideLandmark from "~icons/lucide/landmark";
import LucideMessageSquareWarning from "~icons/lucide/message-square-warning";
import LucideRefreshCw from "~icons/lucide/refresh-cw";
import LucideShieldAlert from "~icons/lucide/shield-alert";

usePageMeta(() => ({ title: __("Intervention credits") }));

const errorMessage = ref("");
const lastLoaded = ref("");

const dashboard = createResource({
  url: "kb_credits.api.agent_dashboard",
  auto: true,
  onSuccess() {
    errorMessage.value = "";
    lastLoaded.value = dayjs().format("HH:mm");
  },
  onError(e: any) {
    errorMessage.value = errorText(e);
  },
});

const data = computed(() => dashboard.data as AgentDashboard | null);

function reload() {
  Promise.resolve(dashboard.reload()).catch(() => {});
}

// the page is meant to stay open: refresh every 5 minutes
let timer: ReturnType<typeof setInterval> | null = null;
onMounted(() => {
  timer = setInterval(reload, 5 * 60 * 1000);
});
onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});

function remedyRatio(a: DashboardAccount): number {
  const cap = Number(a.remedy_annual_cap) || 0;
  if (!cap) return 0;
  return (Number(a.remedy_credits_received) / cap) * 100;
}

function deadlineLabel(d: string | null | undefined): string {
  if (!d) return "";
  if (isPast(d)) return __("Deadline passed on {0}", formatDateTime(d));
  const hours = dayjs(d).diff(dayjs(), "hour", true);
  return __("Tacit acceptance in {0} h ({1})", formatCredits(Math.max(0, Math.round(hours))), formatDateTime(d));
}
</script>
