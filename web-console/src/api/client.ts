export interface ApiResponse<T> {
  code: string;
  message: string;
  data: T;
  trace_id: string;
  timestamp: string;
}

export const PLATFORM_API_BASE_URL = (import.meta.env.VITE_PLATFORM_API_URL ?? '').replace(/\/$/, '');

export function platformApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${PLATFORM_API_BASE_URL}${normalizedPath}`;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(platformApiUrl(path), {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  const body = (await response.json()) as ApiResponse<T>;
  if (body.code !== 'OK') {
    throw new Error(body.message);
  }

  return body.data;
}

export const apiGet = <T>(path: string) => request<T>(path);

export const apiClient = {
  get: <T>(path: string) => apiGet<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: JSON.stringify(data ?? {}),
    }),
};
