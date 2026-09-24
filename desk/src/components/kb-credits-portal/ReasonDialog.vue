<template>
  <!-- Generic "write a reason and submit" dialog: weight contest, statement
       contest. The server call is passed in so errors stay in the dialog. -->
  <Dialog v-model="show" :options="{ title, size: 'lg' }">
    <template #body-content>
      <div class="space-y-4">
        <p v-if="intro" class="text-p-base text-ink-gray-7">{{ intro }}</p>
        <FormControl
          type="textarea"
          :label="label"
          :placeholder="placeholder"
          :rows="5"
          v-model="reason"
          :required="true"
        />
        <p v-if="hint" class="text-p-sm text-ink-gray-5">{{ hint }}</p>
        <ErrorMessage :message="errorMessage" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" :disabled="submitting" @click="show = false" />
        <Button
          variant="solid"
          theme="red"
          :label="submitLabel"
          :loading="submitting"
          :disabled="!reason.trim()"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, Dialog, ErrorMessage, FormControl } from "frappe-ui";
import { ref, watch } from "vue";
import { errorText } from "./utils";

const props = defineProps<{
  title: string;
  label: string;
  submitLabel: string;
  action: (reason: string) => Promise<unknown>;
  intro?: string;
  hint?: string;
  placeholder?: string;
}>();

const emit = defineEmits<{ done: [] }>();
const show = defineModel<boolean>({ required: true });

const reason = ref("");
const submitting = ref(false);
const errorMessage = ref("");

watch(show, (open) => {
  if (open) {
    reason.value = "";
    errorMessage.value = "";
  }
});

async function submit() {
  const text = reason.value.trim();
  if (!text) return;
  submitting.value = true;
  errorMessage.value = "";
  try {
    await props.action(text);
    show.value = false;
    emit("done");
  } catch (e) {
    errorMessage.value = errorText(e);
  } finally {
    submitting.value = false;
  }
}
</script>
