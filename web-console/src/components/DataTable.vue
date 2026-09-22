<template>
  <div class="data-table-wrap">
    <div v-if="loading" class="data-table-loading">正在加载...</div>
    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key" :style="column.style">{{ column.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, rowIndex) in rows" :key="rowKey(row, rowIndex)" @click="$emit('row-click', row)">
          <td v-for="column in columns" :key="column.key" :style="column.style">
            <slot :name="`cell-${column.key}`" :row="row" :index="rowIndex">
              <span :class="{ mono: column.mono }">{{ display(row, column) }}</span>
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !rows.length" class="empty-state">{{ emptyText }}</div>
  </div>
</template>

<script>
export default {
  name: 'DataTable',
  props: {
    columns: { type: Array, default: () => [] },
    rows: { type: Array, default: () => [] },
    loading: Boolean,
    emptyText: { type: String, default: '暂无数据' },
    rowKeyField: { type: String, default: 'id' },
  },
  methods: {
    rowKey(row, index) { return row[this.rowKeyField] || row.id || row.code || index; },
    display(row, column) {
      const value = column.value ? column.value(row) : row[column.key];
      return value === undefined || value === null || value === '' ? '-' : value;
    },
  },
};
</script>
