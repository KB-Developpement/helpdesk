<template>
  <!-- Customer-side list of qualification lines with their F2 actions
       (validate / contest the weight / contest the layer). Used by the
       "My credits" page and by the customer ticket sidebar. -->
  <ul class="space-y-2">
    <QualificationCard
      v-for="q in items"
      :key="q.name"
      :q="q"
      :show-ticket="showTicket"
      :readonly="readonly"
      :busy="busyFor === q.name ? busyAction : null"
      @validate="onValidate"
      @contest="onContest"
      @contest-layer="onContestLayer"
    />
  </ul>

  <ReasonDialog
    v-model="showContest"
    :title="__('Contest the announced weight')"
    :intro="contestIntro"
    :label="__('Reason for the contest')"
    :placeholder="__('Explain why this code or weight does not match your request.')"
    :hint="__('If the ambiguity persists, the lower category applies: the doubt benefits you.')"
    :submit-label="__('Contest')"
    :action="sendContest"
    @done="afterContest"
  />

  <LayerContestDialog v-model="showLayer" :q="active" @done="emit('changed')" />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { call, toast } from "frappe-ui";
import { computed, ref } from "vue";
import LayerContestDialog from "./LayerContestDialog.vue";
import QualificationCard from "./QualificationCard.vue";
import ReasonDialog from "./ReasonDialog.vue";
import type { PortalQualification } from "./types";
import { errorText, formatCredits } from "./utils";

// readonly: KB staff looking at the customer view. Validating or contesting
// belongs to the customer only (api.ensure_customer_self refuses staff).
withDefaults(
  defineProps<{ items: PortalQualification[]; showTicket?: boolean; readonly?: boolean }>(),
  { showTicket: false, readonly: false }
);
const emit = defineEmits<{ changed: [] }>();

const busyFor = ref<string | null>(null);
const busyAction = ref<string | null>(null);
const active = ref<PortalQualification | null>(null);
const showContest = ref(false);
const showLayer = ref(false);

async function onValidate(q: PortalQualification) {
  busyFor.value = q.name;
  busyAction.value = "validate";
  try {
    await call("kb_credits.api.validate_weight", { qualification_name: q.name });
    toast.success(__("Weight validated: we can proceed with the intervention."));
    emit("changed");
  } catch (e) {
    toast.error(errorText(e));
  } finally {
    busyFor.value = null;
    busyAction.value = null;
  }
}

function onContest(q: PortalQualification) {
  active.value = q;
  showContest.value = true;
}

function onContestLayer(q: PortalQualification) {
  active.value = q;
  showLayer.value = true;
}

const contestIntro = computed(() => {
  const q = active.value;
  if (!q) return "";
  return __(
    "{0} — {1}: {2} credit(s) announced.",
    q.grid_code,
    q.grid_label || "",
    formatCredits(q.announced_weight)
  );
});

async function sendContest(reason: string) {
  if (!active.value) return;
  await call("kb_credits.api.contest_weight", {
    qualification_name: active.value.name,
    reason,
  });
}

function afterContest() {
  toast.success(__("Your contest has been recorded and the Support Manager notified."));
  emit("changed");
}
</script>
