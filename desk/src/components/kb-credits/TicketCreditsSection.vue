<template>
  <!-- renders nothing at all if kb_credits is not installed on the site -->
  <Section v-if="available && hasCustomer" label="Credits" v-model:opened="opened">
    <template #header="{ opened: isOpen, toggle }">
      <div
        class="flex gap-2.5 items-center justify-between sticky top-0 bg-surface-white z-10 px-4 py-4 cursor-pointer"
        @click="toggle"
      >
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-ink-gray-8 font-semibold text-base select-none">
            {{ __("Credits") }}
          </span>
          <!-- the announced total is the number an agent looks for first -->
          <Badge
            v-if="credits?.announced_total"
            theme="blue"
            variant="subtle"
            size="sm"
          >
            {{ credits.announced_total }}
          </Badge>
        </div>
        <LucideChevronRight
          class="size-4 text-ink-gray-6 shrink-0"
          :class="{ 'rotate-90': isOpen }"
        />
      </div>
    </template>

    <div class="px-4 pb-4 space-y-3">
      <div v-if="resource.loading && !credits" class="text-ink-gray-5 text-sm">
        {{ __("Loading…") }}
      </div>

      <ErrorMessage v-else-if="loadError" :message="loadError" />

      <template v-else-if="credits">
        <CreditsBalanceBar :summary="credits.summary" />

        <!-- contractual states that change what the agent may do -->
        <div
          v-if="credits.on_quote"
          class="flex items-start gap-1.5 rounded bg-surface-violet-1 px-2 py-1.5"
        >
          <LucideFileText class="size-3.5 shrink-0 mt-px text-ink-violet-3" />
          <span class="text-ink-violet-3 text-xs leading-snug">
            {{ __("This ticket is on quote — no credits are consumed.") }}
          </span>
        </div>

        <div
          v-if="credits.legal_p1"
          class="flex items-start gap-1.5 rounded bg-surface-red-1 px-2 py-1.5"
        >
          <LucideGavel class="size-3.5 shrink-0 mt-px text-ink-red-3" />
          <span class="text-ink-red-3 text-xs leading-snug">
            {{ __("Legal P1") }}
            <template v-if="credits.legal_deadline">
              — {{ __("deadline {0}").replace("{0}", formatDate(credits.legal_deadline)) }}
            </template>
          </span>
        </div>

        <ul
          v-if="credits.qualifications.length"
          class="divide-y divide-outline-gray-1"
        >
          <QualificationItem
            v-for="q in credits.qualifications"
            :key="q.name"
            :q="q"
            :can-qualify="credits.can_qualify"
            :is-manager="credits.is_manager"
            :busy="busyFor === q.name ? busyAction : null"
            @settle="onSettle"
            @requalify="onRequalify"
            @lower-category="onLowerCategory"
          />
        </ul>

        <p v-else class="text-ink-gray-5 text-sm">
          {{ __("No qualification on this ticket yet.") }}
        </p>

        <div
          v-if="credits.settled_total"
          class="flex justify-between text-sm pt-1"
        >
          <span class="text-ink-gray-6">{{ __("Settled") }}</span>
          <span class="text-ink-gray-9 font-semibold tabular-nums">
            {{ credits.settled_total }}
          </span>
        </div>

        <Button
          v-if="credits.can_qualify && credits.summary?.has_account"
          class="w-full"
          :label="__('Announce a qualification')"
          :loading="optionsLoading"
          @click="openAnnounce"
        >
          <template #prefix><LucidePlus class="size-4" /></template>
        </Button>
      </template>
    </div>

    <AnnounceQualificationDialog
      v-if="ticketName"
      v-model="showAnnounce"
      :ticket="ticketName"
      :is-manager="Boolean(credits?.is_manager)"
      :grid="grid"
      :layers="layers"
      @announced="reload"
    />

    <RequalifyDialog
      v-model="showRequalify"
      :q="activeQualification"
      :grid="grid"
      @requalified="reload"
    />
  </Section>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { Badge, Button, call, createResource, dayjs, ErrorMessage, toast } from "frappe-ui";
import { computed, inject, ref, watch } from "vue";
import LucideChevronRight from "~icons/lucide/chevron-right";
import LucideFileText from "~icons/lucide/file-text";
import LucideGavel from "~icons/lucide/gavel";
import LucidePlus from "~icons/lucide/plus";
import Section from "../Section.vue";
import AnnounceQualificationDialog from "./AnnounceQualificationDialog.vue";
import CreditsBalanceBar from "./CreditsBalanceBar.vue";
import QualificationItem from "./QualificationItem.vue";
import RequalifyDialog from "./RequalifyDialog.vue";
import type { GridCode, Qualification, ResponsibilityLayer, TicketCredits } from "./types";

const ticket = inject(TicketSymbol)!;
const ticketName = computed(() => ticket.value?.name as string | undefined);

const opened = ref(false);
const loadError = ref("");
const available = ref(true);

// Credits hang off the customer's account: with no customer linked, the server
// legitimately refuses ("Aucun client n'a pu etre determine"). Don't call at all
// in that case, rather than turning a normal state into a red error box.
const hasCustomer = computed(() => Boolean(ticket.value?.customer));

const resource = createResource({
  url: "kb_credits.api.get_ticket_credits",
  makeParams: () => ({ ticket: ticketName.value }),
  auto: false,
  onError(e: any) {
    const msg = e?.messages?.join(", ") || e?.message || String(e);
    // kb_credits absent (or not permitted): stay silent rather than shouting
    if (/not found|does not exist|AttributeError|Method Not Allowed|PermissionError/i.test(msg)) {
      available.value = false;
      return;
    }
    loadError.value = msg;
  },
});

const credits = computed(() => resource.data as TicketCredits | undefined);

function reload() {
  if (!hasCustomer.value || !ticketName.value) return;
  loadError.value = "";
  resource.fetch();
}

watch(
  [ticketName, hasCustomer],
  () => {
    if (hasCustomer.value && ticketName.value) reload();
  },
  { immediate: true }
);

// ---- grid + layers: only fetched when the agent actually opens a dialog ----
const grid = ref<GridCode[]>([]);
const layers = ref<ResponsibilityLayer[]>([]);
const optionsLoading = ref(false);

async function ensureOptions() {
  if (grid.value.length && layers.value.length) return;
  optionsLoading.value = true;
  try {
    const [g, l] = await Promise.all([
      call("kb_credits.api.get_grid", { ticket: ticketName.value }),
      call("kb_credits.api.get_responsibility_layers"),
    ]);
    grid.value = g || [];
    layers.value = l || [];
  } catch (e: any) {
    toast.error(e?.messages?.join(", ") || e?.message || String(e));
  } finally {
    optionsLoading.value = false;
  }
}

const showAnnounce = ref(false);
const showRequalify = ref(false);
const activeQualification = ref<Qualification | null>(null);

async function openAnnounce() {
  await ensureOptions();
  showAnnounce.value = true;
}

async function onRequalify(q: Qualification) {
  activeQualification.value = q;
  await ensureOptions();
  showRequalify.value = true;
}

// ---- direct actions ----
const busyFor = ref<string | null>(null);
const busyAction = ref<string | null>(null);

async function run(q: Qualification, action: string, method: string, params: object) {
  busyFor.value = q.name;
  busyAction.value = action;
  try {
    await call(method, params);
    toast.success(__("Done"));
    reload();
  } catch (e: any) {
    toast.error(e?.messages?.join(", ") || e?.message || String(e));
  } finally {
    busyFor.value = null;
    busyAction.value = null;
  }
}

function onSettle(q: Qualification) {
  run(q, "settle", "kb_credits.api.settle", { qualification_name: q.name });
}

function onLowerCategory(q: Qualification) {
  run(q, "lowerCategory", "kb_credits.api.apply_lower_category", {
    qualification_name: q.name,
  });
}

function formatDate(d: string) {
  return dayjs(d).format("DD/MM/YYYY");
}
</script>
