export interface ApiResponse<T> {
  code: string;
  message: string;
  data: T;
  trace_id: string;
  timestamp: string;
}

const API_BASE_URL = import.meta.env.VITE_PLATFORM_API_URL ?? '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
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

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: JSON.stringify(data ?? {}),
    }),
};
