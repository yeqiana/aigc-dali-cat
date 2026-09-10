import { apiClient } from './client';
import type { Agent, ExecutionRecord } from '../types/platform';

export const agentApi = {
  getAgent: (id: string) =>
    apiClient.get<Agent>(`/api/v1/agents/${id}`),

  listExecutions: (id: string) =>
    apiClient.get<ExecutionRecord[]>(`/api/v1/agents/${id}/executions`),
};
