import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, test } from 'vitest';
import { gbp, number, percent, titleCase } from '../../lib/format';

const root = process.cwd();
const routes = [
  'app/page.tsx',
  'app/dashboard/page.tsx',
  'app/map/page.tsx',
  'app/sites/page.tsx',
  'app/sites/[siteId]/page.tsx',
  'app/forecasts/page.tsx',
  'app/matching/page.tsx',
  'app/market/page.tsx',
  'app/research/page.tsx',
  'app/reports/page.tsx'
];

describe('Phase 11 product surface', () => {
  test('all P0 product routes contain implemented pages', () => {
    for (const route of routes) {
      const path = join(root, route);
      expect(existsSync(path), route).toBe(true);
      expect(readFileSync(path, 'utf8')).not.toContain('Repository scaffold ready');
    }
  });

  test('design tokens and responsive rules are present', () => {
    const css = readFileSync(join(root, 'app/globals.css'), 'utf8');
    const map = readFileSync(
      join(root, 'components/map/gb-map.tsx'),
      'utf8'
    );
    for (const token of ['--paper', '--surface', '--ink', '--green', '--blue', '--amber', '--red']) {
      expect(css).toContain(token);
    }
    expect(css).toContain('@media (max-width: 860px)');
    expect(css).toContain('prefers-reduced-motion');
    expect(map).toContain('Natural Earth 1:110m public-domain geometry');
    expect(map).toContain('const gbPolygons');
    expect(map).not.toContain('M248 25l42 32');
  });

  test('shared energy formatting is explicit and bounded', () => {
    expect(number(1.234, 2)).toBe('1.23');
    expect(percent(0.684, 1)).toBe('68.4%');
    expect(gbp(1234)).toContain('1,234');
    expect(titleCase('local_preference')).toBe('Local Preference');
  });

  test('local development starts both services through a same-origin proxy', () => {
    const packageJson = JSON.parse(
      readFileSync(join(root, 'package.json'), 'utf8')
    );
    const client = readFileSync(join(root, 'lib/api.ts'), 'utf8');
    const nextConfig = readFileSync(join(root, 'next.config.mjs'), 'utf8');
    expect(packageJson.scripts.dev).toBe('node scripts/dev.mjs');
    expect(client).toContain("?.replace(/\\/$/, '') ??");
    expect(nextConfig).toContain("source: '/api/:path*'");
    expect(nextConfig).toContain('GRIDMATCH_API_INTERNAL_URL');
  });
});
