<template>
  <div class="app-shell" :class="{ 'is-collapsed': sidebarCollapsed }">
    <Sidebar />
    <div class="app-main">
      <HeaderBar />
      <main class="page-main">
        <transition name="page-fade" mode="out-in">
          <keep-alive :include="cachedViews">
            <router-view :key="$route.fullPath" />
          </keep-alive>
        </transition>
      </main>
      <footer class="app-footer">StoryOS 控制台 <span>·</span> v3.0.0 <span>·</span> 平台服务状态以实时查询为准</footer>
    </div>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue';
import HeaderBar from '../components/HeaderBar.vue';

export default {
  name: 'StoryOSHome',
  components: { Sidebar, HeaderBar },
  computed: {
    sidebarCollapsed() { return this.$store.state.app.sidebarCollapsed; },
    cachedViews() { return []; },
  },
};
</script>
