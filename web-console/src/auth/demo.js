const demoUser = {
  id: 'usr-storyos-admin',
  username: 'admin',
  displayName: 'StoryOS 管理员',
  role: 'operator',
  permissions: [
    'production:view',
    'episodes:view',
    'logs:view',
    'platform:view',
    'settings:view',
    'workbench:view',
  ],
};

export function loginWithDemoAccount(username, password) {
  if (username !== 'admin' || password !== 'admin123') {
    return Promise.reject(new Error('账户或密码不正确'));
  }
  return Promise.resolve({ token: `demo-token-${Date.now()}`, user: demoUser });
}
