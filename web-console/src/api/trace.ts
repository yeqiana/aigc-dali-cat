import { apiClient } from './client';
import type { TracePage, TraceRecord } from '../types/platform';

export const traceApi = {
  get: (id: string) =>
    apiClient.get<TraceRecord>(`/api/v1/traces/${id}`),
  list: (limit = 20, offset = 0, episodeId = '', traceId = '') => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (episodeId) params.set('episode_id', episodeId);
    if (traceId) params.set('trace_id', traceId);
    return apiClient.get<TracePage>(`/api/v1/traces?${params.toString()}`);
  },
};
