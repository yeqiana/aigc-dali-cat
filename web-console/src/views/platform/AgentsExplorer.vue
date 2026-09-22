<template>
  <section class="console-page">
    <PageHeading title="智能体"><el-button size="small" icon="el-icon-refresh" :loading="loading" @click="load">刷新</el-button></PageHeading>
    <section class="data-panel"><DataTable :columns="columns" :rows="rows" :loading="loading" :empty-text="errorMessage || '暂无智能体记录'"><template #cell-agent_code="{ row }"><span class="mono">{{ row.agent_code }}</span></template></DataTable></section>
  </section>
</template>
<script>
import PageHeading from '../../components/PageHeading.vue';
import DataTable from '../../components/DataTable.vue';
import { platformApi } from '../../api/platform';
export default {
  name: 'AgentsExplorer', components: { PageHeading, DataTable },
  data() { return { rows: [], loading: false, errorMessage: '' }; },
  computed: { columns() { return [{ key: 'agent_code', label: '智能体编码' }, { key: 'agent_name', label: '名称' }, { key: 'agent_type', label: '类型' }, { key: 'status', label: '状态' }, { key: 'description', label: '说明' }]; } },
  created() { this.load(); },
  methods: { load() { this.loading = true; this.errorMessage = ''; platformApi.agents().then((body) => { this.rows = Array.isArray(body) ? body : body.items || []; }).catch((error) => { this.rows = []; this.errorMessage = `正式接口未提供智能体列表：${error.message}`; }).finally(() => { this.loading = false; }); } },
};
</script>
