export type DataDeliveryMode = 'checking' | 'api' | 'static';

type FallbackRoute = {
  bundle: string;
  key: string;
};

type FallbackIndex = {
  version: string;
  generated_at_utc: string;
  demo_period: {
    label: string;
    start_utc: string;
    end_utc: string;
  };
  routes: Record<string, FallbackRoute>;
};

type FallbackBundle = {
  responses: Record<string, unknown>;
};

const ROOT = '/demo-data/fallback';
let indexPromise: Promise<FallbackIndex> | null = null;
const bundlePromises = new Map<string, Promise<FallbackBundle>>();
let deliveryMode: DataDeliveryMode = 'checking';
const listeners = new Set<(mode: DataDeliveryMode) => void>();

export function canonicalApiPath(path: string): string {
  const url = new URL(path, 'https://gridmatch.local');
  const params = [...url.searchParams.entries()].sort(
    ([aKey, aValue], [bKey, bValue]) =>
      aKey === bKey
        ? aValue.localeCompare(bValue)
        : aKey.localeCompare(bKey)
  );
  const query = new URLSearchParams(params).toString();
  return `${url.pathname}${query ? `?${query}` : ''}`;
}

async function fallbackIndex(): Promise<FallbackIndex> {
  indexPromise ??= fetch(`${ROOT}/index.json`, { cache: 'no-store' })
    .then(async (response) => {
      if (!response.ok) throw new Error('Static artifact index is unavailable.');
      return (await response.json()) as FallbackIndex;
    })
    .catch((error) => {
      indexPromise = null;
      throw error;
    });
  return indexPromise;
}

async function fallbackBundle(
  bundle: string,
  version: string
): Promise<FallbackBundle> {
  const cacheKey = `${version}:${bundle}`;
  const existing = bundlePromises.get(cacheKey);
  if (existing) return existing;
  const request = fetch(
    `${ROOT}/${bundle}?version=${encodeURIComponent(version)}`,
    { cache: 'no-store' }
  )
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Static artifact bundle ${bundle} is unavailable.`);
      }
      return (await response.json()) as FallbackBundle;
    })
    .catch((error) => {
      bundlePromises.delete(cacheKey);
      throw error;
    });
  bundlePromises.set(cacheKey, request);
  return request;
}

async function loadFromIndex<T>(
  canonical: string,
  index: FallbackIndex
): Promise<T> {
  const route = index.routes[canonical];
  if (!route) {
    throw new Error(`No bundled fallback is available for ${canonical}.`);
  }
  const bundle = await fallbackBundle(route.bundle, index.version);
  if (!(route.key in bundle.responses)) {
    throw new Error(`Bundled fallback entry ${route.key} is unavailable.`);
  }
  return bundle.responses[route.key] as T;
}

export async function loadStaticFallback<T>(path: string): Promise<T> {
  const canonical = canonicalApiPath(path);
  const index = await fallbackIndex();
  try {
    return await loadFromIndex<T>(canonical, index);
  } catch {
    // An open browser tab can outlive a deployment. Refresh both caches once so
    // an old index is never combined with bundles from the new deployment.
    indexPromise = null;
    bundlePromises.clear();
    const refreshedIndex = await fallbackIndex();
    return loadFromIndex<T>(canonical, refreshedIndex);
  }
}

export function forceStaticFallback(): boolean {
  if (process.env.NEXT_PUBLIC_GRIDMATCH_FORCE_STATIC === 'true') return true;
  if (typeof window === 'undefined') return false;
  const queryMode = new URLSearchParams(window.location.search).get('data');
  return (
    queryMode === 'static' ||
    window.localStorage.getItem('gridmatch.data-delivery') === 'static'
  );
}

export function setDataDeliveryMode(mode: DataDeliveryMode): void {
  if (deliveryMode === mode) return;
  deliveryMode = mode;
  listeners.forEach((listener) => listener(mode));
}

export function getDataDeliveryMode(): DataDeliveryMode {
  return deliveryMode;
}

export function subscribeDataDeliveryMode(
  listener: (mode: DataDeliveryMode) => void
): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
