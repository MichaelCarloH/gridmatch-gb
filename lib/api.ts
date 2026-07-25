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
  const response = await fetch(`${API_BASE}${path}`, {
    signal,
    cache: 'no-store',
    headers: { Accept: 'application/json' }
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

export async function apiPost<T>(
  path: string,
  payload: unknown,
  signal?: AbortSignal
): Promise<T> {
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
