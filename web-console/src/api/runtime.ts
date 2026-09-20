import { apiClient } from './client';
import type { RuntimeExecutionState, RuntimeTraceState } from '../types/monitoring';

export const runtimeApi = {
  getExecutionRuntime(id: string) {
    return apiClient.get<RuntimeExecutionState>(`/api/v1/executions/${id}`);
  },
  getTrace(id: string) {
    return apiClient.get<RuntimeTraceState>(`/api/v1/traces/${id}`);
  },
};
