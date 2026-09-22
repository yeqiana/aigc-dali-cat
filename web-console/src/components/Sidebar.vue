<template>
  <aside class="app-sidebar">
    <div class="sidebar-brand">
      <div class="brand-mark small">S<span>O</span></div>
      <div v-show="!collapsed"><strong>StoryOS</strong><small>生产平台</small></div>
      <el-button class="collapse-button" type="text" :aria-label="collapsed ? '展开菜单' : '收起菜单'" @click="toggle"><i :class="collapsed ? 'el-icon-s-unfold' : 'el-icon-s-fold'" /></el-button>
    </div>
    <div class="sidebar-status"><i class="status-dot success" /><span v-show="!collapsed">工作区已就绪</span></div>
    <nav class="sidebar-nav" aria-label="StoryOS 控制台导航">
      <div v-for="group in visibleGroups" :key="group.id" class="nav-group">
        <div v-show="!collapsed" class="nav-group-label">{{ group.label }}</div>
        <router-link v-for="item in group.items" :key="item.id" :to="item.path" class="nav-item" active-class="is-active">
          <i :class="item.icon" />
          <span v-show="!collapsed">{{ item.title }}</span>
        </router-link>
      </div>
    </nav>
    <div class="sidebar-bottom">
      <el-dropdown class="sidebar-user-menu" trigger="click" placement="top-start" @command="handleUserCommand">
        <el-button class="sidebar-user-trigger" type="text" aria-label="打开用户菜单">
          <el-avatar :size="28" class="sidebar-avatar">{{ initials }}</el-avatar>
          <span v-show="!collapsed" class="sidebar-user-name">{{ displayName }}</span>
          <i v-show="!collapsed" class="el-icon-arrow-up sidebar-user-arrow" />
        </el-button>
        <el-dropdown-menu slot="dropdown" class="sidebar-user-dropdown">
          <el-dropdown-item command="settings" icon="el-icon-setting">设置</el-dropdown-item>
          <el-dropdown-item command="logout" icon="el-icon-switch-button" divided>退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </aside>
</template>

<script>
import { menuGroups } from '../config/menu';

export default {
  computed: {
    collapsed() { return this.$store.state.app.sidebarCollapsed; },
    displayName() { return this.$store.state.auth.user?.displayName || this.$store.state.auth.user?.username || '未登录'; },
    initials() { return (this.displayName || 'S').slice(0, 1).toUpperCase(); },
    visibleGroups() {
      return menuGroups.map((group) => ({ ...group, items: group.items.filter((item) => this.$store.getters['auth/can'](item.permission)) })).filter((group) => group.items.length);
    },
  },
  methods: {
    toggle() { this.$store.commit('app/TOGGLE_SIDEBAR'); },
    handleUserCommand(command) {
      if (command === 'settings') this.$router.push('/settings');
      if (command === 'logout') {
        this.$store.dispatch('auth/logout');
        this.$router.replace('/login');
      }
    },
  },
};
</script>
