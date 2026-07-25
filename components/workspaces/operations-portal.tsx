'use client';

import { useMemo, useState } from 'react';
import { LineChart } from '@/components/charts/line-chart';
import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { EvidenceTable } from '@/components/ui/evidence-table';
import { MetricCard } from '@/components/ui/metric-card';
import { gbp, number, percent, titleCase } from '@/lib/format';
import { portfolioTotals, sum } from '@/lib/product-analytics';
import { useApi } from '@/lib/use-api';
import type { Dictionary, Envelope, MatchingPeriod, PortfolioMetric, PortfolioPoint, Site } from '@/lib/types';

type OperationsView =
  | 'overview'
  | 'portfolio'
  | 'forecasts'
  | 'matching'
  | 'risk'
  | 'scenarios';

export function OperationsPortal({ view }: { view: OperationsView }) {
  const [shortMultiplier, setShortMultiplier] = useState(1.35);
  const [longMultiplier, setLongMultiplier] = useState(0.7);
  const [outage, setOutage] = useState(false);
  const [demandShock, setDemandShock] = useState(0);
  const [windStress, setWindStress] = useState(0);
  const [solarStress, setSolarStress] = useState(0);
  const [missingData, setMissingData] = useState(false);
  const [method, setMethod] = useState('reconciled');
  const forecast = useApi<Envelope<PortfolioPoint[]>>(`/api/portfolio/forecast?method=${method}&limit=96`);
  const matching = useApi<Envelope<MatchingPeriod[]>>('/api/matching/periods?allocation_type=forecast&matching_mode=local_preference&limit=96');
  const realised = useApi<Envelope<MatchingPeriod[]>>('/api/matching/periods?allocation_type=realised&matching_mode=local_preference&limit=96');
  const hedge = useApi<Envelope<Dictionary[]>>('/api/market/hedge-recommendations?limit=96');
  const policies = useApi<Envelope<Dictionary[]>>('/api/market/policy-summary');
  const metrics = useApi<Envelope<PortfolioMetric[]>>('/api/portfolio/metrics');
  const attribution = useApi<Envelope<Dictionary[]>>('/api/portfolio/error-attribution?level=site');
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const hooks = [forecast, matching, realised, hedge, policies, metrics, attribution, sites];
  const loading = hooks.some((hook) => hook.loading);
  const error = hooks.find((hook) => hook.error)?.error ?? null;
  const rows = forecast.data?.data ?? [];
  const matchRows = matching.data?.data ?? [];
  const realisedRows = realised.data?.data ?? [];
  const hedgeRows = hedge.data?.data ?? [];
  const totals = portfolioTotals(rows);
  const recommended = sum(hedgeRows, 'recommended_mwh');
  const policy = policies.data?.data.find((row) => row.policy === 'validation_optimised') ?? policies.data?.data[0];
  const netMetric = metrics.data?.data.find((row) => row.method === method && row.target === 'net');
  const lowQuality = (sites.data?.data ?? []).filter((row) => row.quality_score < 98);
  const generationSites = (sites.data?.data ?? []).filter((row) => row.site_role === 'generation');
  const windCapacity = generationSites.filter((row) => row.technology === 'wind').reduce((value, row) => value + row.installed_capacity_mw, 0);
  const solarCapacity = generationSites.filter((row) => row.technology === 'solar').reduce((value, row) => value + row.installed_capacity_mw, 0);
  const renewableCapacity = windCapacity + solarCapacity || 1;
  const demandDeviation = Math.abs(totals.demand - totals.actualDemand);
  const generationDeviation = Math.abs(totals.generation - totals.actualGeneration);
  const deviationRows = [
    { driver: 'Demand error', value: demandDeviation, method: 'Absolute forecast demand less actual demand' },
    { driver: 'Solar error', value: generationDeviation * solarCapacity / renewableCapacity, method: 'Generation error allocated by solar capacity share' },
    { driver: 'Wind error', value: generationDeviation * windCapacity / renewableCapacity, method: 'Generation error allocated by wind capacity share' },
    { driver: 'Matching deviation', value: Math.abs(sum(matchRows as unknown as Dictionary[], 'matched_mwh') - sum(realisedRows as unknown as Dictionary[], 'matched_mwh')), method: 'Absolute planned less realised matched MWh' },
    { driver: 'Price exposure', value: sum(hedgeRows, 'imbalance_cost_gbp'), method: 'Saved imbalance scenario cost (GBP)' }
  ];
  const scenario = useMemo(() => {
    const demandFactor = 1 + demandShock / 100;
    const renewableStress = (windStress * windCapacity + solarStress * solarCapacity) / (100 * renewableCapacity);
    const renewableFactor = Math.max(0, 1 - renewableStress - (outage ? 0.25 : 0));
    const residual = Math.max(totals.demand * demandFactor - totals.generation * renewableFactor, 0);
    const baseCost = Number(policy?.total_cost_gbp ?? 0);
    return {
      demand: totals.demand * demandFactor,
      generation: totals.generation * renewableFactor,
      residual,
      adjustment: residual - totals.residual,
      uncertaintyMultiplier: missingData ? 1.4 : 1,
      cost: baseCost * (shortMultiplier / 1.35) * (2 - longMultiplier / 0.7) * demandFactor
    };
  }, [demandShock, longMultiplier, missingData, outage, policy?.total_cost_gbp, renewableCapacity, shortMultiplier, solarCapacity, solarStress, totals, windCapacity, windStress]);

  const header = {
    overview: ['Portfolio operations', 'The complete half-hourly position.', 'Planned demand, renewable generation, allocation, residual need, adjustment and risk in one control room.'],
    portfolio: ['Portfolio position', 'Plan every settlement period.', 'Forecast, contracted volume, recommended adjustment and realised outcome remain explicitly separate.'],
    forecasts: ['Forecast operations', 'Uncertainty before action.', 'Compare demand, generation and net position across the saved forecast hierarchy.'],
    matching: ['Matching operations', 'Allocation and residual position.', 'Commercial renewable allocation and unmatched demand for every half-hour.'],
    risk: ['Portfolio risk', 'Find the drivers, not just the total.', 'Short and long exposure, tail-cost scenarios, bias, concentration and incidents.'],
    scenarios: ['Bounded scenarios', 'Stress the plan without retraining.', 'Deterministic controls alter displayed assumptions only; they never execute trades or retrain models.']
  }[view];

  return (
    <>
      <PageHeader eyebrow={header[0]} title={header[1]} description={header[2]} actions={view === 'forecasts' ? <label className="field">Forecast method<select value={method} onChange={(event) => setMethod(event.target.value)}><option value="baseline">Baseline</option><option value="bottom_up">Bottom up</option><option value="direct">Direct</option><option value="reconciled">Reconciled</option></select></label> : <span className="badge scenario-badge">Decision support only</span>} />
      <DataState loading={loading} error={error} />
      {!loading && !error && (
        <>
          {(view === 'overview' || view === 'portfolio') && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Forecast demand" value={`${number(totals.demand)} MWh`} detail="Displayed 96 half-hours" tone="blue" icon="chart" explanation={{ source: 'portfolio_forecasts.parquet', calculation: 'Sum of selected-method demand point forecasts.' }} />
                <MetricCard label="Renewable generation" value={`${number(totals.generation)} MWh`} detail="Wind and solar point forecast" tone="green" icon="bolt" explanation={{ source: 'portfolio_forecasts.parquet', calculation: 'Sum of generation point forecasts.' }} />
                <MetricCard label="Matched renewable volume" value={`${number(sum(matchRows as unknown as Dictionary[], 'matched_mwh'))} MWh`} detail="Forecast local-preference allocation" tone="green" icon="match" explanation={{ source: 'matching_period_summary.parquet', calculation: 'Sum of commercial matched MWh.' }} />
                <MetricCard label="Residual requirement" value={`${number(sum(matchRows as unknown as Dictionary[], 'residual_grid_demand_mwh'))} MWh`} detail="Unmatched forecast demand" icon="grid" explanation={{ source: 'matching_period_summary.parquet', calculation: 'Sum of forecast demand not commercially allocated.' }} />
                <MetricCard label="Current contracted volume" value={`${number(recommended)} MWh`} detail="Saved recommendation proxy" tone="amber" icon="market" explanation={{ source: 'hedge_recommendations.parquet', calculation: 'Sum of current saved recommendation; no executed trade state exists.', limitation: 'Prototype has no live contract ledger.' }} />
                <MetricCard label="Recommended adjustment" value={`${number(recommended - totals.residual)} MWh`} detail="Contracted proxy less expected residual" tone="amber" icon="market" explanation={{ source: 'forecast + hedge artifacts', calculation: 'Saved recommended volume less positive forecast net requirement.' }} />
                <MetricCard label="q10–q90 range" value={`${number(totals.demandLow)}–${number(totals.demandHigh)} MWh`} detail="Demand forecast uncertainty" tone="blue" icon="flask" explanation={{ source: 'portfolio forecast', calculation: 'Sums of displayed demand q10 and q90.' }} />
                <MetricCard label="Realised net result" value={`${number(totals.actualDemand - totals.actualGeneration)} MWh`} detail="Backtest outcome, kept separate" icon="check" explanation={{ source: 'portfolio forecast backtest', calculation: 'Actual demand less actual generation.' }} />
              </section>
              {view === 'portfolio' && <EvidenceTable caption="Half-hourly portfolio position" headers={['Period', 'Demand', 'Renewables', 'Matched', 'Residual', 'Contracted', 'Adjustment', 'Realised']} rows={rows.slice(0, 48).map((row, index) => {
                const match = matchRows[index];
                const hedgeRow = hedgeRows[index];
                const contracted = Number(hedgeRow?.recommended_mwh ?? 0);
                const residual = Number(match?.residual_grid_demand_mwh ?? row.net_point_mwh);
                return [row.settlement_period, `${number(row.demand_point_mwh, 2)} MWh`, `${number(row.generation_point_mwh, 2)} MWh`, `${number(match?.matched_mwh, 2)} MWh`, `${number(residual, 2)} MWh`, `${number(contracted, 2)} MWh`, `${number(contracted - residual, 2)} MWh`, `${number(row.actual_net_mwh, 2)} MWh`];
              })} />}
              <div className="section-gap">
                <EvidenceTable caption="Planned versus realised deviation attribution" headers={['Driver', 'Attributed value', 'Documented method']} rows={deviationRows.map((row) => [row.driver, row.driver === 'Price exposure' ? gbp(row.value) : `${number(row.value, 2)} MWh`, row.method])} />
              </div>
            </>
          )}

          {view === 'forecasts' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Net MAE" value={`${number(netMetric?.mae, 3)} MWh`} detail={`${titleCase(method)} · out-of-sample`} tone="blue" icon="chart" explanation={{ source: 'portfolio_metrics.parquet', calculation: 'Mean absolute error across temporal validation folds.' }} />
                <MetricCard label="Bias" value={`${number(netMetric?.bias, 3)} MWh`} detail="Signed net-position error" tone="amber" icon="alert" explanation={{ source: 'portfolio_metrics.parquet', calculation: 'Mean forecast minus actual error.' }} />
                <MetricCard label="Coverage" value={percent(netMetric?.interval_coverage, 1)} detail="Empirical q10–q90 coverage" tone="green" icon="check" explanation={{ source: 'portfolio_metrics.parquet', calculation: 'Share of actuals inside q10–q90.' }} />
                <MetricCard label="Interval width" value={`${number(netMetric?.interval_width, 3)} MWh`} detail="Mean q90 less q10" icon="flask" explanation={{ source: 'portfolio_metrics.parquet', calculation: 'Mean forecast interval width.' }} />
              </section>
              <section className="grid two section-gap"><article className="card"><h3>Planned net position</h3><LineChart rows={rows} unit="MWh" series={[{ key: 'net_point_mwh', label: 'Plan', color: '#2f73d9' }, { key: 'actual_net_mwh', label: 'Realised', color: '#0e121a' }]} /></article><article className="card"><h3>Uncertainty</h3><LineChart rows={rows} unit="MWh" series={[{ key: 'net_q10_mwh', label: 'q10', color: '#a9bad2' }, { key: 'net_q50_mwh', label: 'q50', color: '#2f73d9' }, { key: 'net_q90_mwh', label: 'q90', color: '#6f8eb8' }]} /></article></section>
            </>
          )}

          {view === 'matching' && (
            <>
              <section className="grid two"><article className="card"><h3>Planned allocation</h3><LineChart rows={matchRows} unit="MWh" series={[{ key: 'total_demand_mwh', label: 'Demand', color: '#2f73d9' }, { key: 'matched_mwh', label: 'Matched', color: '#4ca855' }, { key: 'residual_grid_demand_mwh', label: 'Residual', color: '#0e121a' }]} /></article><article className="card"><h3>Planned versus realised</h3><LineChart rows={matchRows.map((row, index) => ({ ...row, realised_matched_mwh: realisedRows[index]?.matched_mwh }))} unit="MWh" series={[{ key: 'matched_mwh', label: 'Planned', color: '#2f73d9' }, { key: 'realised_matched_mwh', label: 'Realised', color: '#0e121a' }]} /></article></section>
              <div className="callout section-gap"><strong>Commercial allocation</strong><p>Matching is conservation-tested commercial allocation in the same half-hour, not physical power routing.</p></div>
            </>
          )}

          {view === 'risk' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Expected short volume" value={`${number(sum(hedgeRows, 'expected_short_exposure_mwh'))} MWh`} detail="Saved scenario expectation" tone="amber" icon="alert" explanation={{ source: 'hedge recommendations', calculation: 'Sum of expected short exposure.' }} />
                <MetricCard label="Expected long volume" value={`${number(sum(hedgeRows, 'expected_long_exposure_mwh'))} MWh`} detail="Saved scenario expectation" tone="blue" icon="market" explanation={{ source: 'hedge recommendations', calculation: 'Sum of expected long exposure.' }} />
                <MetricCard label="Scenario cost" value={gbp(policy?.total_cost_gbp)} detail="Validation window" tone="amber" icon="market" explanation={{ source: 'hedge policy metrics', calculation: 'Total simulated policy cost.' }} />
                <MetricCard label="p95 period cost" value={gbp(policy?.p95_period_cost_gbp)} detail="Tail-cost percentile" tone="amber" icon="chart" explanation={{ source: 'hedge policy metrics', calculation: '95th percentile simulated period cost.' }} />
                <MetricCard label="CVaR95" value={gbp(policy?.cvar95_period_cost_gbp)} detail="Mean cost beyond p95" tone="amber" icon="alert" explanation={{ source: 'hedge policy metrics', calculation: 'Mean simulated period cost at or beyond p95.' }} />
                <MetricCard label="Net bias" value={`${number(netMetric?.bias, 3)} MWh`} detail="Persistent signed error signal" tone="blue" icon="chart" explanation={{ source: 'portfolio metrics', calculation: 'Mean signed net-position error.' }} />
                <MetricCard label="Quality incidents" value={String(lowQuality.length)} detail="Sites below 98 / 100" icon="alert" explanation={{ source: 'site quality reports', calculation: 'Count of sites below quality threshold.' }} />
              </section>
              <EvidenceTable caption="Forecast-error drivers" headers={['Site', 'Technology', 'Region', 'Error share', 'Bias']} rows={(attribution.data?.data ?? []).slice(0, 10).map((row) => [String(row.site_id), titleCase(String(row.technology)), String(row.region), percent(row.absolute_error_share, 1), `${number(row.bias_mwh, 3)} MWh`])} />
            </>
          )}

          {view === 'scenarios' && (
            <>
              <section className="assumption-grid">
                <label className="range-field"><span>Short-cost multiplier <b>{number(shortMultiplier, 2)}×</b></span><input aria-label="Short-cost multiplier" type="range" min="1" max="2" step=".05" value={shortMultiplier} onChange={(event) => setShortMultiplier(Number(event.target.value))} /></label>
                <label className="range-field"><span>Long-value multiplier <b>{number(longMultiplier, 2)}×</b></span><input aria-label="Long-value multiplier" type="range" min=".2" max="1" step=".05" value={longMultiplier} onChange={(event) => setLongMultiplier(Number(event.target.value))} /></label>
                <label className="range-field"><span>Customer demand shock <b>{demandShock}%</b></span><input aria-label="Customer demand shock" type="range" min="-10" max="25" value={demandShock} onChange={(event) => setDemandShock(Number(event.target.value))} /></label>
                <label className="range-field"><span>Low-wind stress <b>{windStress}%</b></span><input aria-label="Low-wind stress" type="range" min="0" max="50" value={windStress} onChange={(event) => setWindStress(Number(event.target.value))} /></label>
                <label className="range-field"><span>Solar shortfall <b>{solarStress}%</b></span><input aria-label="Solar shortfall" type="range" min="0" max="50" value={solarStress} onChange={(event) => setSolarStress(Number(event.target.value))} /></label>
                <label className="range-field checkbox-field"><span>Largest generator outage</span><input aria-label="Largest generator outage" type="checkbox" checked={outage} onChange={(event) => setOutage(event.target.checked)} /></label>
                <label className="range-field checkbox-field"><span>Missing-data degradation</span><input aria-label="Missing-data degradation" type="checkbox" checked={missingData} onChange={(event) => setMissingData(event.target.checked)} /></label>
                <label className="field">Forecast method<select value={method} onChange={(event) => setMethod(event.target.value)}><option value="baseline">Baseline</option><option value="bottom_up">Bottom up</option><option value="direct">Direct</option><option value="reconciled">Reconciled</option></select></label>
              </section>
              <section className="kpi-grid section-gap">
                <MetricCard label="Stressed demand" value={`${number(scenario.demand)} MWh`} detail="Deterministic display scenario" tone="blue" icon="chart" explanation={{ source: 'portfolio forecast + user control', calculation: 'Base demand multiplied by demand-shock assumption.' }} />
                <MetricCard label="Stressed renewables" value={`${number(scenario.generation)} MWh`} detail="Weather and outage assumptions" tone="green" icon="bolt" explanation={{ source: 'portfolio forecast + user controls', calculation: 'Base generation reduced by bounded stress assumptions.' }} />
                <MetricCard label="Stressed residual" value={`${number(scenario.residual)} MWh`} detail="Demand less renewables" icon="grid" explanation={{ source: 'deterministic scenario', calculation: 'Stressed demand less stressed generation, floored at zero.' }} />
                <MetricCard label="Suggested adjustment" value={`${number(scenario.adjustment)} MWh`} detail="Versus base residual" tone="amber" icon="market" explanation={{ source: 'deterministic scenario', calculation: 'Stressed residual less base residual.', limitation: 'Not a trade instruction.' }} />
                <MetricCard label="Uncertainty degradation" value={`${number(scenario.uncertaintyMultiplier, 1)}×`} detail={missingData ? 'Missing-data review active' : 'Base interval retained'} tone="blue" icon="flask" explanation={{ source: 'bounded missing-data control', calculation: 'Fixed 1.4× uncertainty factor when missing-data degradation is enabled.' }} />
                <MetricCard label="Scenario cost" value={gbp(scenario.cost)} detail="Sensitivity proxy only" tone="amber" icon="market" explanation={{ source: 'policy metric + user controls', calculation: 'Base scenario cost scaled by bounded price and demand assumptions.', limitation: 'Not a backtest or realised cost.' }} />
              </section>
              <div className="callout warning-callout section-gap"><strong>Operational boundary</strong><p>Controls do not retrain models, mutate saved artifacts, or execute procurement. Missing-data degradation is represented by widening uncertainty and raising a review incident.</p></div>
            </>
          )}
        </>
      )}
    </>
  );
}
