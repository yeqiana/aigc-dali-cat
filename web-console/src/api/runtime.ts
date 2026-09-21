import { apiClient } from './client';
import type { ExecutionRecord, TraceRecord } from '../types/platform';

export const runtimeApi = {
  getExecution(id: string) {
    return apiClient.get<ExecutionRecord>(`/api/v1/executions/${id}`);
  },
  getTrace(traceId: string) {
    return apiClient.get<TraceRecord>(`/api/v1/traces/${traceId}`);
  },
};
