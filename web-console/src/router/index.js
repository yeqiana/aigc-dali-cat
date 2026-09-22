import Vue from 'vue';
import Router from 'vue-router';
import store from '../store';
import { allMenus } from '../config/menu';
import Login from '../layout/Login.vue';
import Home from '../layout/Home.vue';
import ProductionMonitor from '../views/storyos/ProductionMonitor.vue';
import Episodes from '../views/storyos/Episodes.vue';
import RuntimeLogs from '../views/storyos/RuntimeLogs.vue';
import Workbench from '../views/storyos/Workbench.vue';
import Settings from '../views/Settings.vue';
import PlatformConsole from '../views/platform/PlatformConsole.vue';
import RuntimeExplorer from '../views/platform/RuntimeExplorer.vue';
import ExecutionExplorer from '../views/platform/ExecutionExplorer.vue';
import TraceExplorer from '../views/platform/TraceExplorer.vue';
import MemoryExplorer from '../views/platform/MemoryExplorer.vue';
import AgentsExplorer from '../views/platform/AgentsExplorer.vue';
import NotFound from '../views/NotFound.vue';

Vue.use(Router);

const viewMap = {
  production: ProductionMonitor,
  episodes: Episodes,
  logs: RuntimeLogs,
  workbench: Workbench,
  'platform-console': PlatformConsole,
  runtime: RuntimeExplorer,
  executions: ExecutionExplorer,
  traces: TraceExplorer,
  memory: MemoryExplorer,
  agents: AgentsExplorer,
};

const menuRoutes = allMenus.map((menu) => ({
  path: menu.path.replace(/^\//, ''),
  name: menu.id,
  component: viewMap[menu.id],
  meta: { title: menu.title, permission: menu.permission, menuId: menu.id },
}));

export const routes = [
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  {
    path: '/',
    component: Home,
    redirect: '/production',
    children: [
      ...menuRoutes,
      { path: 'settings', name: 'settings', component: Settings, meta: { title: '设置', permission: 'settings:view', menuId: 'settings' } },
    ],
  },
  { path: '/404', name: 'not-found', component: NotFound, meta: { public: true } },
  { path: '*', redirect: '/404' },
];

const router = new Router({ mode: 'history', routes });

router.beforeEach((to, from, next) => {
  if (to.meta.public) {
    if (to.name === 'login' && store.getters['auth/isAuthenticated']) return next('/production');
    return next();
  }
  if (!store.getters['auth/isAuthenticated']) {
    return next({ name: 'login', query: { redirect: to.fullPath } });
  }
  const permission = to.meta.permission;
  if (permission && !store.getters['auth/can'](permission)) return next('/404');
  return next();
});

export default router;
