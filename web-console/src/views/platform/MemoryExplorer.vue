<template>
  <section class="console-page">
    <PageHeading title="记忆检索" />
    <section class="data-panel">
      <FilterBar :count="filteredRows.length" :total="rows.length" :dirty="filtersActive" @reset="resetFilters">
        <el-input v-model="query" size="small" clearable placeholder="输入检索内容" @keyup.enter.native="search" />
        <el-button size="small" type="primary" :loading="loading" @click="search">检索</el-button>
        <el-select v-model="filters.type" size="small" clearable placeholder="全部类型">
          <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.outcome" size="small" clearable placeholder="全部结果">
          <el-option v-for="item in outcomeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </FilterBar>
      <DataTable :columns="columns" :rows="filteredRows" :loading="loading" :empty-text="errorMessage || '请输入关键词开始检索'">
        <template #cell-id="{ row }"><span class="mono">{{ row.id }}</span></template>
      </DataTable>
    </section>
  </section>
</template>
<script>
import PageHeading from '../../components/PageHeading.vue';
import FilterBar from '../../components/FilterBar.vue';
import DataTable from '../../components/DataTable.vue';
import { platformApi } from '../../api/platform';
import { distinctOptions, anyFilter } from '../../utils/filter';

export default {
  name: 'MemoryExplorer',
  components: { PageHeading, FilterBar, DataTable },
  data() { return { query: '', rows: [], filters: { type: '', outcome: '' }, loading: false, errorMessage: '' }; },
  computed: {
    columns() { return [{ key: 'id', label: 'ID' }, { key: 'memory_type', label: '类型' }, { key: 'content', label: '内容' }, { key: 'outcome', label: '结果' }, { key: 'confidence', label: '置信度' }]; },
    typeOptions() { return distinctOptions(this.rows, 'memory_type'); },
    outcomeOptions() { return distinctOptions(this.rows, 'outcome'); },
    filteredRows() { return this.rows.filter((row) => (!this.filters.type || row.memory_type === this.filters.type) && (!this.filters.outcome || row.outcome === this.filters.outcome)); },
    filtersActive() { return anyFilter(this.filters) || Boolean(this.query.trim()); },
  },
  methods: {
    search() { if (!this.query.trim()) { this.errorMessage = '请输入检索内容'; return; } this.loading = true; this.errorMessage = ''; platformApi.memory(this.query.trim()).then((body) => { this.rows = Array.isArray(body) ? body : body.items || []; }).catch((error) => { this.rows = []; this.errorMessage = `检索失败：${error.message}`; }).finally(() => { this.loading = false; }); },
    resetFilters() { this.query = ''; this.rows = []; this.errorMessage = ''; this.filters = { type: '', outcome: '' }; },
  },
};
</script>
