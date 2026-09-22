<template>
  <section class="console-page">
    <PageHeading title="剧集索引" />
    <section class="data-panel">
      <PanelHeader title="剧集" :meta="listMeta" />
      <FilterBar :count="filteredRows.length" :total="rows.length" :dirty="filtersActive" @reset="resetFilters">
        <el-input v-model="keyword" size="small" clearable prefix-icon="el-icon-search" placeholder="搜索剧集" />
        <el-select v-model="filters.stage" size="small" clearable placeholder="全部阶段">
          <el-option v-for="item in stageOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.status" size="small" clearable placeholder="全部状态">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </FilterBar>
      <DataTable :columns="columns" :rows="filteredRows" :loading="loading" :empty-text="errorMessage || '暂无剧集记录'">
        <template #cell-code="{ row }"><span class="mono">{{ row.code }}</span></template>
        <template #cell-currentStage="{ row }"><StatusDot :label="row.currentStage" :tone="runtimeTone(row.currentStage)" /></template>
        <template #cell-executionStatus="{ row }"><StatusDot :label="row.executionStatus" :tone="runtimeTone(row.executionStatus)" /></template>
      </DataTable>
    </section>
  </section>
</template>

<script>
import PageHeading from '../../components/PageHeading.vue';
import PanelHeader from '../../components/PanelHeader.vue';
import FilterBar from '../../components/FilterBar.vue';
import StatusDot from '../../components/StatusDot.vue';
import DataTable from '../../components/DataTable.vue';
import { platformApi } from '../../api/platform';
import { normalizeRuntimeRow, responseItems, runtimeTone, formatListMeta } from '../../utils/runtime';
import { distinctOptions, keywordMatch, anyFilter } from '../../utils/filter';
import { statusLabel } from '../../utils/status';

export default {
  name: 'Episodes',
  components: { PageHeading, PanelHeader, FilterBar, StatusDot, DataTable },
  data() { return { rows: [], totalCount: 0, hasMore: false, keyword: '', filters: { stage: '', status: '' }, loading: false, errorMessage: '' }; },
  computed: {
    columns() { return [{ key: 'code', label: '编号' }, { key: 'title', label: '名称' }, { key: 'currentStage', label: '阶段' }, { key: 'executionStatus', label: '执行状态' }, { key: 'updatedAt', label: '更新时间' }]; },
    listMeta() { return formatListMeta(this.rows.length, this.totalCount, this.hasMore); },
    stageOptions() { return distinctOptions(this.rows, 'currentStage', statusLabel); },
    statusOptions() { return distinctOptions(this.rows, 'executionStatus', statusLabel); },
    filteredRows() { return this.rows.filter((row) => (!this.filters.stage || row.currentStage === this.filters.stage) && (!this.filters.status || row.executionStatus === this.filters.status) && keywordMatch(row, ['title', 'code'], this.keyword)); },
    filtersActive() { return anyFilter(this.filters) || Boolean(this.keyword.trim()); },
  },
  created() { this.load(); },
  methods: {
    runtimeTone,
    load() { this.loading = true; this.errorMessage = ''; platformApi.runtimeStatuses(100).then((body) => { this.rows = responseItems(body).map(normalizeRuntimeRow); this.totalCount = Number(body.total || this.rows.length); this.hasMore = Boolean(body.has_more); }).catch((error) => { this.rows = []; this.totalCount = 0; this.hasMore = false; this.errorMessage = `读取失败：${error.message}`; }).finally(() => { this.loading = false; }); },
    resetFilters() { this.keyword = ''; this.filters = { stage: '', status: '' }; },
  },
};
</script>
