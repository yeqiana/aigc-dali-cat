<template>
  <section class="console-page">
    <PageHeading title="运行状态"><el-button size="small" icon="el-icon-refresh" :loading="loading" @click="load">刷新</el-button></PageHeading>
    <section class="data-panel">
      <PanelHeader title="剧集运行时" :meta="listMeta" />
      <FilterBar :count="filteredRows.length" :total="rows.length" :dirty="filtersActive" @reset="resetFilters">
        <el-input v-model="keyword" size="small" clearable prefix-icon="el-icon-search" placeholder="搜索剧集" />
        <el-select v-model="filters.stage" size="small" clearable placeholder="全部阶段">
          <el-option v-for="item in stageOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.status" size="small" clearable placeholder="全部状态">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.needsUser" size="small" clearable placeholder="全部处理方式">
          <el-option v-for="item in needsUserOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </FilterBar>
      <DataTable :columns="columns" :rows="filteredRows" :loading="loading" :empty-text="errorMessage || '暂无运行状态'">
        <template #cell-episode_ref="{ row }"><span class="mono">{{ row.episode_ref }}</span></template>
        <template #cell-production_stage="{ row }"><StatusDot :label="row.production_stage || 'UNKNOWN'" :tone="runtimeTone(row.production_stage)" /></template>
        <template #cell-execution_status="{ row }"><StatusDot :label="row.execution_status || 'UNKNOWN'" :tone="runtimeTone(row.execution_status)" /></template>
        <template #cell-needs_user="{ row }"><StatusDot :label="row.needs_user ? 'NEEDS_USER' : 'AUTO'" :tone="row.needs_user ? 'danger' : 'success'" /></template>
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
import { runtimeTone, formatListMeta } from '../../utils/runtime';
import { distinctOptions, keywordMatch, anyFilter } from '../../utils/filter';
import { statusLabel } from '../../utils/status';
export default {
  name: 'RuntimeExplorer', components: { PageHeading, PanelHeader, FilterBar, StatusDot, DataTable },
  data() { return { rows: [], totalCount: 0, hasMore: false, keyword: '', filters: { stage: '', status: '', needsUser: '' }, loading: false, errorMessage: '' }; },
  computed: {
    columns() { return [{ key: 'episode_ref', label: '剧集' }, { key: 'title', label: '标题' }, { key: 'production_stage', label: '阶段' }, { key: 'execution_status', label: '执行状态' }, { key: 'current_action', label: '当前动作' }, { key: 'needs_user', label: '人工处理' }]; },
    listMeta() { return this.errorMessage || formatListMeta(this.rows.length, this.totalCount, this.hasMore); },
    stageOptions() { return distinctOptions(this.rows, 'production_stage', statusLabel); },
    statusOptions() { return distinctOptions(this.rows, 'execution_status', statusLabel); },
    needsUserOptions() { return [{ value: 'yes', label: '需要人工' }, { value: 'no', label: '自动处理' }]; },
    filteredRows() { return this.rows.filter((row) => (!this.filters.stage || row.production_stage === this.filters.stage) && (!this.filters.status || row.execution_status === this.filters.status) && (!this.filters.needsUser || (this.filters.needsUser === 'yes') === (row.needs_user === true)) && keywordMatch(row, ['episode_ref', 'title', 'current_action'], this.keyword)); },
    filtersActive() { return anyFilter(this.filters) || Boolean(this.keyword.trim()); },
  },
  created() { this.load(); },
  methods: { runtimeTone, load() { this.loading = true; this.errorMessage = ''; platformApi.runtimeStatuses(100).then((body) => { this.rows = body.items || []; this.totalCount = Number(body.total || this.rows.length); this.hasMore = Boolean(body.has_more); }).catch((error) => { this.rows = []; this.totalCount = 0; this.hasMore = false; this.errorMessage = `读取失败：${error.message}`; }).finally(() => { this.loading = false; }); }, resetFilters() { this.keyword = ''; this.filters = { stage: '', status: '', needsUser: '' }; } },
};
</script>
