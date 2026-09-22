<template>
  <div class="filter-bar">
    <slot />
    <div class="filter-bar-meta">
      <span v-if="dirty && count !== null && total !== null" class="meta mono">筛选 {{ count }} / {{ total }}</span>
      <el-button v-if="dirty" size="mini" type="text" icon="el-icon-refresh-left" @click="$emit('reset')">重置</el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FilterBar',
  props: {
    count: { type: Number, default: null },
    total: { type: Number, default: null },
    dirty: { type: Boolean, default: false },
  },
};
</script>
