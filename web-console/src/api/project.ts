import { apiClient } from './client';

export const projectApi = {
  list: () => apiClient.get('/api/v1/projects'),
  getConfig: (projectId: string) => apiClient.get(`/api/v1/projects/${projectId}/config`),
};
