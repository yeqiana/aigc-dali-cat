import { apiGet } from './client';
import type { ExecutionRecord } from '../types/platform';

export const executionApi = {
  get(id: string) {
    return apiGet<ExecutionRecord>(`/api/v1/executions/${id}`);
  },
};
