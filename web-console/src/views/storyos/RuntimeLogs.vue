<template>
  <section class="console-page">
    <PageHeading title="运行日志"><el-button size="small" icon="el-icon-refresh" :loading="loading" @click="load">刷新</el-button></PageHeading>
    <section class="data-panel">
      <PanelHeader title="事件流" :meta="errorMessage || `${rows.length} 条记录`" />
      <FilterBar :count="filteredRows.length" :total="rows.length" :dirty="filtersActive" @reset="resetFilters">
        <el-input v-model="episodeId" size="small" clearable placeholder="剧集编号" @keyup.enter.native="load" />
        <el-button size="small" icon="el-icon-search" :loading="loading" @click="load">查询</el-button>
        <el-select v-model="filters.eventType" size="small" clearable placeholder="全部事件类型">
          <el-option v-for="item in eventTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.aggregateType" size="small" clearable placeholder="全部聚合类型">
          <el-option v-for="item in aggregateTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </FilterBar>
      <DataTable :columns="columns" :rows="filteredRows" :loading="loading" :empty-text="errorMessage || '暂无事件记录'">
        <template #cell-occurred_at="{ row }"><span class="mono">{{ row.occurred_at || '-' }}</span></template>
        <template #cell-aggregate_id="{ row }"><span class="mono">{{ row.aggregate_id || '-' }}</span></template>
        <template #cell-trace_id="{ row }"><span class="mono">{{ row.trace_id || '-' }}</span></template>
      </DataTable>
    </section>
  </section>
</template>
<script>
import PageHeading from '../../components/PageHeading.vue';
import PanelHeader from '../../components/PanelHeader.vue';
import FilterBar from '../../components/FilterBar.vue';
import DataTable from '../../components/DataTable.vue';
import { platformApi } from '../../api/platform';
import { distinctOptions, anyFilter } from '../../utils/filter';

export default {
  name: 'RuntimeLogs',
  components: { PageHeading, PanelHeader, FilterBar, DataTable },
  data() { return { rows: [], episodeId: '', filters: { eventType: '', aggregateType: '' }, loading: false, errorMessage: '' }; },
  computed: {
    columns() { return [{ key: 'occurred_at', label: '发生时间' }, { key: 'event_type', label: '事件' }, { key: 'aggregate_id', label: '聚合 ID' }, { key: 'trace_id', label: '链路 ID' }]; },
    eventTypeOptions() { return distinctOptions(this.rows, 'event_type'); },
    aggregateTypeOptions() { return distinctOptions(this.rows, 'aggregate_type'); },
    filteredRows() { return this.rows.filter((row) => (!this.filters.eventType || row.event_type === this.filters.eventType) && (!this.filters.aggregateType || row.aggregate_type === this.filters.aggregateType)); },
    filtersActive() { return anyFilter(this.filters) || Boolean(this.episodeId.trim()); },
  },
  created() { this.load(); },
  methods: {
    load() { this.loading = true; this.errorMessage = ''; platformApi.events(50, 0, this.episodeId).then((body) => { this.rows = body.items || []; }).catch((error) => { this.rows = []; this.errorMessage = `读取失败：${error.message}`; }).finally(() => { this.loading = false; }); },
    resetFilters() { this.episodeId = ''; this.filters = { eventType: '', aggregateType: '' }; this.load(); },
  },
};
</script>
