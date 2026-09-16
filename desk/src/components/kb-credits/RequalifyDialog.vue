<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Requalify downwards'), size: 'lg' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <p v-if="q" class="text-ink-gray-6 text-sm">
          {{ q.grid_label || q.grid_code }} —
          <span class="tabular-nums">{{ q.announced_weight }}</span>
          {{ __("credit(s) announced") }}
        </p>

        <FormControl
          type="select"
          :label="__('New grid code')"
          v-model="form.new_code"
          :options="gridOptions"
        />

        <FormControl
          type="number"
          step="0.25"
          :label="__('New base weight (optional)')"
          v-model="form.new_base_weight"
          :description="__('Leave empty to use the weight of the new code.')"
        />

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
          :disabled="!form.new_code || !form.note"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, call, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui";
import { computed, reactive, ref, watch } from "vue";
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

const gridOptions = computed(() => [
  { label: __("Select a code"), value: "" },
  ...props.grid.map((g) => ({
    label: `${g.code} — ${g.label} (${g.base_weight})`,
    value: g.code,
  })),
]);

async function submit() {
  if (!props.q) return;
  submitting.value = true;
  errorMessage.value = "";
  try {
    const res = await call("kb_credits.api.requalify", {
      qualification_name: props.q.name,
      new_code: form.new_code,
      note: form.note,
      new_base_weight: form.new_base_weight === "" ? null : form.new_base_weight,
    });
    toast.success(
      __("Requalified: {0} credit(s)").replace("{0}", String(res?.final_weight ?? ""))
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
