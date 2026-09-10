import { apiClient } from './client';
import type { MemoryItem } from '../types/platform';

export const memoryApi = {
  search: (query: string) =>
    apiClient.post<MemoryItem[]>('/api/v1/memory/search', { query }),

  get: (id: string) =>
    apiClient.get<MemoryItem>(`/api/v1/memory/${id}`),
};
