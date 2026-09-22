<template>
  <section class="console-page">
    <PageHeading title="设置" />
    <section class="settings-panel"><div class="settings-row"><div><strong>侧边栏默认折叠</strong><p>适合窄屏或只关注主工作区时使用。</p></div><el-switch v-model="$store.state.app.sidebarCollapsed" @change="toggleSidebar" /></div><div class="settings-row"><div><strong>认证模式</strong><p>{{ authMode === 'local' ? '本地登录' : '远程接口' }}</p></div><span class="mono">{{ authMode === 'local' ? '本地登录' : '远程接口' }}</span></div><div class="settings-row"><div><strong>当前用户</strong><p>{{ userName }}</p></div><el-button size="small" @click="logout">退出登录</el-button></div></section>
  </section>
</template>
<script>
import PageHeading from '../components/PageHeading.vue';
import { appConfig } from '../config/app';
export default { name: 'Settings', components: { PageHeading }, computed: { authMode() { return appConfig.authMode; }, userName() { return this.$store.state.auth.user?.username || '-'; } }, methods: { toggleSidebar(value) { if (value !== this.$store.state.app.sidebarCollapsed) this.$store.commit('app/TOGGLE_SIDEBAR'); }, logout() { this.$store.dispatch('auth/logout'); this.$router.replace('/login'); } } };
</script>
