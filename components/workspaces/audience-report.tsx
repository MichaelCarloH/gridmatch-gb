'use client';

import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { MetricCard } from '@/components/ui/metric-card';
import { gbp, number, percent } from '@/lib/format';
import { portfolioTotals, sum } from '@/lib/product-analytics';
import { useApi } from '@/lib/use-api';
import type { Dictionary, Envelope, PortfolioMetric, PortfolioPoint } from '@/lib/types';

export function AudienceReport({
  audience
}: {
  audience: 'generator' | 'portfolio';
}) {
  const forecast = useApi<Envelope<PortfolioPoint[]>>('/api/portfolio/forecast?method=reconciled&limit=48');
  const generators = useApi<Envelope<Dictionary[]>>('/api/matching/generators?allocation_type=realised&matching_mode=local_preference');
  const matching = useApi<Envelope<Dictionary>>('/api/matching/summary');
  const policies = useApi<Envelope<Dictionary[]>>('/api/market/policy-summary');
  const metrics = useApi<Envelope<PortfolioMetric[]>>('/api/portfolio/metrics?method=reconciled');
  const hooks = [forecast, generators, matching, policies, metrics];
  const loading = hooks.some((hook) => hook.loading);
  const error = hooks.find((hook) => hook.error)?.error ?? null;
  const totals = portfolioTotals(forecast.data?.data ?? []);
  const generatorRows = generators.data?.data ?? [];
  const policy = policies.data?.data.find((row) => row.policy === 'validation_optimised') ?? policies.data?.data[0];
  const net = metrics.data?.data.find((row) => row.target === 'net');
  const analysis = matching.data?.data.analysis;
  const isGenerator = audience === 'generator';
  return (
    <>
      <PageHeader
        eyebrow={`${audience} report`}
        title={isGenerator ? 'Renewable portfolio evidence.' : 'Portfolio operations evidence.'}
        description="Print-safe summary generated from the same governed artifacts used throughout the product."
        actions={<button className="button ghost" onClick={() => window.print()}>Print report</button>}
      />
      <DataState loading={loading} error={error} />
      {!loading && !error && (
        <section className="print-report">
          <div className="callout warning-callout">
            <strong>Data and claims disclosure</strong>
            <p>Portfolio, forecasts and allocations are simulated. Prices are public scenario references. Values are not invoices, trades, savings claims or physical routing.</p>
          </div>
          <section className="kpi-grid section-gap">
            {isGenerator ? (
              <>
                <MetricCard label="Available generation" value={`${number(sum(generatorRows, 'available_generation_mwh'))} MWh`} detail="Saved realised matching window" tone="green" icon="bolt" explanation={{ source: 'generator matching summary', calculation: 'Sum of generator available MWh.' }} />
                <MetricCard label="Matched generation" value={`${number(sum(generatorRows, 'matched_generation_mwh'))} MWh`} detail="Commercially allocated" tone="green" icon="match" explanation={{ source: 'generator matching summary', calculation: 'Sum of matched generator MWh.' }} />
                <MetricCard label="Unused generation" value={`${number(sum(generatorRows, 'unused_generation_mwh'))} MWh`} detail="Not allocated to business demand" tone="amber" icon="alert" explanation={{ source: 'generator matching summary', calculation: 'Sum of unused generation.' }} />
                <MetricCard label="Mean offtake coverage" value={percent(generatorRows.length ? sum(generatorRows, 'offtake_coverage') / generatorRows.length : 0, 1)} detail="Across simulated assets" tone="green" icon="match" explanation={{ source: 'generator matching summary', calculation: 'Mean generator offtake coverage.' }} />
              </>
            ) : (
              <>
                <MetricCard label="Forecast demand" value={`${number(totals.demand)} MWh`} detail="Next 48 half-hours" tone="blue" icon="chart" explanation={{ source: 'portfolio forecast', calculation: 'Sum of demand point forecasts.' }} />
                <MetricCard label="Forecast generation" value={`${number(totals.generation)} MWh`} detail="Next 48 half-hours" tone="green" icon="bolt" explanation={{ source: 'portfolio forecast', calculation: 'Sum of generation point forecasts.' }} />
                <MetricCard label="Renewable coverage" value={percent(analysis?.average_forecast_renewable_match_rate, 1)} detail="Commercial allocation" tone="green" icon="match" explanation={{ source: 'matching summary', calculation: 'Matched renewable MWh divided by demand.' }} />
                <MetricCard label="Net MAE" value={`${number(net?.mae, 3)} MWh`} detail="Reconciled out-of-sample" tone="blue" icon="flask" explanation={{ source: 'portfolio metrics', calculation: 'Mean absolute net-position error.' }} />
                <MetricCard label="Scenario cost" value={gbp(policy?.total_cost_gbp)} detail="Saved validation window" tone="amber" icon="market" explanation={{ source: 'policy metrics', calculation: 'Day-ahead plus imbalance scenario cost.', limitation: 'Not realised cost or savings.' }} />
                <MetricCard label="p95 / CVaR95" value={`${gbp(policy?.p95_period_cost_gbp)} / ${gbp(policy?.cvar95_period_cost_gbp)}`} detail="Period tail-cost evidence" tone="amber" icon="alert" explanation={{ source: 'policy metrics', calculation: '95th percentile and conditional tail mean.' }} />
              </>
            )}
          </section>
          <article className="card section-gap">
            <h3>Method and ownership</h3>
            <div className="detail-list">
              <div><span>Forecast</span><b>Saved reconciled probabilistic model</b></div>
              <div><span>Matching</span><b>Half-hour commercial allocation</b></div>
              <div><span>Procurement execution</span><b>Licensed supplier or utility partner</b></div>
              <div><span>Model version</span><b>portfolio-v1 / matching-v1 / hedge-decision-v1</b></div>
              <div><span>Data origin</span><b>Simulated portfolio · public scenario price</b></div>
            </div>
          </article>
        </section>
      )}
    </>
  );
}
