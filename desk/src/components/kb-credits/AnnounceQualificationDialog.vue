<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Announce a qualification'), size: 'lg' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <FormControl
          type="select"
          :label="__('Grid code')"
          v-model="form.grid_code"
          :options="gridOptions"
        />

        <div v-if="selectedCode" class="-mt-2 space-y-1">
          <p class="text-ink-gray-5 text-xs">
            {{ __("Grid weight: {0}", [gridWeightLabel(selectedCode)]) }}
            <template v-if="selectedCode.category">
              · {{ selectedCode.category }}
            </template>
          </p>
          <p
            v-if="selectedCode.description"
            class="text-ink-gray-5 text-xs leading-snug"
          >
            {{ selectedCode.description }}
          </p>
          <p
            v-if="isQuoteOnly(selectedCode)"
            class="text-violet-700 text-xs leading-snug"
          >
            {{ __("This code puts the ticket on quote — no credits are consumed.") }}
          </p>
        </div>

        <!-- CB-8: the after-hours multiplier depends on WHEN the intervention
             takes place, not on when the agent announces it -->
        <div class="space-y-1">
          <FormControl
            type="datetime-local"
            :label="__('Planned intervention')"
            v-model="form.intervention_at"
            :description="__('The after-hours multiplier depends on this time, not on the announcement time.')"
          />
          <p
            v-if="preview && !isFreeCode"
            class="text-xs leading-snug"
            :class="preview.multiplier > 1 ? 'text-ink-amber-3' : 'text-ink-gray-5'"
          >
            <template v-if="preview.multiplier > 1">
              {{
                __("Outside working hours: weight × {0}").replace(
                  "{0}",
                  formatCredits(preview.multiplier)
                )
              }}
            </template>
            <template v-else>
              {{ __("Within working hours: no multiplier") }}
            </template>
          </p>
        </div>

        <FormControl
          type="select"
          :label="__('Responsibility layer')"
          v-model="form.responsibility_layer"
          :options="layerOptions"
          :description="__('Article 4 — determines the multiplier applied to the grid weight.')"
        />

        <!-- Only range codes (F4: 6–10) take a weight: the server ignores any
             value sent for a fixed code, so none is offered. -->
        <FormControl
          v-if="selectedIsRange"
          type="number"
          step="0.25"
          :min="selectedCode?.min_weight"
          :max="selectedCode?.max_weight"
          :label="__('Estimated weight')"
          v-model="form.base_weight"
          :required="true"
          :placeholder="selectedCode ? gridWeightLabel(selectedCode) : ''"
          :description="rangeHint"
        />
        <p
          v-if="selectedIsRange && form.base_weight !== '' && weightError"
          class="text-ink-red-4 text-xs -mt-2"
        >
          {{ weightError }}
        </p>

        <div class="space-y-2">
          <FormControl
            type="checkbox"
            :label="__('Regularisation')"
            v-model="form.is_regularisation"
          />
          <FormControl
            type="checkbox"
            :label="__('On-site intervention')"
            v-model="form.onsite"
          />
          <FormControl
            v-if="form.onsite"
            type="number"
            :label="__('Travel fee')"
            v-model="form.travel_fee"
          />
          <!-- art. 6.4: reserved to the support manager -->
          <FormControl
            v-if="isManager"
            type="checkbox"
            :label="__('Unfounded P1 (manager only)')"
            v-model="form.unfounded_p1"
          />
        </div>

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Announce')"
          :loading="submitting"
          :disabled="!form.grid_code || Boolean(weightError)"
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
  rangeHintText,
  rangeWeightError,
  weightParam,
} from "./grid";
import type { GridCode, ResponsibilityLayer } from "./types";

const props = defineProps<{
  ticket: string;
  isManager: boolean;
  grid: GridCode[];
  layers: ResponsibilityLayer[];
}>();

const emit = defineEmits<{ announced: [] }>();
const show = defineModel<boolean>({ required: true });

const submitting = ref(false);
const errorMessage = ref("");

const blank = () => ({
  grid_code: "",
  responsibility_layer: "",
  base_weight: "" as string | number,
  is_regularisation: false,
  unfounded_p1: false,
  onsite: false,
  travel_fee: "" as string | number,
  intervention_at: "",
});
const form = reactive(blank());

type MultiplierPreview = { intervention_at: string; working_hours: boolean; multiplier: number };
const preview = ref<MultiplierPreview | null>(null);

// "2026-09-24 10:15:00.123" (server) <-> "2026-09-24T10:15" (datetime-local).
// Both are naive times of the server's timezone: no conversion.
function toInputValue(value: string): string {
  return (value || "").replace(" ", "T").slice(0, 16);
}
function toServerValue(value: string): string | null {
  if (!value) return null;
  const v = value.replace("T", " ");
  return v.length === 16 ? `${v}:00` : v;
}

let previewSeq = 0;
async function loadPreview(value: string | null) {
  const seq = ++previewSeq;
  try {
    const res = await call("kb_credits.api.intervention_multiplier", {
      ticket: props.ticket,
      intervention_at: value,
    });
    if (seq !== previewSeq) return;
    preview.value = res;
    if (!value && res?.intervention_at && !form.intervention_at) {
      form.intervention_at = toInputValue(res.intervention_at);
    }
  } catch {
    if (seq === previewSeq) preview.value = null;
  }
}

// reset every time the dialog opens, so a cancelled attempt never leaks into the next
watch(show, (open) => {
  if (open) {
    Object.assign(form, blank());
    errorMessage.value = "";
    preview.value = null;
    // prefilled with the server's "now": an immediate intervention
    loadPreview(null);
  }
});

watch(
  () => form.intervention_at,
  (value) => {
    if (show.value && value) loadPreview(toServerValue(value));
  }
);

const gridOptions = computed(() => [
  { label: __("Select a code"), value: "" },
  ...props.grid.map((g) => ({ label: gridOptionLabel(g), value: g.code })),
]);

const layerOptions = computed(() => [
  { label: __("Not specified"), value: "" },
  ...props.layers.map((l) => ({
    label: `${l.label} (×${formatCredits(l.factor)})`,
    value: l.layer,
  })),
]);

const selectedCode = computed(() =>
  props.grid.find((g) => g.code === form.grid_code)
);
const selectedIsRange = computed(() => isRange(selectedCode.value));
const isFreeCode = computed(() => Boolean(selectedCode.value?.is_free));

// a value typed for a range code must not leak onto the next code picked
watch(
  () => form.grid_code,
  () => {
    form.base_weight = "";
  }
);

const weightError = computed(() =>
  rangeWeightError(selectedCode.value, form.base_weight)
);

const rangeHint = computed(() => rangeHintText(selectedCode.value));

async function submit() {
  if (weightError.value) {
    errorMessage.value = weightError.value;
    return;
  }
  submitting.value = true;
  errorMessage.value = "";
  try {
    const res = await call("kb_credits.api.announce", {
      ticket: props.ticket,
      grid_code: form.grid_code,
      base_weight: weightParam(selectedCode.value, form.base_weight),
      responsibility_layer: form.responsibility_layer || null,
      is_regularisation: form.is_regularisation ? 1 : 0,
      unfounded_p1: form.unfounded_p1 ? 1 : 0,
      onsite: form.onsite ? 1 : 0,
      travel_fee: form.travel_fee === "" ? 0 : form.travel_fee,
      intervention_at: toServerValue(form.intervention_at),
    });
    // C5 / F5: a quote-only code, or an estimate above the quote threshold,
    // is not an announcement at all — say so rather than "0 credit(s)"
    if (res?.status === "Sur devis") {
      toast.success(__("Ticket put on quote — no credits will be consumed."));
    } else {
      toast.success(
        __("Announced: {0} credit(s)").replace(
          "{0}",
          formatCredits(res?.announced_weight ?? 0)
        )
      );
    }
    show.value = false;
    emit("announced");
  } catch (e: any) {
    // server-side permission and article-rule errors are meaningful to the agent
    errorMessage.value = e?.messages?.join(", ") || e?.message || String(e);
  } finally {
    submitting.value = false;
  }
}
</script>
