import http from './http';
import { appConfig } from '../config/app';
import { loginWithDemoAccount } from '../auth/demo';

export function login(username, password) {
  if (appConfig.authMode === 'remote') {
    return http.post(import.meta.env.VITE_AUTH_API_URL, { username, password }).then((body) => ({
      token: body.token || body.access_token,
      user: body.user || body.principal || { username },
    }));
  }
  return loginWithDemoAccount(username, password);
}
