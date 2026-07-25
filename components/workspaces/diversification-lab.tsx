'use client';

import { useMemo, useState } from 'react';
import { Bars } from '@/components/charts/bars';
import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { EvidenceTable } from '@/components/ui/evidence-table';
import { MetricCard } from '@/components/ui/metric-card';
import { gbp, number, percent, titleCase } from '@/lib/format';
import { concentrationBy, hypotheticalSites, portfolioTotals, stressScenarios } from '@/lib/product-analytics';
import { useApi } from '@/lib/use-api';
import type { Dictionary, Envelope, PortfolioPoint, Site } from '@/lib/types';

type DiversificationView = 'diversification' | 'concentration' | 'stress-tests' | 'portfolio-addition';

export function DiversificationLab({ view }: { view: DiversificationView }) {
  const [scenarioId, setScenarioId] = useState<string>(stressScenarios[0].id);
  const [additionId, setAdditionId] = useState<string>(hypotheticalSites[0].id);
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const attribution = useApi<Envelope<Dictionary[]>>('/api/portfolio/error-attribution?level=site');
  const correlation = useApi<Envelope<Dictionary>>('/api/portfolio/correlation');
  const forecast = useApi<Envelope<PortfolioPoint[]>>('/api/portfolio/forecast?method=reconciled&limit=48');
  const matching = useApi<Envelope<Dictionary>>('/api/matching/summary');
  const policies = useApi<Envelope<Dictionary[]>>('/api/market/policy-summary');
  const hooks = [sites, attribution, correlation, forecast, matching, policies];
  const loading = hooks.some((hook) => hook.loading);
  const error = hooks.find((hook) => hook.error)?.error ?? null;
  const siteRows = sites.data?.data ?? [];
  const attributionRows = attribution.data?.data ?? [];
  const totals = portfolioTotals(forecast.data?.data ?? []);
  const policy = policies.data?.data.find((row) => row.policy === 'validation_optimised') ?? policies.data?.data[0];
  const baseCoverage = Number(matching.data?.data.analysis?.average_forecast_renewable_match_rate ?? 0);
  const region = concentrationBy(siteRows, 'region');
  const technology = concentrationBy(siteRows, 'technology');
  const archetype = concentrationBy(siteRows, 'business_archetype');
  const customers = concentrationBy(siteRows.filter((row) => row.site_role === 'demand'), 'site_id');
  const generators = concentrationBy(siteRows.filter((row) => row.site_role === 'generation'), 'site_id');
  const scenario = stressScenarios.find((row) => row.id === scenarioId) ?? stressScenarios[0];
  const addition = hypotheticalSites.find((row) => row.id === additionId) ?? hypotheticalSites[0];
  const additionResult = useMemo(() => {
    const demand = totals.demand + addition.demandMwh;
    const generation = totals.generation + addition.generationMwh;
    const matched = Math.min(demand, generation);
    return {
      coverage: demand ? matched / demand : 0,
      residual: Math.max(demand - generation, 0),
      uncertainty: (totals.demandHigh - totals.demandLow) + addition.uncertaintyMwh,
      cost: Number(policy?.total_cost_gbp ?? 0) * (1 + Math.max(addition.demandMwh - addition.generationMwh, -5) / Math.max(totals.demand, 1)),
      concentration: Math.max(0, technology.hhi - (addition.generationMwh > 0 ? 0.015 : 0))
    };
  }, [addition, policy?.total_cost_gbp, technology.hhi, totals]);
  const correlationData = correlation.data?.data;
  const correlationPairs = (() => {
    const ids = (correlationData?.site_ids ?? []) as string[];
    const matrix = (correlationData?.matrix ?? []) as number[][];
    const pairs: Dictionary[] = [];
    ids.forEach((left, i) => ids.slice(i + 1).forEach((right, offset) => {
      pairs.push({ pair: `${left} / ${right}`, correlation: Number(matrix[i]?.[i + offset + 1] ?? 0) });
    }));
    return pairs.sort((a, b) => Math.abs(Number(b.correlation)) - Math.abs(Number(a.correlation))).slice(0, 10);
  })();

  const title = {
    diversification: ['Diversification lab', 'Forecast errors are portfolio assets too.', 'Use saved site-error correlation and contribution evidence to find combinations that reduce concentration.'],
    concentration: ['Concentration', 'Know what dominates the portfolio.', 'Largest share, top-five share and HHI across region, technology and archetype.'],
    'stress-tests': ['Stress tests', 'Reproducible shocks, no retraining.', 'Apply documented deterministic multipliers to saved portfolio outputs.'],
    'portfolio-addition': ['Portfolio addition', 'Test a hypothetical site before retraining.', 'Add a deterministic office, supermarket, solar or wind profile and compare portfolio effects.']
  }[view];

  return (
    <>
      <PageHeader eyebrow={title[0]} title={title[1]} description={title[2]} actions={<span className="badge scenario-badge">Deterministic analysis</span>} />
      <DataState loading={loading} error={error} />
      {!loading && !error && (
        <>
          {view === 'diversification' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Largest error contributor" value={String(attributionRows[0]?.site_id ?? 'None')} detail={percent(attributionRows[0]?.absolute_error_share, 1)} tone="amber" icon="alert" explanation={{ source: 'portfolio_error_attribution_site.parquet', calculation: 'Site with largest absolute-error share.' }} />
                <MetricCard label="Correlation pairs" value={String(correlationPairs.length)} detail="Highest absolute relationships shown" tone="blue" icon="chart" explanation={{ source: 'portfolio_error_correlation.parquet', calculation: 'Unique site-pair correlations sorted by absolute value.' }} />
                <MetricCard label="Region HHI" value={number(region.hhi, 3)} detail="Capacity-share concentration" icon="map" explanation={{ source: 'site registry', calculation: 'Sum of squared regional capacity shares.' }} />
                <MetricCard label="Technology HHI" value={number(technology.hhi, 3)} detail="Capacity-share concentration" tone="green" icon="bolt" explanation={{ source: 'site registry', calculation: 'Sum of squared technology capacity shares.' }} />
              </section>
              <section className="grid two section-gap">
                <article className="card"><h3>Error contribution</h3><Bars rows={attributionRows.slice(0, 10)} labelKey="site_id" valueKey="absolute_error_share" unit="share" color="var(--amber)" /></article>
                <article className="card"><h3>Strongest error relationships</h3><EvidenceTable caption="Strongest site-error correlation pairs" headers={['Site pair', 'Correlation']} rows={correlationPairs.map((row) => [String(row.pair), number(row.correlation, 3)])} /></article>
              </section>
              <EvidenceTable caption="Site risk contribution" headers={['Site', 'Error contribution', 'Variance proxy', 'Shortfall proxy', 'Diversification benefit']} rows={attributionRows.map((row) => {
                const share = Number(row.absolute_error_share ?? 0);
                const variance = Number(row.rmse_mwh ?? 0) ** 2;
                const shortfall = Math.max(Number(row.bias_mwh ?? 0), 0);
                const benefit = Math.max(0, 1 - share);
                return [String(row.site_id), percent(share, 2), `${number(variance, 4)} MWh²`, `${number(shortfall, 3)} MWh`, percent(benefit, 1)];
              })} />
            </>
          )}

          {view === 'concentration' && (
            <>
              <section className="grid five">
                {([
                  ['Customer', customers],
                  ['Generator', generators],
                  ['Region', region],
                  ['Technology', technology],
                  ['Archetype', archetype]
                ] as Array<[string, typeof region]>).map(([label, values]) => {
                  return <article className="card" key={String(label)}><h3>{label}</h3><div className="detail-list"><div><span>Largest share</span><b>{percent(values.largestShare, 1)}</b></div><div><span>Top-five share</span><b>{percent(values.topFiveShare, 1)}</b></div><div><span>HHI</span><b>{number(values.hhi, 3)}</b></div></div><Bars rows={values.rows} labelKey="label" valueKey="value" unit="MW" /></article>;
                })}
              </section>
              <div className="callout section-gap"><strong>Interpretation</strong><p>HHI uses installed-capacity share as a deterministic exposure proxy. It is not a regulatory concentration assessment or contract-value measure.</p></div>
            </>
          )}

          {view === 'stress-tests' && (
            <>
              <label className="field">Stress scenario<select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>{stressScenarios.map((row) => <option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
              <section className="kpi-grid section-gap">
                <MetricCard label="Residual demand" value={`${number(totals.residual * scenario.residualMultiplier)} MWh`} detail={`${number((scenario.residualMultiplier - 1) * 100, 0)}% deterministic shock`} tone="amber" icon="grid" explanation={{ source: 'saved forecast + scenario definition', calculation: 'Base residual multiplied by documented scenario factor.' }} />
                <MetricCard label="Uncertainty width" value={`${number((totals.demandHigh - totals.demandLow) * scenario.uncertaintyMultiplier)} MWh`} detail="q10–q90 proxy" tone="blue" icon="flask" explanation={{ source: 'forecast interval + scenario definition', calculation: 'Base aggregate interval width multiplied by documented factor.' }} />
                <MetricCard label="Scenario cost" value={gbp(Number(policy?.total_cost_gbp ?? 0) * scenario.costMultiplier)} detail="Sensitivity only" tone="amber" icon="market" explanation={{ source: 'policy metric + scenario definition', calculation: 'Saved cost multiplied by documented scenario factor.', limitation: 'Not a historical backtest.' }} />
                <MetricCard label="Reproducibility" value={scenario.id} detail="Versioned deterministic ID" tone="green" icon="check" explanation={{ source: 'product-analytics.ts', calculation: 'Fixed scenario ID and multipliers; no random sampling.' }} />
              </section>
              <EvidenceTable caption="Documented stress scenario assumptions" headers={['Scenario', 'Residual factor', 'Uncertainty factor', 'Cost factor']} rows={stressScenarios.map((row) => [row.label, `${number(row.residualMultiplier, 2)}×`, `${number(row.uncertaintyMultiplier, 2)}×`, `${number(row.costMultiplier, 2)}×`])} />
            </>
          )}

          {view === 'portfolio-addition' && (
            <>
              <label className="field">Hypothetical addition<select value={additionId} onChange={(event) => setAdditionId(event.target.value)}>{hypotheticalSites.map((row) => <option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
              <section className="kpi-grid section-gap">
                <MetricCard label="Renewable coverage" value={percent(additionResult.coverage, 1)} detail={`${number((additionResult.coverage - baseCoverage) * 100, 1)} pp versus artifact baseline`} tone="green" icon="match" explanation={{ source: 'forecast + deterministic site profile', calculation: 'Minimum of total demand and generation divided by total demand.' }} />
                <MetricCard label="Residual demand" value={`${number(additionResult.residual)} MWh`} detail="After hypothetical addition" icon="grid" explanation={{ source: 'forecast + deterministic site profile', calculation: 'Combined demand less combined generation, floored at zero.' }} />
                <MetricCard label="Uncertainty" value={`${number(additionResult.uncertainty)} MWh`} detail="Additive conservative proxy" tone="blue" icon="flask" explanation={{ source: 'forecast + profile assumption', calculation: 'Base interval width plus documented profile uncertainty.' }} />
                <MetricCard label="Technology HHI" value={number(additionResult.concentration, 3)} detail="Capacity concentration proxy" tone="green" icon="chart" explanation={{ source: 'site registry + deterministic profile', calculation: 'Existing HHI with documented diversification adjustment.' }} />
                <MetricCard label="Scenario cost" value={gbp(additionResult.cost)} detail="Deterministic sensitivity" tone="amber" icon="market" explanation={{ source: 'policy metric + profile assumption', calculation: 'Saved scenario cost scaled by net profile addition.', limitation: 'Not a quote or procurement decision.' }} />
              </section>
              <div className="callout warning-callout section-gap"><strong>No request-time training</strong><p>Hypothetical sites use fixed half-day energy and uncertainty assumptions. Results do not create a model, customer, generator, or contract.</p></div>
            </>
          )}
        </>
      )}
    </>
  );
}
