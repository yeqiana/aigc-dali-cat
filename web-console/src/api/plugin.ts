import { apiClient } from './client';
import type { PluginDefinition } from '../types/plugin';

export const pluginApi = {
  list: () => apiClient.get<PluginDefinition[]>('/api/v1/plugins'),
  extensions: () => apiClient.get('/api/v1/extensions'),
};
