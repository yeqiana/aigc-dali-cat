import { apiClient } from './client';
import type { TraceRecord } from '../types/platform';

export const traceApi = {
  get: (id: string) =>
    apiClient.get<TraceRecord>(`/api/v1/traces/${id}`),
};
