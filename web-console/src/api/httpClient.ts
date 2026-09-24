import { appConfig } from '../config/appConfig';

// Platform API 信封：platform/api/http_server.py 统一种子格式。
export interface PlatformEnvelope<T> {
  code: string;
  message?: string;
  data: T;
  trace_id?: string;
  timestamp?: string;
}

export interface HttpRequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
}

const DEFAULT_TIMEOUT_MS = 10000;

export class PlatformApiError extends Error {
  readonly code: string;
  readonly httpStatus: number;
  readonly traceId?: string;

  constructor(code: string, message: string, httpStatus: number, traceId?: string) {
    super(message);
    this.name = 'PlatformApiError';
    this.code = code;
    this.httpStatus = httpStatus;
    this.traceId = traceId;
  }
}

function buildUrl(path: string): string {
  if (appConfig.platformApiBaseUrl) {
    return appConfig.platformApiBaseUrl.replace(/\/+$/, '') + path;
  }
  // 未显式配置基址时走同源相对路径，由 Vite proxy 转发至 Platform API。
  return path;
}

/** 解包 Platform API 信封；保留原始 payload 供排查。 */
export function unwrapEnvelope<T>(payload: unknown): T {
  if (payload && typeof payload === 'object' && 'data' in (payload as Record<string, unknown>)) {
    return (payload as PlatformEnvelope<T>).data;
  }
  return payload as T;
}

/**
 * 对 Platform API 发起请求并解包信封。
 *
 * - 非 2xx 或 code != OK 时抛出 PlatformApiError，错误信息带 code 便于定位后端能力缺口
 *   （例如 RegistryApiController 未配置时返回 503 CAPABILITY_NOT_CONFIGURED）。
 * - 超时默认 10s，且可由调用方用 signal 主动中止。
 */
export async function platformRequest<T>(path: string, options: HttpRequestOptions = {}): Promise<T> {
  const { method = 'GET', body, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const relayAbort = () => controller.abort();
  signal?.addEventListener('abort', relayAbort);
  try {
    const response = await fetch(buildUrl(path), {
      method,
      headers: body === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    let parsed: unknown = null;
    const raw = await response.text();
    if (raw) {
      try {
        parsed = JSON.parse(raw);
      } catch {
        throw new PlatformApiError('INVALID_RESPONSE', 'Platform API 返回了非 JSON 响应', response.status);
      }
    }
    const envelope = (parsed || {}) as PlatformEnvelope<T>;
    if (!response.ok || (envelope.code && envelope.code !== 'OK')) {
      const message = envelope.message || (response.ok ? `请求失败（${envelope.code || 'unknown'}）` : `请求失败（HTTP ${response.status}）`);
      throw new PlatformApiError(envelope.code || 'HTTP_ERROR', message, response.status, envelope.trace_id);
    }
    return unwrapEnvelope<T>(parsed);
  } catch (error) {
    if (error instanceof PlatformApiError) throw error;
    if ((error as Error)?.name === 'AbortError') {
      throw new PlatformApiError('TIMEOUT', 'Platform API 请求超时', 0);
    }
    throw new PlatformApiError('NETWORK_ERROR', (error as Error)?.message || 'Platform API 网络请求失败', 0);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', relayAbort);
  }
}
