<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Requalify downwards'), size: 'lg' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <p v-if="q" class="text-ink-gray-6 text-sm">
          {{ q.grid_label || q.grid_code }} —
          <span class="tabular-nums">{{ formatCredits(q.announced_weight) }}</span>
          {{ __("credit(s) announced") }}
        </p>
        <p v-if="q && hasCeiling" class="text-ink-gray-5 text-xs -mt-2">
          {{ __("The announced weight is a ceiling: codes that would exceed it are disabled.") }}
        </p>

        <FormControl
          type="select"
          :label="__('New grid code')"
          v-model="form.new_code"
          :options="gridOptions"
        />

        <p v-if="selectedCode" class="text-ink-gray-5 text-xs -mt-2">
          {{ __("Grid weight: {0}", [gridWeightLabel(selectedCode)]) }}
        </p>

        <!-- only range codes take a weight; fixed codes use Annexe A as is -->
        <FormControl
          v-if="selectedIsRange"
          type="number"
          step="0.25"
          :min="selectedCode?.min_weight"
          :max="selectedCode?.max_weight"
          :label="__('Estimated weight')"
          v-model="form.new_base_weight"
          :required="true"
          :description="rangeHint"
        />
        <p
          v-if="selectedIsRange && form.new_base_weight !== '' && weightError"
          class="text-ink-red-4 text-xs -mt-2"
        >
          {{ weightError }}
        </p>

        <FormControl
          type="textarea"
          :label="__('Reason')"
          v-model="form.note"
          :required="true"
          :description="__('Recorded on the qualification and visible to the customer.')"
        />

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Requalify')"
          :loading="submitting"
          :disabled="!form.new_code || !form.note || Boolean(weightError)"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, call, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui";
import { computed, reactive, ref, watch } from "vue";
import {
  formatCredits,
  gridOptionLabel,
  gridWeightLabel,
  isQuoteOnly,
  isRange,
  minEffectiveWeight,
  rangeHintText,
  rangeWeightError,
  weightParam,
} from "./grid";
import type { GridCode, Qualification } from "./types";

const props = defineProps<{
  q: Qualification | null;
  grid: GridCode[];
}>();

const emit = defineEmits<{ requalified: [] }>();
const show = defineModel<boolean>({ required: true });

const submitting = ref(false);
const errorMessage = ref("");
const form = reactive({ new_code: "", new_base_weight: "" as string | number, note: "" });

watch(show, (open) => {
  if (open) {
    form.new_code = "";
    form.new_base_weight = "";
    form.note = "";
    errorMessage.value = "";
  }
});

// RB-2: requalification only goes down — the announced weight is an absolute
// ceiling, 0 included (a free D0/E0 line or a layer-2 line must not become a
// paying one without a new announcement). Codes that would exceed it, once
// this line's multiplier and layer are applied, are shown but not selectable.
// A draft or on-quote line has announced nothing yet: no ceiling there.
const hasCeiling = computed(
  () => Boolean(props.q) && !["Brouillon", "Sur devis"].includes(props.q!.status)
);

function exceedsCeiling(g: GridCode): boolean {
  if (!props.q || !hasCeiling.value) return false;
  // UI-R2-1: a quote-only code (F5) is another service, quoted outside the
  // pack — never a downward requalification of an announced weight (RB-2)
  if (isQuoteOnly(g)) return true;
  return minEffectiveWeight(g, props.q) > Number(props.q.announced_weight) + 0.0001;
}

const gridOptions = computed(() => [
  { label: __("Select a code"), value: "" },
  ...props.grid.map((g) => ({
    label: gridOptionLabel(g),
    value: g.code,
    disabled: exceedsCeiling(g),
  })),
]);

const selectedCode = computed(() =>
  props.grid.find((g) => g.code === form.new_code)
);
const selectedIsRange = computed(() => isRange(selectedCode.value));

watch(
  () => form.new_code,
  () => {
    form.new_base_weight = "";
  }
);

const weightError = computed(() =>
  rangeWeightError(selectedCode.value, form.new_base_weight)
);

const rangeHint = computed(() => rangeHintText(selectedCode.value));

async function submit() {
  if (!props.q) return;
  if (weightError.value) {
    errorMessage.value = weightError.value;
    return;
  }
  submitting.value = true;
  errorMessage.value = "";
  try {
    const res = await call("kb_credits.api.requalify", {
      qualification_name: props.q.name,
      new_code: form.new_code,
      note: form.note,
      new_base_weight: weightParam(selectedCode.value, form.new_base_weight),
    });
    toast.success(
      __("Requalified: {0} credit(s)").replace("{0}", formatCredits(res?.final_weight ?? 0))
    );
    show.value = false;
    emit("requalified");
  } catch (e: any) {
    errorMessage.value = e?.messages?.join(", ") || e?.message || String(e);
  } finally {
    submitting.value = false;
  }
}
</script>
