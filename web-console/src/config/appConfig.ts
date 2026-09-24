// StoryOS Web Console 应用配置。
//
// 后端基址只保留一个入口：VITE_PLATFORM_API_URL。
// 留空表示走 Vite dev/preview 的同源代理（vite.config.ts -> platformProxy），
// 由代理转发到 Platform API（默认 http://127.0.0.1:8080）。
// 该字段与仓库内 scripts/platform_console_launcher.py、tests/platform 契约保持一致。
export const appConfig = {
  appName: 'StoryOS 控制台',
  headerText: 'StoryOS 生产控制台',
  platformApiBaseUrl: (import.meta.env.VITE_PLATFORM_API_URL || '').replace(/\/$/, ''),
} as const;

export const storageKeys = {
  token: 'storyos_console_token',
  user: 'storyos_console_user',
} as const;

export default appConfig;
