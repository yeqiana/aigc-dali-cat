export const menuGroups = [
  {
    id: 'storyos',
    label: '内容生产',
    items: [
      { id: 'production', path: '/production', title: '生产监控', icon: 'el-icon-data-analysis', permission: 'production:view' },
      { id: 'episodes', path: '/episodes', title: '剧集索引', icon: 'el-icon-film', permission: 'episodes:view' },
      { id: 'logs', path: '/logs', title: '运行日志', icon: 'el-icon-document', permission: 'logs:view' },
      { id: 'workbench', path: '/workbench', title: '生产工作台', icon: 'el-icon-s-operation', permission: 'workbench:view' },
    ],
  },
  {
    id: 'platform',
    label: '平台能力',
    items: [
      { id: 'platform-console', path: '/platform', title: '平台总览', icon: 'el-icon-monitor', permission: 'platform:view' },
      { id: 'runtime', path: '/runtime', title: '运行状态', icon: 'el-icon-refresh', permission: 'platform:view' },
      { id: 'executions', path: '/executions', title: '执行记录', icon: 'el-icon-s-operation', permission: 'platform:view' },
      { id: 'traces', path: '/traces', title: '链路追踪', icon: 'el-icon-share', permission: 'platform:view' },
      { id: 'memory', path: '/memory', title: '记忆检索', icon: 'el-icon-collection', permission: 'platform:view' },
      { id: 'agents', path: '/agents', title: '智能体', icon: 'el-icon-user', permission: 'platform:view' },
    ],
  },
];

export const allMenus = menuGroups.reduce((result, group) => result.concat(group.items), []);
