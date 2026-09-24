<template>
  <!-- F3: monthly statements. "Deemed accepted" after 15 days without a
       written, reasoned contest — the clock only runs once the customer was
       notified, so a missing deadline is shown as such, never guessed. -->
  <div class="space-y-3">
    <div v-if="rows.length" class="overflow-x-auto rounded-lg border border-outline-gray-2">
      <table class="w-full min-w-[980px] text-base">
        <thead class="bg-surface-gray-1 text-left text-p-sm text-ink-gray-5">
          <tr>
            <th class="px-3 py-2 font-medium">{{ __("Period") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Opening") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Allocations & recharges") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Consumed") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Remedies") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Symmetry") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Adjustments & expirations") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("Closing") }}</th>
            <th class="px-3 py-2 font-medium text-right">{{ __("SLA breaches") }}</th>
            <th class="px-3 py-2 font-medium">{{ __("Status") }}</th>
            <th class="px-3 py-2 font-medium"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1">
          <tr v-for="s in rows" :key="s.name" class="align-top">
            <td class="px-3 py-2 whitespace-nowrap">
              <p class="text-ink-gray-8">
                {{ formatDate(s.period_start) }} → {{ formatDate(s.period_end) }}
              </p>
              <p class="text-p-sm text-ink-gray-5">{{ s.statement_type }}</p>
            </td>
            <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">
              {{ formatCredits(s.opening_balance) }}
            </td>
            <!-- opening + recharges − consumed + remedies − symmetry ± adjustments = closing,
                 as in the PDF (templates/statement.html) -->
            <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">
              {{ s.total_recharges ? formatSignedCredits(s.total_recharges) : "—" }}
            </td>
            <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">
              {{ s.total_consumed ? formatSignedCredits(-s.total_consumed) : "0" }}
            </td>
            <td class="px-3 py-2 text-right tabular-nums text-ink-green-3">
              {{ s.total_remedies ? formatSignedCredits(s.total_remedies) : "—" }}
            </td>
            <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">
              {{ s.total_symmetry ? formatSignedCredits(-s.total_symmetry) : "—" }}
            </td>
            <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">
              {{ s.total_adjustments ? formatSignedCredits(s.total_adjustments) : "—" }}
            </td>
            <td class="px-3 py-2 text-right tabular-nums font-semibold text-ink-gray-9">
              {{ formatCredits(s.closing_balance) }}
            </td>
            <td class="px-3 py-2 text-right tabular-nums text-ink-gray-7">
              {{ s.sla_breaches || 0 }}
            </td>
            <td class="px-3 py-2">
              <Badge :theme="statementTheme(s.status)" variant="subtle" size="sm">
                {{ s.status }}
              </Badge>
              <p v-if="s.status === 'Émis'" class="text-p-sm text-ink-gray-5 mt-1 max-w-[220px]">
                <template v-if="s.acceptance_deadline">
                  {{ __("Deemed accepted on {0} without a contest.", formatDate(s.acceptance_deadline)) }}
                </template>
                <template v-else>
                  {{ __("15 days to contest, counted from its notification.") }}
                </template>
              </p>
            </td>
            <td class="px-3 py-2">
              <div class="flex justify-end gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  :label="__('Download')"
                  @click="download(s)"
                >
                  <template #prefix><LucideDownload class="size-3.5" /></template>
                </Button>
                <Button
                  v-if="canContest && canContestStatement(s)"
                  size="sm"
                  variant="subtle"
                  theme="red"
                  :label="__('Contest')"
                  @click="openContest(s)"
                />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else-if="!loading" class="text-p-sm text-ink-gray-5">
      {{ __("No statement issued yet. The monthly statement is issued on the 1st of each month.") }}
    </p>

    <ErrorMessage :message="error" />

    <ReasonDialog
      v-model="showContest"
      :title="__('Contest the statement')"
      :intro="contestIntro"
      :label="__('Written and reasoned contest')"
      :placeholder="__('Indicate the movements you dispute and why.')"
      :submit-label="__('Contest')"
      :action="sendContest"
      @done="afterContest"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Badge, Button, call, ErrorMessage, toast } from "frappe-ui";
import { computed, onMounted, ref } from "vue";
import LucideDownload from "~icons/lucide/download";
import ReasonDialog from "./ReasonDialog.vue";
import type { Statement } from "./types";
import {
  canContestStatement,
  errorText,
  formatCredits,
  formatDate,
  formatSignedCredits,
  statementTheme,
} from "./utils";

const props = withDefaults(
  defineProps<{ customer?: string | null; canContest?: boolean }>(),
  { customer: null, canContest: true }
);

const rows = ref<Statement[]>([]);
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    rows.value =
      (await call("kb_credits.api.get_statements", {
        customer: props.customer || undefined,
      })) || [];
  } catch (e) {
    error.value = errorText(e);
  } finally {
    loading.value = false;
  }
}

// Served by kb_credits.api.download_statement (customer access checked there).
function download(s: Statement) {
  const url =
    "/api/method/kb_credits.api.download_statement?statement=" +
    encodeURIComponent(s.name);
  window.open(url, "_blank");
}

const showContest = ref(false);
const active = ref<Statement | null>(null);

function openContest(s: Statement) {
  active.value = s;
  showContest.value = true;
}

const contestIntro = computed(() => {
  const s = active.value;
  if (!s) return "";
  return __(
    "Statement from {0} to {1}. Without a written and reasoned contest within 15 days, it is deemed accepted and settles the account.",
    formatDate(s.period_start),
    formatDate(s.period_end)
  );
});

async function sendContest(reason: string) {
  if (!active.value) return;
  await call("kb_credits.api.contest_statement", {
    statement: active.value.name,
    reason,
  });
}

function afterContest() {
  toast.success(__("Your contest has been recorded and the Support Manager notified."));
  load();
}

onMounted(load);
defineExpose({ reload: load });
</script>
