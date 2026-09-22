export const appConfig = {
  appName: 'StoryOS 控制台',
  headerText: 'StoryOS 生产控制台',
  systemVersion: '3.0.0',
  authMode: import.meta.env.VITE_AUTH_API_URL ? 'remote' : 'local',
  platformApiBaseUrl: (import.meta.env.VITE_PLATFORM_API_URL || '').replace(/\/$/, ''),
};

export const storageKeys = {
  token: 'storyos_console_token',
  user: 'storyos_console_user',
};
