'use client';

import { PageHeader } from '@/components/layout/page-header';
import { LineChart } from '@/components/charts/line-chart';
import { DataState } from '@/components/ui/data-state';
import { MetricCard } from '@/components/ui/metric-card';
import { useApi } from '@/lib/use-api';
import { gbp, number, percent, timestamp } from '@/lib/format';
import type { Dictionary, Envelope, PortfolioPoint, Site } from '@/lib/types';

export default function DashboardPage() {
  const forecast = useApi<Envelope<PortfolioPoint[]>>('/api/portfolio/forecast?method=reconciled&limit=48');
  const matching = useApi<Envelope<Dictionary>>('/api/matching/summary');
  const hedge = useApi<Envelope<Dictionary[]>>('/api/market/hedge-recommendations?limit=48');
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const rows = forecast.data?.data ?? [];
  const hedgeRows = hedge.data?.data ?? [];
  const totals = rows.reduce((sum, row) => ({
    demand: sum.demand + row.demand_point_mwh,
    generation: sum.generation + row.generation_point_mwh,
    net: sum.net + row.net_point_mwh,
    width: sum.width + (row.net_q90_mwh - row.net_q10_mwh)
  }), { demand: 0, generation: 0, net: 0, width: 0 });
  const recommended = hedgeRows.reduce((sum, row) => sum + Number(row.recommended_mwh ?? 0), 0);
  const expectedCost = hedgeRows.reduce((sum, row) => sum + Number(row.total_cost_gbp ?? 0), 0);
  const matchRate = matching.data?.data.analysis?.average_forecast_renewable_match_rate;
  const lowQuality = (sites.data?.data ?? []).filter((site) => site.quality_score < 98);
  const loading = forecast.loading || matching.loading || hedge.loading;
  const error = forecast.error || matching.error || hedge.error;
  return (
    <>
      <PageHeader eyebrow="Portfolio control room" title="Tomorrow, in one view." description="Day-ahead portfolio outlook from saved reconciled forecasts, renewable allocations and hedge policy artifacts." actions={<span className="badge status-active">Live demo artifacts</span>} />
      <DataState loading={loading} error={error} onRetry={() => { forecast.reload(); matching.reload(); hedge.reload(); }} />
      {!loading && !error && <>
        <section className="kpi-grid">
          <MetricCard label="Tomorrow demand" value={`${number(totals.demand)} MWh`} detail="Reconciled day-ahead point forecast" tone="blue" icon="chart" />
          <MetricCard label="Renewable generation" value={`${number(totals.generation)} MWh`} detail="Solar and wind portfolio output" tone="green" icon="bolt" />
          <MetricCard label="Net position" value={`${number(totals.net)} MWh`} detail={totals.net >= 0 ? 'Expected grid import' : 'Expected export'} icon="match" />
          <MetricCard label="Recommended hedge" value={`${number(recommended)} MWh`} detail="Sum of half-hourly recommendations" tone="amber" icon="market" />
          <MetricCard label="Renewable match" value={percent(matchRate)} detail="Forecast local-preference coverage" tone="green" icon="match" />
          <MetricCard label="Forecast uncertainty" value={`${number(totals.width / Math.max(rows.length, 1), 2)} MWh`} detail="Mean net q10–q90 interval width" tone="blue" icon="flask" />
          <MetricCard label="Scenario cost" value={gbp(expectedCost)} detail="Modelled, not realised savings" tone="amber" icon="market" />
          <MetricCard label="Quality alerts" value={String(lowQuality.length)} detail={`${sites.data?.meta?.count ?? 0} sites monitored`} icon="alert" />
        </section>
        <section className="split" style={{ marginTop: 18 }}>
          <article className="card">
            <div className="card-head"><div><h3>Portfolio energy outlook</h3><p>First 48 half-hours · issue {timestamp(rows[0]?.issue_time_utc)}</p></div><span className="badge status-ready">Reconciled</span></div>
            <LineChart rows={rows} unit="MWh / half-hour" series={[
              { key: 'demand_point_mwh', label: 'Demand', color: '#2f73d9' },
              { key: 'generation_point_mwh', label: 'Generation', color: '#4ca855' },
              { key: 'net_point_mwh', label: 'Net', color: '#0e121a' }
            ]} />
          </article>
          <aside className="card dark">
            <div className="card-head"><div><h3>Decision brief</h3><p>Artifact-derived exceptions</p></div><span className="live-dot" /></div>
            <div className="rank-list">
              <div className="rank-row"><i>1</i><span>Renewable coverage</span><b>{percent(matchRate)}</b></div>
              <div className="rank-row"><i>2</i><span>Residual grid need</span><b>{number(matching.data?.data.analysis?.total_realised_residual_grid_requirement_mwh)} MWh</b></div>
              <div className="rank-row"><i>3</i><span>Sites below 98 quality</span><b>{lowQuality.length}</b></div>
            </div>
            <div className="callout warning-callout" style={{ marginTop: 22 }}><strong>Scenario boundary</strong><p>Costs use a non-contemporaneous public price reference and are not realised supplier savings.</p></div>
          </aside>
        </section>
      </>}
    </>
  );
}
