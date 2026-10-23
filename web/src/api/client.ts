/** Typed fetch client: JSON in/out, CSRF header on mutations, errors mapped to ApiError. */
export const API_BASE = '/api/v1';

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    /** Validation details: FastAPI `detail` array (422) or the backend's `error.details`. */
    readonly details?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

let csrfToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

/** Headers every mutation needs (CSRF); for callers that send a non-JSON body. */
export function mutationHeaders(): Record<string, string> {
  return csrfToken ? { 'X-CSRF-Token': csrfToken } : {};
}

export function notifyUnauthorized(): void {
  onUnauthorized?.();
}

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

export async function toApiError(res: Response): Promise<ApiError> {
  try {
    const body = (await res.json()) as { error?: { code?: string; message?: string; details?: unknown }; detail?: unknown };
    const details = body.error?.details ?? body.detail;
    return new ApiError(res.status, body.error?.code ?? `http_${res.status}`, body.error?.message ?? res.statusText, details);
  } catch {
    return new ApiError(res.status, `http_${res.status}`, res.statusText);
  }
}

export async function request<T>(method: Method, path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (method !== 'GET') {
    if (csrfToken) headers['X-CSRF-Token'] = csrfToken;
    if (body !== undefined) headers['Content-Type'] = 'application/json';
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      credentials: 'same-origin',
      signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e;
    throw new ApiError(0, 'network', 'network error');
  }
  if (!res.ok) {
    const err = await toApiError(res);
    if (err.status === 401) onUnauthorized?.();
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const get = <T>(path: string, signal?: AbortSignal) => request<T>('GET', path, undefined, signal);
export const post = <T>(path: string, body?: unknown) => request<T>('POST', path, body);
export const patch = <T>(path: string, body: unknown) => request<T>('PATCH', path, body);
export const put = <T>(path: string, body: unknown) => request<T>('PUT', path, body);
export const del = <T>(path: string) => request<T>('DELETE', path);

export function query(params: Record<string, string | number | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== '') q.set(k, String(v));
  const s = q.toString();
  return s ? `?${s}` : '';
}
