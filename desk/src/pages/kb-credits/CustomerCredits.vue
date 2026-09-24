<template>
  <!-- Customer portal — "Tickets → Mes crédits" (manuel client §7), route /my-credits -->
  <div class="flex flex-col w-full overflow-y-auto">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-ink-gray-9">
          {{ __("My credits") }}
        </div>
      </template>
      <template #right-header>
        <Button
          variant="ghost"
          :label="__('Refresh')"
          :loading="refreshing"
          @click="refreshAll"
        >
          <template #prefix><LucideRefreshCw class="size-4" /></template>
        </Button>
      </template>
    </LayoutHeader>

    <div class="w-full max-w-5xl mx-auto px-4 sm:px-6 py-5 flex flex-col gap-6">
      <LegalFreezeBanner :windows="legalWindows" audience="customer" />

      <!-- balance -->
      <div v-if="summary.loading && !summary.data" class="text-p-sm text-ink-gray-5">
        {{ __("Loading…") }}
      </div>
      <div
        v-else-if="summaryError"
        class="rounded-lg border border-outline-gray-2 px-4 py-3 text-p-base text-ink-gray-7"
      >
        {{ summaryError }}
      </div>
      <template v-else-if="summaryData">
        <BalanceCard v-if="summaryData.has_account" :summary="summaryData" />
        <div
          v-else
          class="rounded-lg border border-outline-gray-2 px-4 py-4 text-p-base text-ink-gray-7"
        >
          {{
            __(
              "You do not have an active credit account yet. Contact KB support to subscribe to a support pack."
            )
          }}
        </div>
      </template>

      <!-- F2: announcements waiting for the customer -->
      <section v-if="hasCustomer" class="flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <h2 class="text-lg font-semibold text-ink-gray-9">
            {{ __("Announcements awaiting your reply") }}
          </h2>
          <Badge v-if="awaiting.length" theme="orange" variant="subtle">
            {{ awaiting.length }}
          </Badge>
        </div>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              "Above 1 credit, we wait for your agreement before intervening. Without a reply within 48 working hours, the weight is deemed accepted. The announced weight is a ceiling: it can only go down."
            )
          }}
        </p>
        <div v-if="openLines.loading && !openLines.items.length" class="text-p-sm text-ink-gray-5">
          {{ __("Loading…") }}
        </div>
        <QualificationList
          v-else-if="openLines.items.length"
          :items="openLines.items"
          :show-ticket="true"
          @changed="onQualificationChanged"
        />
        <p v-else class="text-p-sm text-ink-gray-5">
          {{ __("Nothing is waiting for your reply.") }}
        </p>
      </section>

      <!-- F3: movements -->
      <section v-if="hasCustomer" class="flex flex-col gap-3">
        <h2 class="text-lg font-semibold text-ink-gray-9">
          {{ __("Movement history") }}
        </h2>
        <MovementsTable ref="movementsRef" />
      </section>

      <!-- F3: statements -->
      <section v-if="hasCustomer" class="flex flex-col gap-3">
        <h2 class="text-lg font-semibold text-ink-gray-9">
          {{ __("Monthly statements") }}
        </h2>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              "Without a written and reasoned contest within 15 days, a statement is deemed accepted and settles the account."
            )
          }}
        </p>
        <StatementsTable ref="statementsRef" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
import BalanceCard from "@/components/kb-credits-portal/BalanceCard.vue";
import LegalFreezeBanner from "@/components/kb-credits-portal/LegalFreezeBanner.vue";
import MovementsTable from "@/components/kb-credits-portal/MovementsTable.vue";
import QualificationList from "@/components/kb-credits-portal/QualificationList.vue";
import StatementsTable from "@/components/kb-credits-portal/StatementsTable.vue";
import type {
  LegalWindow,
  PortalAccountSummary,
  PortalQualification,
  PortalTicketCredits,
} from "@/components/kb-credits-portal/types";
import {
  canContestLayer,
  canContestWeight,
  canValidate,
  errorText,
} from "@/components/kb-credits-portal/utils";
import { __ } from "@/translation";
import { Badge, Button, call, createResource, dayjs, usePageMeta } from "frappe-ui";
import { computed, reactive, ref } from "vue";
import LucideRefreshCw from "~icons/lucide/refresh-cw";

usePageMeta(() => ({ title: __("My credits") }));

// ---------------------------------------------------------------- balance
const summaryError = ref("");
// include_pending=1: the page shows the pending announcements and statements,
// so reading them here counts as the customer being notified (the 48 h tacit
// period and the 15-day statement period start from this view, server-side).
const summary = createResource({
  url: "kb_credits.api.get_account_summary",
  params: { include_pending: 1 },
  auto: true,
  onSuccess() {
    loadOpenLines();
  },
  onError(e: any) {
    const msg = errorText(e);
    summaryError.value = /Aucun client/i.test(msg)
      ? __("Your user is not linked to a customer account. Please contact KB support.")
      : msg;
  },
});
const summaryData = computed(() => summary.data as PortalAccountSummary | null);
const hasCustomer = computed(() => Boolean(summaryData.value?.customer));

// ------------------------------------------------------- legal 72 h window
const legal = createResource({
  url: "kb_credits.api.legal_banner",
  auto: true,
  onError() {
    // the banner is informative: never block the page on it
  },
});
const legalWindows = computed(() => (legal.data as LegalWindow[]) || []);

// --------------------------------------------- lines waiting on the customer
// get_account_summary(include_pending=1) names the tickets with announcements
// to validate; the customer's live tickets (open, or touched in the last 15
// days so a layer can still be contested) are added. Full lines then come from
// get_ticket_credits, which checks access on each ticket.
const RECENT_DAYS = 15;
const MAX_TICKETS = 40;
const CONCURRENCY = 5;

const openLines = reactive({
  loading: false,
  items: [] as PortalQualification[],
});

function isRelevant(q: PortalQualification) {
  return (
    canValidate(q) ||
    canContestWeight(q) ||
    canContestLayer(q) ||
    q.status === "Contestée"
  );
}

let loadSeq = 0;

async function loadOpenLines() {
  const seq = ++loadSeq;
  openLines.loading = true;
  try {
    const live: { name: string; subject?: string }[] =
      (await call("frappe.client.get_list", {
        doctype: "HD Ticket",
        fields: ["name", "subject"],
        filters: [["customer", "is", "set"]],
        or_filters: [
          ["status_category", "!=", "Resolved"],
          ["modified", ">=", dayjs().subtract(RECENT_DAYS, "day").format("YYYY-MM-DD")],
        ],
        order_by: "modified desc",
        limit_page_length: MAX_TICKETS,
      }).catch(() => [])) || [];

    const tickets = [...live];
    const known = new Set(live.map((t) => t.name));
    for (const p of summaryData.value?.pending_validations || []) {
      if (p.ticket && !known.has(p.ticket)) {
        known.add(p.ticket);
        tickets.unshift({ name: p.ticket });
      }
    }

    const found: PortalQualification[] = [];
    for (let i = 0; i < tickets.length; i += CONCURRENCY) {
      const chunk = tickets.slice(i, i + CONCURRENCY);
      const results = await Promise.allSettled(
        chunk.map((t) =>
          call("kb_credits.api.get_ticket_credits", { ticket: t.name }).then(
            (res: PortalTicketCredits) => ({ t, res })
          )
        )
      );
      for (const r of results) {
        if (r.status !== "fulfilled" || !r.value.res) continue;
        const { t, res } = r.value;
        for (const q of res.qualifications || []) {
          if (isRelevant(q)) found.push({ ...q, ticket: t.name, ticket_subject: t.subject });
        }
      }
    }
    // what needs an answer first, then the soonest tacit deadline
    found.sort((a, b) => {
      const pa = canValidate(a) ? 0 : 1;
      const pb = canValidate(b) ? 0 : 1;
      if (pa !== pb) return pa - pb;
      return String(a.tacit_deadline || "9999").localeCompare(String(b.tacit_deadline || "9999"));
    });
    if (seq === loadSeq) openLines.items = found;
  } catch {
    // tickets list unavailable: leave the section empty rather than failing the page
    if (seq === loadSeq) openLines.items = [];
  } finally {
    if (seq === loadSeq) openLines.loading = false;
  }
}

const awaiting = computed(() => openLines.items.filter(canValidate));

// ------------------------------------------------------------------ refresh
const movementsRef = ref<InstanceType<typeof MovementsTable> | null>(null);
const statementsRef = ref<InstanceType<typeof StatementsTable> | null>(null);
const refreshing = ref(false);

// summary.onSuccess reloads the open lines: no separate call here
function onQualificationChanged() {
  Promise.resolve(summary.reload()).catch(() => {});
  movementsRef.value?.reload();
}

async function refreshAll() {
  refreshing.value = true;
  summaryError.value = "";
  try {
    await Promise.allSettled([
      summary.reload(),
      legal.reload(),
      movementsRef.value?.reload(),
      statementsRef.value?.reload(),
    ]);
  } finally {
    refreshing.value = false;
  }
}

</script>
