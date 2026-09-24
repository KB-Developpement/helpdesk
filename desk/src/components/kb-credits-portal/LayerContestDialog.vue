<template>
  <!-- Convention art. 4.2: the layer is contested on a precise technical
       element, within 5 working days. Both are enforced server-side. -->
  <Dialog
    v-model="show"
    :options="{ title: __('Contest the responsibility layer'), size: 'lg' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "The layer says where the malfunction comes from and changes what is counted: a customisation delivered by KB costs 0 credits, a core / customisation interaction 50% of the weight."
            )
          }}
        </p>
        <p v-if="q?.responsibility_layer" class="text-p-sm text-ink-gray-6">
          {{ __("Current layer: {0}", q.responsibility_layer) }}
        </p>

        <FormControl
          type="select"
          :label="__('Layer you consider applicable')"
          v-model="newLayer"
          :options="layerOptions"
          :disabled="loadingLayers"
        />

        <FormControl
          type="textarea"
          :label="__('Technical element')"
          :placeholder="
            __(
              'Reference instance test, log extract, audit trail… Describe precisely what shows the origin of the problem.'
            )
          "
          :rows="5"
          v-model="evidence"
          :required="true"
        />

        <ErrorMessage :message="errorMessage" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" :disabled="submitting" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Send the contest')"
          :loading="submitting"
          :disabled="!newLayer || !evidence.trim()"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Button, call, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui";
import { computed, ref, watch } from "vue";
import type { LayerOption, PortalQualification } from "./types";
import { errorText, formatCredits } from "./utils";

const props = defineProps<{ q: PortalQualification | null }>();
const emit = defineEmits<{ done: [] }>();
const show = defineModel<boolean>({ required: true });

const layers = ref<LayerOption[]>([]);
const loadingLayers = ref(false);
const newLayer = ref("");
const evidence = ref("");
const submitting = ref(false);
const errorMessage = ref("");

watch(show, async (open) => {
  if (!open) return;
  newLayer.value = "";
  evidence.value = "";
  errorMessage.value = "";
  if (layers.value.length) return;
  loadingLayers.value = true;
  try {
    layers.value = (await call("kb_credits.api.get_responsibility_layers")) || [];
  } catch (e) {
    errorMessage.value = errorText(e);
  } finally {
    loadingLayers.value = false;
  }
});

const layerOptions = computed(() => [
  { label: __("Select a layer"), value: "" },
  ...layers.value
    .filter((l) => l.layer !== props.q?.responsibility_layer)
    .map((l) => ({
      label: `${l.label} (× ${formatCredits(l.factor)})`,
      value: l.layer,
    })),
]);

async function submit() {
  if (!props.q || !newLayer.value || !evidence.value.trim()) return;
  submitting.value = true;
  errorMessage.value = "";
  try {
    await call("kb_credits.api.contest_layer", {
      qualification_name: props.q.name,
      new_layer: newLayer.value,
      evidence: evidence.value.trim(),
    });
    toast.success(__("Your contest has been recorded and the Support Manager notified."));
    show.value = false;
    emit("done");
  } catch (e) {
    errorMessage.value = errorText(e);
  } finally {
    submitting.value = false;
  }
}
</script>
