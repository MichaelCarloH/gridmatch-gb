import type { Dictionary, PortfolioPoint, Site } from './types';

export const BUSINESS_SITE_ID = 'dem_retail_cardiff';
export const GENERATOR_SITE_ID = 'gen_solar_cambridge';

export function sum(
  rows: Dictionary[],
  key: string
): number {
  return rows.reduce((total, row) => total + Number(row[key] ?? 0), 0);
}

export function mean(
  rows: Dictionary[],
  key: string
): number {
  return rows.length ? sum(rows, key) / rows.length : 0;
}

export function portfolioTotals(rows: PortfolioPoint[]) {
  return rows.reduce(
    (totals, row) => ({
      demand: totals.demand + row.demand_point_mwh,
      demandLow: totals.demandLow + row.demand_q10_mwh,
      demandHigh: totals.demandHigh + row.demand_q90_mwh,
      generation: totals.generation + row.generation_point_mwh,
      generationLow: totals.generationLow + row.generation_q10_mwh,
      generationHigh: totals.generationHigh + row.generation_q90_mwh,
      residual: totals.residual + Math.max(row.net_point_mwh, 0),
      actualDemand: totals.actualDemand + row.actual_demand_mwh,
      actualGeneration: totals.actualGeneration + row.actual_generation_mwh
    }),
    {
      demand: 0,
      demandLow: 0,
      demandHigh: 0,
      generation: 0,
      generationLow: 0,
      generationHigh: 0,
      residual: 0,
      actualDemand: 0,
      actualGeneration: 0
    }
  );
}

export function hhi(shares: number[]): number {
  const total = shares.reduce((value, share) => value + share, 0);
  if (!total) return 0;
  return shares.reduce(
    (value, share) => value + Math.pow(share / total, 2),
    0
  );
}

export function concentrationBy(
  sites: Site[],
  field: 'site_id' | 'region' | 'technology' | 'business_archetype'
) {
  const grouped = new Map<string, number>();
  for (const site of sites) {
    const label = String(site[field] || 'unknown');
    grouped.set(
      label,
      (grouped.get(label) ?? 0) + site.installed_capacity_mw
    );
  }
  const rows = [...grouped.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
  const total = rows.reduce((value, row) => value + row.value, 0);
  return {
    rows,
    largestShare: total ? rows[0]?.value / total : 0,
    topFiveShare: total
      ? rows.slice(0, 5).reduce((value, row) => value + row.value, 0) / total
      : 0,
    hhi: hhi(rows.map((row) => row.value))
  };
}

export const calculationLineage = [
  ['Meter data', 'Phase 3 dataset', 'Half-hourly observations'],
  ['Validation', 'quality-v1', 'Flagged observations and readiness score'],
  ['Weather enrichment', 'features-v1', 'Weather-aligned feature rows'],
  ['Site forecast', 'site-model-v1', 'Point and q10/q50/q90 forecasts'],
  ['Portfolio aggregation', 'portfolio-v1', 'Bottom-up and direct forecasts'],
  ['Renewable allocation', 'matching-v1', 'Commercial half-hour allocations'],
  ['Residual requirement', 'matching-v1', 'Demand less matched generation'],
  ['Procurement recommendation', 'hedge-decision-v1', 'Scenario volume'],
  ['Realised reconciliation', 'portfolio-v1', 'Planned versus actual'],
  ['Reporting', 'extension-v1', 'Audience-specific evidence views']
] as const;

export const stressScenarios = [
  {
    id: 'generator-outage',
    label: 'Largest generator outage',
    residualMultiplier: 1.28,
    uncertaintyMultiplier: 1.2,
    costMultiplier: 1.24
  },
  {
    id: 'low-wind',
    label: 'Low-wind Scotland',
    residualMultiplier: 1.18,
    uncertaintyMultiplier: 1.35,
    costMultiplier: 1.17
  },
  {
    id: 'cloud',
    label: 'Widespread cloud',
    residualMultiplier: 1.09,
    uncertaintyMultiplier: 1.18,
    costMultiplier: 1.08
  },
  {
    id: 'cold-demand',
    label: 'Cold-demand shock',
    residualMultiplier: 1.16,
    uncertaintyMultiplier: 1.24,
    costMultiplier: 1.2
  },
  {
    id: 'retail-spike',
    label: 'Supermarket demand spike',
    residualMultiplier: 1.08,
    uncertaintyMultiplier: 1.12,
    costMultiplier: 1.1
  },
  {
    id: 'meter-delay',
    label: 'Delayed meter',
    residualMultiplier: 1,
    uncertaintyMultiplier: 1.3,
    costMultiplier: 1.05
  },
  {
    id: 'weather-missing',
    label: 'Missing weather',
    residualMultiplier: 1,
    uncertaintyMultiplier: 1.45,
    costMultiplier: 1.08
  },
  {
    id: 'high-price',
    label: 'High-price scenario',
    residualMultiplier: 1,
    uncertaintyMultiplier: 1,
    costMultiplier: 1.5
  }
] as const;

export const hypotheticalSites = [
  {
    id: 'office',
    label: '1 MW office demand',
    demandMwh: 12,
    generationMwh: 0,
    uncertaintyMwh: 1.6
  },
  {
    id: 'supermarket',
    label: '1 MW supermarket demand',
    demandMwh: 18,
    generationMwh: 0,
    uncertaintyMwh: 2.1
  },
  {
    id: 'solar',
    label: '1 MW solar',
    demandMwh: 0,
    generationMwh: 4.2,
    uncertaintyMwh: 1.2
  },
  {
    id: 'wind',
    label: '1 MW wind',
    demandMwh: 0,
    generationMwh: 8.6,
    uncertaintyMwh: 1.8
  }
] as const;
