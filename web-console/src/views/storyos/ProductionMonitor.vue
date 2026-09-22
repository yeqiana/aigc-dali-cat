<template>
  <section class="console-page">
    <PageHeading title="生产监控">
      <el-button size="small" icon="el-icon-refresh" :loading="loading" @click="load">刷新</el-button>
    </PageHeading>
    <div class="status-strip">
      <div><span>运行中</span><strong class="mono">{{ count(runningCount) }}</strong></div>
      <div><span>待处理</span><strong class="mono">{{ count(pendingCount) }}</strong></div>
      <div><span>已完成</span><strong class="mono">{{ count(completedCount) }}</strong></div>
      <div><span>阻塞</span><strong class="mono danger-text">{{ count(blockedCount) }}</strong></div>
    </div>
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
      <DataTable :columns="columns" :rows="filteredRows" :loading="loading" :empty-text="errorMessage || '暂无运行记录'" @row-click="openEpisode">
        <template #cell-title="{ row }"><div class="primary-cell"><strong>{{ row.title }}</strong><span class="mono">{{ row.code }}</span></div></template>
        <template #cell-currentStage="{ row }"><StatusDot :label="row.currentStage" :tone="runtimeTone(row.currentStage)" /></template>
        <template #cell-executionStatus="{ row }"><StatusDot :label="row.executionStatus" :tone="runtimeTone(row.executionStatus)" /></template>
        <template #cell-progress="{ row }"><div class="progress-cell"><el-progress :percentage="progress(row)" :show-text="false" :stroke-width="4" /><span class="mono">{{ row.completedFrames }}/{{ row.totalFrames || '-' }}</span></div></template>
      </DataTable>
    </section>
    <el-drawer :visible.sync="drawerVisible" size="520px" :with-header="false">
      <div v-if="selected" class="drawer-content">
        <div class="drawer-header">
          <div class="drawer-heading"><span class="mono drawer-code">{{ selected.code }}</span><h2>{{ selected.title }}</h2></div>
          <el-button class="drawer-close" size="mini" icon="el-icon-close" aria-label="关闭详情" @click="drawerVisible = false" />
        </div>
        <section class="drawer-section">
          <div class="drawer-section-title"><span>进度节点</span><span class="mono meta">{{ selected.currentStage }}</span></div>
          <el-steps direction="vertical" :active="currentStageIndex" finish-status="success" class="node-steps">
            <el-step v-for="(stage, index) in progressStages" :key="stage.code">
              <span slot="title" class="node-title">{{ stage.label }}<em v-if="index === currentStageIndex" class="node-current">当前</em></span>
              <span slot="description" class="node-code mono">{{ stage.code }}</span>
            </el-step>
          </el-steps>
          <p v-if="currentStageIndex < 0" class="drawer-hint">当前阶段不在标准节点内，未高亮进度。</p>
        </section>
        <section class="drawer-section">
          <div class="drawer-section-title"><span>运行详情</span></div>
          <dl class="detail-list">
            <div><dt>当前阶段</dt><dd><StatusDot :label="selected.currentStage" :tone="runtimeTone(selected.currentStage)" /></dd></div>
            <div><dt>执行状态</dt><dd><StatusDot :label="selected.executionStatus" :tone="runtimeTone(selected.executionStatus)" /></dd></div>
            <div><dt>当前动作</dt><dd>{{ selected.currentAction }}</dd></div>
            <div><dt>帧进度</dt><dd><span class="progress-cell detail-progress"><el-progress :percentage="progress(selected)" :show-text="false" :stroke-width="4" /><span class="mono">{{ selected.completedFrames }}/{{ selected.totalFrames || '-' }}</span></span></dd></div>
            <div><dt>更新时间</dt><dd class="mono">{{ selected.updatedAt }}</dd></div>
            <div><dt>状态来源</dt><dd>{{ selected.source }}</dd></div>
          </dl>
        </section>
      </div>
    </el-drawer>
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
import { progressStages, stageIndex } from '../../config/progress';

export default {
  name: 'ProductionMonitor',
  components: { PageHeading, PanelHeader, FilterBar, StatusDot, DataTable },
  data() { return { rows: [], totalCount: 0, hasMore: false, keyword: '', filters: { stage: '', status: '' }, loading: false, errorMessage: '', drawerVisible: false, selected: null, progressStages }; },
  computed: {
    columns() { return [{ key: 'title', label: '剧集' }, { key: 'currentStage', label: '阶段' }, { key: 'executionStatus', label: '执行状态' }, { key: 'progress', label: '帧进度' }, { key: 'updatedAt', label: '更新时间' }]; },
    listMeta() { return formatListMeta(this.rows.length, this.totalCount, this.hasMore); },
    stageOptions() { return distinctOptions(this.rows, 'currentStage', statusLabel); },
    statusOptions() { return distinctOptions(this.rows, 'executionStatus', statusLabel); },
    filteredRows() { return this.rows.filter((row) => (!this.filters.stage || row.currentStage === this.filters.stage) && (!this.filters.status || row.executionStatus === this.filters.status) && keywordMatch(row, ['title', 'code'], this.keyword)); },
    filtersActive() { return anyFilter(this.filters) || Boolean(this.keyword.trim()); },
    runningCount() { return this.rows.filter((row) => row.executionStatus === 'RUNNING').length; },
    pendingCount() { return this.rows.filter((row) => ['NEEDS_USER', 'READY', 'HOST_WAIT', 'CAPABILITY_WAIT'].includes(row.executionStatus)).length; },
    completedCount() { return this.rows.filter((row) => ['COMPLETE', 'COMPLETED'].includes(row.executionStatus)).length; },
    blockedCount() { return this.rows.filter((row) => ['BLOCKED', 'HARD_STOP', 'ERROR'].includes(row.executionStatus)).length; },
    currentStageIndex() { return this.selected ? stageIndex(this.selected.currentStage) : -1; },
  },
  created() { this.load(); },
  methods: {
    runtimeTone,
    count(value) { return this.errorMessage ? '-' : value; },
    load() { this.loading = true; this.errorMessage = ''; platformApi.runtimeStatuses(100).then((body) => { this.rows = responseItems(body).map(normalizeRuntimeRow); this.totalCount = Number(body.total || this.rows.length); this.hasMore = Boolean(body.has_more); }).catch((error) => { this.rows = []; this.totalCount = 0; this.hasMore = false; this.errorMessage = `读取失败：${error.message}`; }).finally(() => { this.loading = false; }); },
    progress(row) { return row.totalFrames ? Math.round((row.completedFrames / row.totalFrames) * 100) : 0; },
    resetFilters() { this.keyword = ''; this.filters = { stage: '', status: '' }; },
    openEpisode(row) { this.selected = row; this.drawerVisible = true; },
  },
};
</script>
