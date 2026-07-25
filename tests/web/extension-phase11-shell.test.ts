import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { apiGet } from '../../lib/api';
import { canonicalApiPath } from '../../lib/static-fallback';

const root = process.cwd();

describe('Extension Phase 11 shared shell', () => {
  afterEach(() => vi.unstubAllGlobals());

  test('all workspace roots support direct navigation', () => {
    for (const route of [
      'business',
      'generator',
      'operations',
      'models',
      'research',
      'admin'
    ]) {
      expect(existsSync(join(root, 'app', route, 'page.tsx')), route).toBe(true);
    }
  });

  test('required shared components are implemented and wired into the shell', () => {
    const files = [
      ['components/layout/workspace-switcher.tsx', 'WorkspaceSwitcher'],
      ['components/layout/primary-nav.tsx', 'PrimaryNav'],
      ['components/layout/secondary-nav.tsx', 'SecondaryNav'],
      ['components/ui/metric-card.tsx', 'MetricCard'],
      ['components/ui/metric-explanation.tsx', 'MetricExplanation'],
      ['components/ui/how-calculated-drawer.tsx', 'HowCalculatedDrawer'],
      ['components/ui/action-card.tsx', 'ActionCard'],
      ['components/ui/badges.tsx', 'DataOriginBadge'],
      ['components/ui/badges.tsx', 'ScenarioBadge'],
      ['components/ui/artifact-status.tsx', 'ArtifactStatus'],
      ['components/ui/states.tsx', 'LoadingSkeleton'],
      ['components/ui/states.tsx', 'ErrorState'],
      ['components/ui/states.tsx', 'EmptyState']
    ];
    for (const [file, symbol] of files) {
      expect(readFileSync(join(root, file), 'utf8'), file).toContain(symbol);
    }
    const shell = readFileSync(
      join(root, 'components/layout/app-shell.tsx'),
      'utf8'
    );
    expect(shell).toContain('DEMO_PERIOD_LABEL');
    expect(shell).toContain('Demonstration data boundary');
    expect(shell).toContain('<Breadcrumbs');
    expect(shell).toContain('<ArtifactStatus');
  });

  test('workspace selection persists across extension workspace routes', () => {
    const context = readFileSync(
      join(root, 'components/layout/workspace-context.tsx'),
      'utf8'
    );
    expect(context).toContain("const STORAGE_KEY = 'gridmatch.workspace'");
    expect(context).toContain('window.localStorage.setItem');
    expect(readdirSync(join(root, 'app', 'business'))).toContain('sites');
    expect(readdirSync(join(root, 'app', 'generator'))).toContain('offtake');
    expect(readdirSync(join(root, 'app', 'operations'))).toContain('risk');
    expect(readdirSync(join(root, 'app', 'models'))).toContain('registry');
    expect(readdirSync(join(root, 'app', 'admin'))).toContain('data');
  });

  test('static fallback bundles are compact, indexed and canonical', () => {
    const fallbackRoot = join(root, 'public/demo-data/fallback');
    const index = JSON.parse(
      readFileSync(join(fallbackRoot, 'index.json'), 'utf8')
    );
    expect(index.version).toBe('extension-phase20-v1');
    expect(Object.keys(index.routes).length).toBeGreaterThanOrEqual(100);
    for (const route of [
      '/health',
      '/api/sites?limit=100',
      '/api/portfolio/forecast?limit=48&method=reconciled',
      '/api/matching/summary',
      '/api/research/notebooks'
    ]) {
      expect(index.routes[route], route).toBeDefined();
      expect(existsSync(join(fallbackRoot, index.routes[route].bundle))).toBe(true);
    }
    expect(
      canonicalApiPath('/api/sites?z=2&limit=100&a=1')
    ).toBe('/api/sites?a=1&limit=100&z=2');
  });

  test('forced static mode returns bundled API evidence without FastAPI', async () => {
    const fallbackRoot = join(root, 'public/demo-data/fallback');
    vi.stubGlobal('window', {
      location: { search: '?data=static' },
      localStorage: { getItem: () => null }
    });
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      const name = url.split('/').at(-1) ?? '';
      return new Response(readFileSync(join(fallbackRoot, name), 'utf8'), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }));
    const response = await apiGet<{ meta: { count: number } }>(
      '/api/sites?limit=100'
    );
    expect(response.meta.count).toBe(12);
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  test('first render uses loading state instead of false KPI values', () => {
    const home = readFileSync(join(root, 'app/page.tsx'), 'utf8');
    const dashboard = readFileSync(join(root, 'app/dashboard/page.tsx'), 'utf8');
    const research = readFileSync(join(root, 'app/research/page.tsx'), 'utf8');
    expect(home).toContain('inline-skeleton');
    expect(home).not.toContain("?? '—'");
    expect(dashboard).toContain('sites.loading');
    expect(research).toContain('notebooks.loading');
  });
});
