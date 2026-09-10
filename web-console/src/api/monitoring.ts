import { apiGet } from './client';

export const monitoringApi = {
  getRuntimeState: (executionId: string) =>
    apiGet(`/api/v1/runtime/${executionId}/state`),

  getHeartbeat: (executionId: string) =>
    apiGet(`/api/v1/runtime/${executionId}/heartbeat`),
};
