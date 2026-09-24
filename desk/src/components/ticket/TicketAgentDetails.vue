<template>
  <div class="flex flex-col gap-3 border-b px-6 py-3">
    <div
      v-for="s in sections"
      :key="s.label"
      class="flex items-center text-base leading-5"
    >
      <Tooltip :text="s.label">
        <div class="w-[126px] text-sm text-ink-gray-5">{{ s.label }}</div>
      </Tooltip>
      <div class="flex items-center justify-between">
        <div v-if="s.value">{{ s.value }}</div>
        <Tooltip :text="s.tooltipValue">
          <Badge
            v-if="s.badgeText"
            class="-ml-1"
            :label="s.badgeText"
            variant="subtle"
            :theme="s.badgeColor"
          />
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import {
  dateFormat,
  dateTooltipFormat,
  formatTime,
} from "@/utils";
import { Badge, dayjs, Tooltip } from "frappe-ui";
import { computed, onUnmounted, ref, watch } from "vue";

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

let firstResponseInterval = null;
let resolutionInterval = null;

const firstResponseSeconds = ref(0);
const resolutionSeconds = ref(0);

const firstResponseBadge = computed(() => {
  let firstResponse = null;
  if (
    !props.ticket.first_responded_on &&
    dayjs().isBefore(dayjs(props.ticket.response_by))
  ) {
    // KB : secondes calculées directement — l'aller-retour texte → secondes
    // perdait les jours depuis que formatTime est traduit (« 4j » et non « 4d »)
    let responseBy = dayjs(props.ticket.response_by).diff(dayjs(), "s");
    if (firstResponseInterval) {
      clearInterval(firstResponseInterval);
      firstResponseInterval = null;
    }
    handleFirstResponseInterval(responseBy);
    firstResponse = {
      label: __("Due in {0}", formatTime(firstResponseSeconds.value)),
      color: "orange",
    };
  } else if (
    dayjs(props.ticket.first_responded_on).isBefore(
      dayjs(props.ticket.response_by)
    )
  ) {
    firstResponse = {
      label: __("Fulfilled in {0}", formatTime(
        dayjs(props.ticket.first_responded_on).diff(
          dayjs(props.ticket.creation),
          "s"
        )
      )),
      color: "green",
    };
  } else {
    firstResponse = {
      label: __("Failed"),
      color: "red",
    };
  }
  return firstResponse;
});

const resolutionBadge = computed(() => {
  let resolution = null;
  if (resolutionInterval) {
    clearInterval(resolutionInterval);
  }
  if (
    props.ticket.status_category === "Paused" &&
    props.ticket.on_hold_since &&
    dayjs(props.ticket.resolution_by).isAfter(dayjs(props.ticket.on_hold_since))
  ) {
    let timeLeft = dayjs(props.ticket.resolution_by).diff(dayjs(), "s");
    resolution = {
      label: __("{0} left (On Hold)", formatTime(timeLeft)),
      color: "blue",
    };
  } else if (
    !props.ticket.resolution_date &&
    dayjs().isBefore(props.ticket.resolution_by)
  ) {
    let resolutionBy = dayjs(props.ticket.resolution_by).diff(dayjs(), "s");
    handleResolutionInterval(resolutionBy);

    resolution = {
      label: __("Due in {0}", formatTime(resolutionSeconds.value)),
      color: "orange",
    };
  } else if (props.ticket.agreement_status === "Fulfilled") {
    resolution = {
      label: __("Fulfilled in {0}", formatTime(
        dayjs(props.ticket.resolution_time, "s")
      )),
      color: "green",
    };
  } else {
    resolution = {
      label: __("Failed"),
      color: "red",
    };
  }
  return resolution;
});

function getCalculatedResolution() {
  let resolution = dayjs(props.ticket.resolution_by).add(
    props.ticket.total_hold_time,
    "s"
  );
  // let now = new Date()
  resolution = dayjs(resolution).diff(dayjs(), "s");
  return formatTime(resolution);
}

const sections = computed(() => [
  {
    label: __("First Response"),
    tooltipValue: dateFormat(props.ticket.response_by, dateTooltipFormat),
    badgeText: firstResponseBadge.value.label,
    badgeColor: firstResponseBadge.value.color,
  },
  {
    label: __("Resolution"),
    tooltipValue: dateFormat(
      props.ticket.resolution_date || props.ticket.resolution_by,
      dateTooltipFormat
    ),
    badgeText: resolutionBadge.value.label,
    badgeColor: resolutionBadge.value.color,
  },
  {
    label: __("Source"),
    value: props.ticket.via_customer_portal ? __("Portal") : __("Mail"),
  },
]);

// Watch for status changes and clear intervals
watch(
  () => props.ticket,
  (ticket: any) => {
    if (ticket.status_category !== "Open") {
      if (firstResponseInterval) {
        clearInterval(firstResponseInterval);
        firstResponseInterval = null;
      }
      if (resolutionInterval) {
        clearInterval(resolutionInterval);
        resolutionInterval = null;
      }
    }
  },
  { deep: true, immediate: true }
);

function handleFirstResponseInterval(seconds: number) {
  if (!seconds || seconds <= 0) return;
  if (props.ticket.status_category !== "Open") {
    return;
  }
  firstResponseSeconds.value = seconds;
  firstResponseInterval = setInterval(() => {
    if (firstResponseSeconds.value <= 0) {
      clearInterval(firstResponseInterval);
      return;
    }
    firstResponseSeconds.value--;
  }, 1000);
}

function handleResolutionInterval(seconds: number) {
  if (!seconds || seconds <= 0) return;
  if (props.ticket.status_category !== "Open") {
    return;
  }

  resolutionSeconds.value = seconds;
  resolutionInterval = setInterval(() => {
    if (resolutionSeconds.value <= 0) {
      clearInterval(resolutionInterval);
      return;
    }
    resolutionSeconds.value--;
  }, 1000);
}

onUnmounted(() => {
  if (firstResponseInterval) {
    clearInterval(firstResponseInterval);
  }
  if (resolutionInterval) {
    clearInterval(resolutionInterval);
  }
  firstResponseInterval = null;
  resolutionInterval = null;
});
</script>
