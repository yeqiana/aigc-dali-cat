import { apiClient } from './client';

export const runtimeApi = {
  getExecutionRuntime(id: string) {
    return apiClient.get(`/api/v1/executions/${id}`);
  },
  getTrace(id: string) {
    return apiClient.get(`/api/v1/traces/${id}`);
  },
};
