'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/layout/page-header';
import { LineChart } from '@/components/charts/line-chart';
import { Bars } from '@/components/charts/bars';
import { DataState } from '@/components/ui/data-state';
import { MetricCard } from '@/components/ui/metric-card';
import { useApi } from '@/lib/use-api';
import { number, percent } from '@/lib/format';
import type { Dictionary, Envelope, PortfolioMetric, PortfolioPoint } from '@/lib/types';

export default function ForecastLabPage() {
  const [method, setMethod] = useState('reconciled');
  const forecast = useApi<Envelope<PortfolioPoint[]>>(`/api/portfolio/forecast?method=${method}&limit=96`);
  const metrics = useApi<Envelope<PortfolioMetric[]>>('/api/portfolio/metrics');
  const attribution = useApi<Envelope<Dictionary[]>>('/api/portfolio/error-attribution?level=site');
  const rows = forecast.data?.data ?? [];
  const relevant = (metrics.data?.data ?? []).filter((row) => row.method === method);
  const net = relevant.find((row) => row.target === 'net');
  return (
    <>
      <PageHeader eyebrow="Forecast lab" title="Evidence before confidence." description="Compare temporal baselines, bottom-up estimators, direct portfolio models and coherent reconciled forecasts." actions={<label className="field">Forecast method<select value={method} onChange={(e) => setMethod(e.target.value)}><option value="baseline">Baseline</option><option value="bottom_up">Bottom up</option><option value="direct">Direct</option><option value="reconciled">Reconciled</option></select></label>} />
      <DataState loading={forecast.loading || metrics.loading} error={forecast.error || metrics.error} onRetry={() => { forecast.reload(); metrics.reload(); }} />
      {!forecast.loading && !forecast.error && <>
        <section className="kpi-grid">
          <MetricCard label="Net MAE" value={`${number(net?.mae, 3)} MWh`} detail="Out-of-sample absolute error" tone="blue" icon="chart" />
          <MetricCard label="Net RMSE" value={`${number(net?.rmse, 3)} MWh`} detail="Large-error sensitivity" icon="flask" />
          <MetricCard label="q10–q90 coverage" value={percent(net?.interval_coverage, 1)} detail="Empirical interval calibration" tone="green" icon="check" />
          <MetricCard label="Bias" value={`${number(net?.bias, 3)} MWh`} detail="Signed portfolio error" tone="amber" icon="alert" />
        </section>
        <section className="grid two" style={{ marginTop: 18 }}>
          <article className="card"><div className="card-head"><div><h3>Rolling backtest forecast</h3><p>Point and realised net position · MWh / half-hour</p></div><span className="badge status-active">{method}</span></div><LineChart rows={rows} unit="MWh / half-hour" series={[{ key: 'actual_net_mwh', label: 'Actual', color: '#0e121a' }, { key: 'net_point_mwh', label: 'Forecast', color: '#2f73d9' }]} /></article>
          <article className="card"><div className="card-head"><div><h3>Forecast distribution</h3><p>Calibrated q10, q50 and q90</p></div></div>{method === 'baseline' ? <div className="state-card">Baseline is deterministic and has no quantile interval.</div> : <LineChart rows={rows} unit="MWh / half-hour" series={[{ key: 'net_q10_mwh', label: 'q10', color: '#a9bad2' }, { key: 'net_q50_mwh', label: 'q50', color: '#2f73d9' }, { key: 'net_q90_mwh', label: 'q90', color: '#6f8eb8' }]} />}</article>
        </section>
        <section className="grid two" style={{ marginTop: 18 }}>
          <article className="card"><div className="card-head"><div><h3>Model comparison</h3><p>Net-position MAE by method</p></div></div><Bars rows={(metrics.data?.data ?? []).filter((row) => row.target === 'net')} labelKey="method" valueKey="mae" unit="MWh" color="var(--blue)" /></article>
          <article className="card"><div className="card-head"><div><h3>Error attribution</h3><p>Largest site contributions</p></div></div><Bars rows={(attribution.data?.data ?? []).slice(0, 8)} labelKey="site_id" valueKey={attribution.data?.data[0] && 'absolute_error_contribution_mwh' in attribution.data.data[0] ? 'absolute_error_contribution_mwh' : 'mae'} unit="MWh" /></article>
        </section>
        <div className="callout warning-callout" style={{ marginTop: 18 }}><strong>Leakage-aware evaluation</strong><p>All metrics come from expanding-window temporal folds. Realised weather is a prototype proxy and must not be interpreted as a production forecast-at-issue feed.</p></div>
      </>}
    </>
  );
}
