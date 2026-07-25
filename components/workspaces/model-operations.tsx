'use client';

import { Bars } from '@/components/charts/bars';
import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { EvidenceTable } from '@/components/ui/evidence-table';
import { MetricCard } from '@/components/ui/metric-card';
import { number, percent, titleCase } from '@/lib/format';
import { useApi } from '@/lib/use-api';
import type { Dictionary, Envelope, HealthStatus, ModelRecord, PortfolioMetric, PortfolioPoint, Site } from '@/lib/types';

type ModelView = 'overview' | 'performance' | 'calibration' | 'registry' | 'incidents' | 'data-drift';

export function ModelOperations({ view }: { view: ModelView }) {
  const models = useApi<Envelope<ModelRecord[]>>('/api/models?limit=12');
  const metrics = useApi<Envelope<PortfolioMetric[]>>('/api/portfolio/metrics');
  const forecast = useApi<Envelope<PortfolioPoint[]>>('/api/portfolio/forecast?method=reconciled&limit=96');
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const health = useApi<HealthStatus>('/health');
  const siteMetrics = useApi<Envelope<Dictionary[]>>(
    view === 'performance' ? '/api/sites/dem_retail_cardiff/metrics' : null
  );
  const siteForecast = useApi<Envelope<Dictionary[]>>(
    view === 'performance' ? '/api/sites/dem_retail_cardiff/forecast?model=ml&limit=96' : null
  );
  const siteObservations = useApi<Envelope<Dictionary[]>>(
    view === 'performance' ? '/api/sites/dem_retail_cardiff/observations?limit=96' : null
  );
  const hooks = [models, metrics, forecast, sites, health, siteMetrics, siteForecast, siteObservations];
  const loading = hooks.some((hook) => hook.loading);
  const error = hooks.find((hook) => hook.error)?.error ?? null;
  const modelRows = models.data?.data ?? [];
  const metricRows = metrics.data?.data ?? [];
  const forecastRows = forecast.data?.data ?? [];
  const netMetrics = metricRows.filter((row) => row.target === 'net');
  const production = netMetrics.find((row) => row.method === 'reconciled');
  const challenger = [...netMetrics].sort((a, b) => a.mae - b.mae)[0];
  const crossingCount = forecastRows.filter((row) => row.net_q10_mwh > row.net_q50_mwh || row.net_q50_mwh > row.net_q90_mwh).length;
  const physicalCount = forecastRows.filter((row) => row.demand_point_mwh < 0 || row.generation_point_mwh < 0).length;
  const qualityIncidents = (sites.data?.data ?? []).filter((row) => row.quality_score < 98);
  const meanFirst = forecastRows.slice(0, 48).reduce((v, row) => v + row.actual_demand_mwh, 0) / Math.max(Math.min(forecastRows.length, 48), 1);
  const secondRows = forecastRows.slice(48, 96);
  const meanSecond = secondRows.reduce((v, row) => v + row.actual_demand_mwh, 0) / Math.max(secondRows.length, 1);
  const loadDrift = meanFirst ? meanSecond / meanFirst - 1 : 0;
  const reliability = {
    q10: forecastRows.length ? forecastRows.filter((row) => row.actual_net_mwh <= row.net_q10_mwh).length / forecastRows.length : 0,
    q50: forecastRows.length ? forecastRows.filter((row) => row.actual_net_mwh <= row.net_q50_mwh).length / forecastRows.length : 0,
    q90: forecastRows.length ? forecastRows.filter((row) => row.actual_net_mwh <= row.net_q90_mwh).length / forecastRows.length : 0
  };
  const metricFor = (rows: PortfolioPoint[]) => {
    const errors = rows.map((row) => row.net_point_mwh - row.actual_net_mwh);
    return {
      mae: errors.reduce((value, errorValue) => value + Math.abs(errorValue), 0) / Math.max(errors.length, 1),
      rmse: Math.sqrt(errors.reduce((value, errorValue) => value + errorValue ** 2, 0) / Math.max(errors.length, 1)),
      bias: errors.reduce((value, errorValue) => value + errorValue, 0) / Math.max(errors.length, 1)
    };
  };
  const horizonRows = [
    { horizon: 'Periods 1–48', ...metricFor(forecastRows.slice(0, 48)) },
    { horizon: 'Periods 49–96', ...metricFor(forecastRows.slice(48, 96)) }
  ];
  const settlementRows = [...new Set(forecastRows.map((row) => row.settlement_period))]
    .map((period) => ({ period, ...metricFor(forecastRows.filter((row) => row.settlement_period === period)) }))
    .sort((a, b) => b.mae - a.mae)
    .slice(0, 10);
  const weatherGroups = new Map<string, number[]>();
  (siteForecast.data?.data ?? []).forEach((row, index) => {
    const weather = siteObservations.data?.data[index];
    if (!weather) return;
    const regime =
      Number(weather.wind_speed_mps ?? 0) >= 8 ? 'High wind' :
      Number(weather.irradiance_wm2 ?? 0) >= 300 ? 'Bright' :
      Number(weather.temperature_c ?? 20) < 8 ? 'Cold' : 'Temperate';
    const values = weatherGroups.get(regime) ?? [];
    values.push(Math.abs(Number(row.point_mwh ?? 0) - Number(row.actual_mwh ?? 0)));
    weatherGroups.set(regime, values);
  });
  const weatherRows = [...weatherGroups.entries()].map(([regime, values]) => ({
    regime,
    mae: values.reduce((value, item) => value + item, 0) / Math.max(values.length, 1),
    rows: values.length
  }));
  const incidents: Dictionary[] = [
    {
      severity: health.data?.status === 'healthy' ? 'clear' : 'critical',
      incident: 'Missing artifact',
      evidence: health.data?.status === 'healthy' ? 'Required artifact manifest healthy' : 'Health endpoint reports degraded artifacts'
    },
    {
      severity: crossingCount ? 'critical' : 'clear',
      incident: 'Quantile crossing',
      evidence: `${crossingCount} crossing rows in displayed reconciled forecast`
    },
    {
      severity: physicalCount ? 'critical' : 'clear',
      incident: 'Physical-limit violation',
      evidence: `${physicalCount} negative demand or generation point forecasts`
    },
    {
      severity: challenger && production && challenger.method !== production.method && challenger.mae < production.mae ? 'review' : 'clear',
      incident: 'Challenger outperformance',
      evidence: challenger ? `${titleCase(challenger.method)} net MAE ${number(challenger.mae, 3)} MWh` : 'No metric evidence'
    },
    {
      severity: Math.abs(Number(production?.bias ?? 0)) > 0.05 ? 'review' : 'clear',
      incident: 'Persistent residual bias',
      evidence: `Reconciled net bias ${number(production?.bias, 3)} MWh`
    },
    {
      severity: qualityIncidents.length ? 'review' : 'clear',
      incident: 'Data-quality deterioration',
      evidence: `${qualityIncidents.length} sites below 98 / 100`
    }
  ];

  const title = {
    overview: ['Model operations', 'Forecast evidence with an audit trail.', 'Selection hierarchy, performance, calibration, registry lineage and incidents without request-time retraining.'],
    performance: ['Model performance', 'Compare before selecting.', 'Baseline, bottom-up, direct and reconciled metrics from leakage-aware temporal evaluation.'],
    calibration: ['Calibration', 'Intervals must earn trust.', 'Empirical q10/q50/q90 reliability, interval coverage and width.'],
    registry: ['Model registry', 'Every model has a purpose and boundary.', 'IDs, windows, features, metrics, intended use and limitations from the saved registry.'],
    incidents: ['Model incidents', 'Surface failure modes explicitly.', 'Artifact, quantile, physical, challenger, bias and data-quality checks.'],
    'data-drift': ['Data drift', 'Detect change without pretending to retrain.', 'Window comparisons and readiness signals identify review needs.']
  }[view];

  return (
    <>
      <PageHeader eyebrow={title[0]} title={title[1]} description={title[2]} actions={<span className="badge status-active">Saved artifacts · no retraining</span>} />
      <DataState loading={loading} error={error} />
      {!loading && !error && (
        <>
          {view === 'overview' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Selected forecast" value="Reconciled" detail="Coherent demand, generation and net" tone="green" icon="check" explanation={{ source: 'portfolio_metrics + Phase 7 selection', calculation: 'Selected for coherence while retaining bottom-up site traceability.' }} />
                <MetricCard label="Net MAE" value={`${number(production?.mae, 3)} MWh`} detail="Out-of-sample reconciled metric" tone="blue" icon="chart" explanation={{ source: 'portfolio_metrics.parquet', calculation: 'Mean absolute error over temporal validation folds.' }} />
                <MetricCard label="Interval coverage" value={percent(production?.interval_coverage, 1)} detail="Empirical q10–q90 reliability" tone="green" icon="flask" explanation={{ source: 'portfolio_metrics.parquet', calculation: 'Actual outcomes inside the forecast interval.' }} />
                <MetricCard label="Open incidents" value={String(incidents.filter((row) => row.severity !== 'clear').length)} detail="Derived from saved evidence" tone="amber" icon="alert" explanation={{ source: 'health, forecasts, metrics, quality', calculation: 'Count of documented checks currently requiring review.' }} />
              </section>
              <section className="grid five hierarchy section-gap">
                {[
                  ['Site model', 'Local pattern and weather response'],
                  ['Global fallback', 'Used when local evidence is insufficient'],
                  ['Bottom-up portfolio', 'Sum of traceable site forecasts'],
                  ['Direct portfolio', 'Independent challenger and hedge input'],
                  ['Reconciled model', 'Coherent selected operational view']
                ].map(([label, detail], index) => <article className={`card ${index === 4 ? 'selected-model' : ''}`} key={label}><span className="badge">{index + 1}</span><h3>{label}</h3><p>{detail}</p></article>)}
              </section>
              <div className="callout section-gap"><strong>Why reconciled?</strong><p>It preserves the site-level bottom-up evidence while enforcing demand minus generation equals net. Direct models remain visible as independent challengers because error and decision cost can rank methods differently.</p></div>
            </>
          )}

          {view === 'performance' && (
            <>
              <section className="grid two"><article className="card"><h3>Net MAE by method</h3><Bars rows={netMetrics} labelKey="method" valueKey="mae" unit="MWh" color="var(--blue)" /></article><article className="card"><h3>Net RMSE by method</h3><Bars rows={netMetrics} labelKey="method" valueKey="rmse" unit="MWh" color="var(--amber)" /></article></section>
              <EvidenceTable caption="Portfolio model metrics" headers={['Method', 'Target', 'MAE', 'RMSE', 'Bias', 'Pinball', 'Coverage', 'Horizon']} rows={metricRows.map((row) => [titleCase(row.method), titleCase(row.target), number(row.mae, 3), number(row.rmse, 3), number(row.bias, 3), number(row.pinball_loss, 3), percent(row.interval_coverage, 1), 'Day-ahead · all settlement periods'])} />
              <section className="grid two section-gap">
                <article className="card"><h3>Horizon drill-down</h3><EvidenceTable caption="Net performance by horizon" headers={['Horizon', 'MAE', 'RMSE', 'Bias']} rows={horizonRows.map((row) => [row.horizon, `${number(row.mae, 3)} MWh`, `${number(row.rmse, 3)} MWh`, `${number(row.bias, 3)} MWh`])} /></article>
                <article className="card"><h3>Settlement-period drill-down</h3><EvidenceTable caption="Worst net performance by settlement period" headers={['Period', 'MAE', 'RMSE', 'Bias']} rows={settlementRows.map((row) => [row.period, `${number(row.mae, 3)} MWh`, `${number(row.rmse, 3)} MWh`, `${number(row.bias, 3)} MWh`])} /></article>
                <article className="card"><h3>Representative site</h3><EvidenceTable caption="Taff Retail Park saved site metrics" headers={['Model', 'MAE', 'RMSE', 'Bias']} rows={(siteMetrics.data?.data ?? []).map((row) => [titleCase(String(row.model_name)), `${number(row.mae, 3)} MWh`, `${number(row.rmse, 3)} MWh`, `${number(row.bias, 3)} MWh`])} /></article>
                <article className="card"><h3>Weather regime</h3><EvidenceTable caption="Representative site performance by weather regime" headers={['Regime', 'Rows', 'MAE']} rows={weatherRows.map((row) => [row.regime, row.rows, `${number(row.mae, 3)} MWh`])} /><p className="micro muted">Deterministic regimes use displayed observed weather; they are descriptive backtest slices, not forecast-at-issue production monitoring.</p></article>
              </section>
            </>
          )}

          {view === 'calibration' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="q10 empirical reliability" value={percent(reliability.q10, 1)} detail="Target · 10%" tone="blue" icon="flask" explanation={{ source: 'reconciled forecast backtest', calculation: 'Share of actual net outcomes at or below q10.' }} />
                <MetricCard label="q50 empirical reliability" value={percent(reliability.q50, 1)} detail="Target · 50%" tone="blue" icon="flask" explanation={{ source: 'reconciled forecast backtest', calculation: 'Share of actual net outcomes at or below q50.' }} />
                <MetricCard label="q90 empirical reliability" value={percent(reliability.q90, 1)} detail="Target · 90%" tone="blue" icon="flask" explanation={{ source: 'reconciled forecast backtest', calculation: 'Share of actual net outcomes at or below q90.' }} />
                <MetricCard label="q10–q90 coverage" value={percent(production?.interval_coverage, 1)} detail="Empirical net coverage" tone="green" icon="check" explanation={{ source: 'portfolio metrics', calculation: 'Actual net outcomes within q10–q90.' }} />
              </section>
              <EvidenceTable caption="Calibration by forecast target" headers={['Target', 'Method', 'Coverage', 'Interval width', 'Pinball loss']} rows={metricRows.filter((row) => row.method === 'reconciled').map((row) => [titleCase(row.target), titleCase(row.method), percent(row.interval_coverage, 1), `${number(row.interval_width, 3)} MWh`, number(row.pinball_loss, 4)])} />
              <div className="callout warning-callout section-gap"><strong>Calibration boundary</strong><p>Reliability is recomputed from the displayed reconciled backtest rows. Aggregate coverage and pinball loss remain the saved selection metrics; neither is a production guarantee.</p></div>
            </>
          )}

          {view === 'registry' && (
            <EvidenceTable caption="Saved model registry" headers={['Model ID', 'Scope', 'Target', 'Algorithm', 'Window', 'Metric', 'Intended use', 'Limitations']} rows={modelRows.map((row) => [
              <code key={row.model_id}>{row.model_id}</code>,
              titleCase(row.scope),
              titleCase(row.target),
              titleCase(row.algorithm),
              `${String((row as unknown as Dictionary).training_start ?? 'documented')} → ${String((row as unknown as Dictionary).training_end ?? 'documented')}`,
              row.mae == null ? 'See linked metric' : `${number(row.mae, 3)} MAE`,
              row.intended_use,
              row.limitations
            ])} />
          )}

          {view === 'incidents' && (
            <EvidenceTable caption="Model and data incidents" headers={['Status', 'Check', 'Evidence', 'Response']} rows={incidents.map((row) => [
              <span className={`badge ${row.severity === 'clear' ? 'status-ready' : 'status-review'}`} key={String(row.incident)}>{String(row.severity)}</span>,
              String(row.incident),
              String(row.evidence),
              row.severity === 'clear' ? 'Continue monitoring' : 'Manual review before operational use'
            ])} />
          )}

          {view === 'data-drift' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Load-profile drift" value={percent(loadDrift, 1)} detail="Second 48 periods versus first 48" tone={Math.abs(loadDrift) > 0.15 ? 'amber' : 'green'} icon="chart" explanation={{ source: 'portfolio forecast actuals', calculation: 'Mean demand in second displayed window divided by first, less one.', limitation: 'Short-window monitoring proxy.' }} />
                <MetricCard label="Weather-response drift" value="Monitor" detail="No saved production drift artifact" tone="amber" icon="flask" explanation={{ source: 'model limitations', calculation: 'Status reflects absence of a dedicated live weather-response drift artifact.' }} />
                <MetricCard label="Quality deterioration" value={String(qualityIncidents.length)} detail="Sites below 98 / 100" tone="amber" icon="alert" explanation={{ source: 'site quality reports', calculation: 'Threshold count.' }} />
                <MetricCard label="Model decline" value={production && challenger ? `${number(production.mae - challenger.mae, 3)} MWh` : 'Unavailable'} detail="Selected MAE minus best saved challenger" tone="blue" icon="chart" explanation={{ source: 'portfolio metrics', calculation: 'Reconciled net MAE less lowest saved net MAE.' }} />
              </section>
              <div className="callout warning-callout section-gap"><strong>No fabricated production status</strong><p>These are artifact-backed prototype monitoring signals. There is no live retraining scheduler, production feature store, or automated model promotion workflow.</p></div>
            </>
          )}
        </>
      )}
    </>
  );
}
