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

        <p v-if="selectedCode" class="text-ink-gray-5 text-xs -mt-2">
          {{ __("Grid weight") }}: {{ selectedCode.base_weight }}
          <template v-if="selectedCode.category">
            · {{ selectedCode.category }}
          </template>
        </p>

        <FormControl
          type="select"
          :label="__('Responsibility layer')"
          v-model="form.responsibility_layer"
          :options="layerOptions"
          :description="__('Article 4 — determines the multiplier applied to the grid weight.')"
        />

        <FormControl
          type="number"
          step="0.25"
          :label="__('Override base weight (optional)')"
          v-model="form.base_weight"
          :placeholder="selectedCode ? String(selectedCode.base_weight) : ''"
          :description="__('Leave empty to use the grid weight.')"
        />

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
          :disabled="!form.grid_code"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, call, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui";
import { computed, reactive, ref, watch } from "vue";
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
});
const form = reactive(blank());

// reset every time the dialog opens, so a cancelled attempt never leaks into the next
watch(show, (open) => {
  if (open) {
    Object.assign(form, blank());
    errorMessage.value = "";
  }
});

const gridOptions = computed(() => [
  { label: __("Select a code"), value: "" },
  ...props.grid.map((g) => ({
    label: `${g.code} — ${g.label} (${g.base_weight})`,
    value: g.code,
  })),
]);

const layerOptions = computed(() => [
  { label: __("Not specified"), value: "" },
  ...props.layers.map((l) => ({
    label: `${l.label} (×${l.factor})`,
    value: l.layer,
  })),
]);

const selectedCode = computed(() =>
  props.grid.find((g) => g.code === form.grid_code)
);

async function submit() {
  submitting.value = true;
  errorMessage.value = "";
  try {
    const res = await call("kb_credits.api.announce", {
      ticket: props.ticket,
      grid_code: form.grid_code,
      base_weight: form.base_weight === "" ? null : form.base_weight,
      responsibility_layer: form.responsibility_layer || null,
      is_regularisation: form.is_regularisation ? 1 : 0,
      unfounded_p1: form.unfounded_p1 ? 1 : 0,
      onsite: form.onsite ? 1 : 0,
      travel_fee: form.travel_fee === "" ? 0 : form.travel_fee,
    });
    toast.success(
      __("Announced: {0} credit(s)").replace(
        "{0}",
        String(res?.announced_weight ?? "")
      )
    );
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
