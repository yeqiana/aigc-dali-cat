import { apiClient } from './client';
import type { ProjectConfig, ProjectContext } from '../types/project';

export const projectApi = {
  list: () => apiClient.get<ProjectContext[]>('/api/v1/projects'),
  getConfig: (projectId: string) => apiClient.get<ProjectConfig[]>(`/api/v1/projects/${projectId}/config`),
};
