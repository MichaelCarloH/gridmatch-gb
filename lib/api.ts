import {
  forceStaticFallback,
  loadStaticFallback,
  setDataDeliveryMode
} from './static-fallback';

export const API_BASE =
  (
    process.env.NEXT_PUBLIC_GRIDMATCH_API_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL
  )?.replace(/\/$/, '') ??
  '';

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code = 'API_ERROR'
  ) {
    super(message);
  }
}

export async function apiGet<T>(
  path: string,
  signal?: AbortSignal
): Promise<T> {
  if (forceStaticFallback()) {
    const fallback = await loadStaticFallback<T>(path);
    setDataDeliveryMode('static');
    return fallback;
  }
  let apiError: Error | null = null;
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      signal,
      cache: 'no-store',
      headers: { Accept: 'application/json' }
    });
    const body = await response.json().catch(() => null);
    if (response.ok) {
      setDataDeliveryMode('api');
      return body as T;
    }
    apiError = new ApiClientError(
      body?.error?.message ?? `Request failed with status ${response.status}.`,
      response.status,
      body?.error?.code
    );
    if (response.status < 500 && response.status !== 404) throw apiError;
  } catch (reason) {
    if (signal?.aborted) throw reason;
    apiError = reason instanceof Error ? reason : new Error(String(reason));
  }
  try {
    const fallback = await loadStaticFallback<T>(path);
    setDataDeliveryMode('static');
    return fallback;
  } catch (fallbackError) {
    if (apiError) throw apiError;
    throw fallbackError;
  }
}

export async function apiPost<T>(
  path: string,
  payload: unknown,
  signal?: AbortSignal
): Promise<T> {
  if (forceStaticFallback()) {
    throw new ApiClientError(
      'Interactive recomputation requires the live API; bundled fallback mode is read-only.',
      503,
      'STATIC_FALLBACK_READ_ONLY'
    );
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    signal,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload)
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiClientError(
      body?.error?.message ?? `Request failed with status ${response.status}.`,
      response.status,
      body?.error?.code
    );
  }
  return body as T;
}

export async function apiUpload<T>(
  path: string,
  file: File,
  signal?: AbortSignal
): Promise<T> {
  if (forceStaticFallback()) {
    throw new ApiClientError(
      'Live API validation is unavailable in bundled fallback mode.',
      503,
      'STATIC_FALLBACK_READ_ONLY'
    );
  }
  const payload = new FormData();
  payload.append('file', file);
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    signal,
    headers: { Accept: 'application/json' },
    body: payload
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiClientError(
      body?.error?.message ?? `Request failed with status ${response.status}.`,
      response.status,
      body?.error?.code
    );
  }
  return body as T;
}
