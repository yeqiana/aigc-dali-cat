<template><section class="console-page"><PageHeading title="执行记录" /><section class="query-panel"><el-input v-model="query" size="small" clearable placeholder="输入执行编号" @keyup.enter.native="load" /><el-button size="small" type="primary" :loading="loading" @click="load">查询</el-button></section><section v-if="record" class="data-panel json-panel"><PanelHeader :title="record.execution_id || query"><StatusDot :label="record.status || 'UNKNOWN'" :tone="record.status === 'COMPLETED' ? 'success' : 'warning'" /></PanelHeader><pre>{{ pretty(record) }}</pre></section><div v-if="errorMessage" class="error-panel">{{ errorMessage }}</div></section></template>
<script>
import PageHeading from '../../components/PageHeading.vue';
import PanelHeader from '../../components/PanelHeader.vue';
import StatusDot from '../../components/StatusDot.vue';
import { platformApi } from '../../api/platform';
export default { name: 'ExecutionExplorer', components: { PageHeading, PanelHeader, StatusDot }, data() { return { query: '', record: null, loading: false, errorMessage: '' }; }, methods: { load() { if (!this.query.trim()) { this.errorMessage = '请输入执行编号'; return; } this.loading = true; this.errorMessage = ''; platformApi.execution(this.query.trim()).then((body) => { this.record = body; }).catch((error) => { this.record = null; this.errorMessage = `查询失败：${error.message}`; }).finally(() => { this.loading = false; }); }, pretty(value) { return JSON.stringify(value, null, 2); } } };
</script>
