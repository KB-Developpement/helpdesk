<template>
  <FormControl
    v-if="filter.type == 'Check'"
    :label="__(filter.label)"
    type="checkbox"
    :checked="props.value"
    @change.stop="updateFilter(filter, $event.target.checked)"
    class="w-36"
  />
  <FormControl
    v-else-if="filter.type === 'Select'"
    class="form-control cursor-pointer [&_select]:cursor-pointer w-36"
    type="select"
    :model-value="props.value || undefined"
    :options="(filter.options || []).map((o) => ({ ...o, label: __(o.label) }))"
    :placeholder="__(filter.label)"
    @update:modelValue="(v) => updateFilter(filter, v || '')"
  />
  <Link
    v-else-if="filter.type === 'Link'"
    :value="props.value"
    :doctype="filter.options"
    :placeholder="__(filter.label)"
    @change="(data) => updateFilter(filter, data)"
    class="w-36"
  />
  <component
    v-else-if="['Date', 'Datetime'].includes(filter.type)"
    class="border-none w-36"
    :is="filter.type === 'Date' ? DatePicker : DateTimePicker"
    :value="props.value"
    @change="(v) => updateFilter(filter, v)"
    :placeholder="__(filter.label)"
  />
  <TextInput
    v-else
    :value="props.value"
    type="text"
    :placeholder="__(filter.label)"
    @input.stop="debouncedFn(filter, $event.target.value)"
  />
</template>
<script setup>
import { Link } from "@/components";
import { useDebounceFn } from "@vueuse/core";
import { DatePicker, DateTimePicker, FormControl, TextInput } from "frappe-ui";

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
  value: {
    type: [String, Boolean],
    required: true,
  },
});

const emit = defineEmits(["applyQuickFilter"]);

const debouncedFn = useDebounceFn((f, value) => {
  emit("applyQuickFilter", f, value);
}, 500);

function updateFilter(f, value) {
  emit("applyQuickFilter", f, value);
}
</script>
