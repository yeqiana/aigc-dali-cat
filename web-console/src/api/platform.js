import http from './http';

export const platformApi = {
  health() {
    return http.get('/healthz');
  },
  runtimeStatuses(limit = 20, offset = 0) {
    return http.get(`/api/v1/runtime/statuses?limit=${limit}&offset=${offset}`);
  },
  events(limit = 50, offset = 0, episodeId = '') {
    const suffix = episodeId ? `&episode_id=${encodeURIComponent(episodeId)}` : '';
    return http.get(`/api/v1/runtime/events?limit=${limit}&offset=${offset}${suffix}`);
  },
  execution(id) {
    return http.get(`/api/v1/executions/${encodeURIComponent(id)}`);
  },
  trace(id) {
    return http.get(`/api/v1/traces/${encodeURIComponent(id)}`);
  },
  traces(limit = 20, offset = 0, episodeId = '', traceId = '') {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (episodeId) params.set('episode_id', episodeId);
    if (traceId) params.set('trace_id', traceId);
    return http.get(`/api/v1/traces?${params.toString()}`);
  },
  memory(query) {
    return http.post('/api/v1/memory/search', { query });
  },
  agents() {
    return http.get('/api/v1/agents');
  },
};
