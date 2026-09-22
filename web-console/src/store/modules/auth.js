import { login } from '../../api/auth';
import { storageKeys } from '../../config/app';

function readJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key) || '') || fallback;
  } catch (error) {
    return fallback;
  }
}

const state = {
  token: localStorage.getItem(storageKeys.token) || '',
  user: readJson(storageKeys.user, null),
};

const mutations = {
  SET_AUTH(state, payload) {
    state.token = payload.token;
    state.user = payload.user;
    localStorage.setItem(storageKeys.token, payload.token);
    localStorage.setItem(storageKeys.user, JSON.stringify(payload.user));
  },
  CLEAR_AUTH(state) {
    state.token = '';
    state.user = null;
    localStorage.removeItem(storageKeys.token);
    localStorage.removeItem(storageKeys.user);
  },
};

const actions = {
  login({ commit }, credentials) {
    return login(credentials.username, credentials.password).then((payload) => {
      if (!payload.token) throw new Error('登录响应缺少 token');
      commit('SET_AUTH', payload);
      return payload;
    });
  },
  logout({ commit }) {
    commit('CLEAR_AUTH');
  },
};

const getters = {
  isAuthenticated: (state) => Boolean(state.token),
  permissions: (state) => state.user?.permissions || [],
  can: (state, getters) => (permission) => getters.permissions.includes(permission),
};

export default { namespaced: true, state, mutations, actions, getters };
