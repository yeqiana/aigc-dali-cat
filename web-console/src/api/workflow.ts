import { apiClient } from './client';
import type { WorkflowRun } from '../types/platform';

export const workflowApi = {
  startRun: (code: string, data: unknown) =>
    apiClient.post<WorkflowRun>(`/api/v1/workflows/${code}/runs`, data),

  getRun: (id: string) =>
    apiClient.get<WorkflowRun>(`/api/v1/workflows/runs/${id}`),
};
