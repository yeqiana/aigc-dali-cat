<template><span class="status-label"><i class="status-dot" :class="tone" />{{ displayLabel }}</span></template>

<script>
import { statusLabel } from '../utils/status';

export default {
  props: { label: { type: String, required: true }, tone: { type: String, default: 'neutral' } },
  computed: {
    displayLabel() {
      return statusLabel(this.label);
    },
  },
};
</script>
