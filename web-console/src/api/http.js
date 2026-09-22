import axios from 'axios';
import { appConfig } from '../config/app';
import { storageKeys } from '../config/app';

const http = axios.create({
  baseURL: appConfig.platformApiBaseUrl,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(storageKeys.token);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (response) => {
    const payload = response.data;
    return payload && Object.prototype.hasOwnProperty.call(payload, 'data') ? payload.data : payload;
  },
  (error) => {
    const status = error.response?.status;
    const message = error.response?.data?.message || (status ? `请求失败（HTTP ${status}）` : error.message || '请求失败');
    return Promise.reject(new Error(message));
  },
);

export default http;
