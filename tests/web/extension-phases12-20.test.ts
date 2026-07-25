import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, test } from 'vitest';
import { hypotheticalSites, stressScenarios } from '../../lib/product-analytics';
import { validateMeterCsv } from '../../lib/upload-validation';

const root = process.cwd();
const routes = [
  'business',
  'business/sites',
  'business/sites/[siteId]',
  'business/renewables',
  'business/energy-plan',
  'business/reports',
  'generator',
  'generator/output',
  'generator/offtake',
  'generator/revenue',
  'generator/assets',
  'generator/sites/[siteId]',
  'generator/reports',
  'operations',
  'operations/portfolio',
  'operations/forecasts',
  'operations/matching',
  'operations/risk',
  'operations/scenarios',
  'operations/diversification',
  'operations/concentration',
  'operations/stress-tests',
  'operations/portfolio-addition',
  'operations/reports',
  'models',
  'models/performance',
  'models/calibration',
  'models/registry',
  'models/incidents',
  'models/data-drift',
  'admin',
  'admin/customers',
  'admin/customers/new',
  'admin/generators',
  'admin/generators/new',
  'admin/contracts',
  'admin/data',
  'admin/data/uploads',
  'admin/data/incidents',
  'demo'
];

describe('Extension Phases 12–20', () => {
  test('every required product route supports direct navigation', () => {
    for (const route of routes) {
      const file = join(root, 'app', route, 'page.tsx');
      expect(existsSync(file), route).toBe(true);
      expect(readFileSync(file, 'utf8')).not.toContain('scaffold');
    }
  });

  test('business and generator claims boundaries are explicit', () => {
    const business = readFileSync(
      join(root, 'components/workspaces/business-portal.tsx'),
      'utf8'
    );
    const generator = readFileSync(
      join(root, 'components/workspaces/generator-portal.tsx'),
      'utf8'
    );
    expect(business).toContain('not the physical path of electricity');
    expect(business).toContain('Licensed supplier / partner');
    expect(generator).toContain('not physical electricity routing');
    expect(generator).toContain('Not a real invoice or Volter contract');
  });

  test('operations scenarios and diversification are deterministic', () => {
    expect(stressScenarios).toHaveLength(8);
    expect(new Set(stressScenarios.map((row) => row.id)).size).toBe(8);
    expect(hypotheticalSites.map((row) => row.id)).toEqual([
      'office',
      'supermarket',
      'solar',
      'wind'
    ]);
    const operations = readFileSync(
      join(root, 'components/workspaces/operations-portal.tsx'),
      'utf8'
    );
    expect(operations).toContain('do not retrain models');
    expect(operations).toContain('execute procurement');
  });

  test('browser fallback upload validation is bounded and auditable', () => {
    const valid = validateMeterCsv(
      'timestamp,consumption_kwh\n' +
      '2025-06-17T00:00:00Z,10\n' +
      '2025-06-17T00:30:00Z,12\n' +
      '2025-06-17T01:00:00Z,11\n'
    );
    expect(valid.readiness).toBe('ready');
    expect(valid.quality_score).toBeGreaterThanOrEqual(0);
    expect(valid.quality_score).toBeLessThanOrEqual(100);
    expect(valid.permanent_storage).toBe(false);

    const invalid = validateMeterCsv(
      'timestamp,consumption_kwh\n' +
      '2025-06-17T00:00:00Z,-2\n' +
      '2025-06-17T00:00:00Z,3\n'
    );
    expect(invalid.readiness).toBe('manual_review');
    expect(invalid.duplicates).toBe(1);
    expect(invalid.annotated_preview).toHaveLength(2);
  });

  test('reports, lineage, responsive and print styles are present', () => {
    const css = readFileSync(join(root, 'app/globals.css'), 'utf8');
    const drawer = readFileSync(
      join(root, 'components/ui/how-calculated-drawer.tsx'),
      'utf8'
    );
    expect(css).toContain('@media print');
    expect(css).toContain('@media (max-width: 860px)');
    expect(drawer).toContain('Full calculation lineage');
    expect(drawer).toContain('Open methodology evidence');
  });

  test('final interview documents exist', () => {
    for (const file of [
      'README.md',
      'ARCHITECTURE.md',
      'DATA_SOURCES.md',
      'MODEL_CARDS.md',
      'LIMITATIONS.md',
      'DEMO_SCRIPT.md',
      'INTERVIEW_TALKING_POINTS.md',
      'PRODUCT_WALKTHROUGH.md',
      'FINAL_AUDIT.md'
    ]) {
      expect(existsSync(join(root, file)), file).toBe(true);
    }
  });
});
