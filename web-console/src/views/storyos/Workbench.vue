<template>
  <section class="console-page">
    <PageHeading title="生产工作台" />
    <div class="workbench-grid"><section class="data-panel"><PanelHeader title="生产队列" meta="当前任务" /><div v-if="!queue.length" class="empty-state">暂无生产任务</div><div v-for="item in queue" :key="item.id" class="queue-row"><div><strong>{{ item.title }}</strong><span class="meta">{{ item.frames }}</span></div><StatusDot :label="item.status" :tone="item.tone" /></div></section><section class="data-panel"><PanelHeader title="审核合同" /><div class="contract-lines"><div><span>视觉锁定</span><strong>1 + 3</strong></div><div><span>帧合同</span><strong>SHA 绑定</strong></div><div><span>状态权威</span><strong>episode-state.json</strong></div><div><span>图片质量</span><strong>高</strong></div></div></section></div>
  </section>
</template>
<script>
import PageHeading from '../../components/PageHeading.vue';
import PanelHeader from '../../components/PanelHeader.vue';
import StatusDot from '../../components/StatusDot.vue';
export default { name: 'Workbench', components: { PageHeading, PanelHeader, StatusDot }, data() { return { queue: [] }; } };
</script>
