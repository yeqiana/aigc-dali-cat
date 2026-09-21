import { apiClient } from './client';
import type {
  ExecutionRecord,
  RuntimeEventPage,
  RuntimeEpisodeStatus,
  RuntimeEpisodeStatusPage,
  TraceRecord,
} from '../types/platform';

export const runtimeApi = {
  getExecution(id: string) {
    return apiClient.get<ExecutionRecord>(`/api/v1/executions/${id}`);
  },
  getTrace(traceId: string) {
    return apiClient.get<TraceRecord>(`/api/v1/traces/${traceId}`);
  },
  getEpisodeStatus(episodeRef: string) {
    return apiClient.get<RuntimeEpisodeStatus>(
      `/api/v1/runtime/status?episode=${encodeURIComponent(episodeRef)}`,
    );
  },
  listEpisodeStatuses(limit = 20, offset = 0) {
    return apiClient.get<RuntimeEpisodeStatusPage>(
      `/api/v1/runtime/statuses?limit=${limit}&offset=${offset}`,
    );
  },
  listEvents(limit = 50, offset = 0, episodeId = '') {
    const episodeQuery = episodeId
      ? `&episode_id=${encodeURIComponent(episodeId)}`
      : '';
    return apiClient.get<RuntimeEventPage>(
      `/api/v1/runtime/events?limit=${limit}&offset=${offset}${episodeQuery}`,
    );
  },
};
