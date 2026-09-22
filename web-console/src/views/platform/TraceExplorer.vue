<template>
  <section class="console-page">
    <PageHeading title="链路追踪"><el-button size="small" :loading="loading" icon="el-icon-refresh" @click="load">刷新</el-button></PageHeading>
    <section class="data-panel">
      <FilterBar :count="filteredRows.length" :total="rows.length" :dirty="filtersActive" @reset="resetFilters">
        <el-input v-model="traceId" size="small" clearable placeholder="链路编号" @keyup.enter.native="load" />
        <el-button size="small" icon="el-icon-search" :loading="loading" @click="load">查询</el-button>
        <el-select v-model="filters.status" size="small" clearable placeholder="全部状态">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.operation" size="small" clearable placeholder="全部操作">
          <el-option v-for="item in operationOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </FilterBar>
      <DataTable :columns="columns" :rows="filteredRows" :loading="loading" :empty-text="errorMessage || '暂无链路记录'">
        <template #cell-trace_id="{ row }"><span class="mono">{{ row.trace_id }}</span></template>
        <template #cell-duration_ms="{ row }"><span class="mono">{{ row.duration_ms || '-' }}</span></template>
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
import { statusLabel } from '../../utils/status';

export default {
  name: 'TraceExplorer',
  components: { PageHeading, FilterBar, DataTable },
  data() { return { rows: [], traceId: '', filters: { status: '', operation: '' }, loading: false, errorMessage: '' }; },
  computed: {
    columns() { return [{ key: 'trace_id', label: '链路 ID' }, { key: 'operation', label: '操作' }, { key: 'status', label: '状态' }, { key: 'duration_ms', label: '耗时（毫秒）' }, { key: 'started_at', label: '开始时间' }]; },
    statusOptions() { return distinctOptions(this.rows, 'status', statusLabel); },
    operationOptions() { return distinctOptions(this.rows, 'operation'); },
    filteredRows() { return this.rows.filter((row) => (!this.filters.status || row.status === this.filters.status) && (!this.filters.operation || row.operation === this.filters.operation)); },
    filtersActive() { return anyFilter(this.filters) || Boolean(this.traceId.trim()); },
  },
  created() { this.load(); },
  methods: {
    load() { this.loading = true; this.errorMessage = ''; platformApi.traces(20, 0, '', this.traceId).then((body) => { this.rows = body.items || []; }).catch((error) => { this.rows = []; this.errorMessage = `读取失败：${error.message}`; }).finally(() => { this.loading = false; }); },
    resetFilters() { this.traceId = ''; this.filters = { status: '', operation: '' }; this.load(); },
  },
};
</script>
