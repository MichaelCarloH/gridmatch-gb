'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/layout/page-header';
import { LineChart } from '@/components/charts/line-chart';
import { Bars } from '@/components/charts/bars';
import { DataState } from '@/components/ui/data-state';
import { MetricCard } from '@/components/ui/metric-card';
import { apiPost } from '@/lib/api';
import { useApi } from '@/lib/use-api';
import { gbp, number } from '@/lib/format';
import type { Dictionary, Envelope } from '@/lib/types';

export default function MarketPage() {
  const prices = useApi<Envelope<Dictionary[]>>('/api/market/prices?limit=58');
  const recommendations = useApi<Envelope<Dictionary[]>>('/api/market/hedge-recommendations?limit=96');
  const policies = useApi<Envelope<Dictionary[]>>('/api/market/policy-summary');
  const [shortCost, setShortCost] = useState(1.35);
  const [longValue, setLongValue] = useState(.65);
  const [risk, setRisk] = useState(0);
  const [simulation, setSimulation] = useState<Envelope<Dictionary> | null>(null);
  const [simError, setSimError] = useState<string | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const first = recommendations.data?.data[24] ?? recommendations.data?.data[0];
  const active = simulation?.data ?? first;
  const simulate = async () => {
    setSimLoading(true); setSimError(null);
    try {
      const result = await apiPost<Envelope<Dictionary>>('/api/market/hedge-simulate', {
        timestamp_utc: first?.timestamp_utc ?? '2025-06-20T12:00:00Z',
        forecast_model: 'bottom_up',
        short_cost_multiplier: shortCost,
        long_value_multiplier: longValue,
        risk_preference: risk
      });
      setSimulation(result);
    } catch (error) { setSimError((error as Error).message); }
    finally { setSimLoading(false); }
  };
  const loading = prices.loading || recommendations.loading || policies.loading;
  return (
    <>
      <PageHeader eyebrow="Market and hedge intelligence" title="Price uncertainty. Clear action." description="Convert a probabilistic net-position forecast into bounded hedge scenarios using explicit cost and risk assumptions." actions={<span className="badge origin-public">Public price reference</span>} />
      <DataState loading={loading} error={prices.error || recommendations.error || policies.error} />
      {!loading && <>
        <section className="kpi-grid">
          <MetricCard label="Recommended quantile" value={`q${number(Number(active?.selected_quantile ?? active?.recommended_quantile) * 100, 0)}`} detail="Asymmetric cost-aware selection" tone="green" icon="flask" />
          <MetricCard label="Hedge volume" value={`${number(active?.recommended_hedge_mwh ?? active?.recommended_mwh, 2)} MWh`} detail="Operationally bounded recommendation" tone="blue" icon="market" />
          <MetricCard label="Expected short" value={`${number(active?.expected_short_exposure_mwh, 2)} MWh`} detail="Residual under-hedge exposure" tone="amber" icon="alert" />
          <MetricCard label="Reference price" value={`${number(active?.reference_price_gbp_mwh ?? active?.market_reference_price_gbp_mwh, 2)} GBP/MWh`} detail="Public scenario proxy" icon="chart" />
        </section>
        <section className="grid two" style={{ marginTop: 18 }}>
          <article className="card"><div className="card-head"><div><h3>Public system price snapshot</h3><p>Cached Elexon evidence · GBP/MWh</p></div></div><LineChart rows={prices.data?.data ?? []} unit="GBP/MWh" series={[{ key: 'systembuyprice', label: 'System price', color: '#d99a2b' }]} /></article>
          <article className="card dark"><div className="card-head"><div><h3>Interactive assumptions</h3><p>Lightweight recomputation only</p></div></div>
            <div className="assumption-grid" style={{ gridTemplateColumns: '1fr' }}>
              <label className="range-field"><span>Short cost multiplier <b>{shortCost.toFixed(2)}</b></span><input type="range" min="1" max="2" step=".05" value={shortCost} onChange={(e) => setShortCost(Number(e.target.value))} /></label>
              <label className="range-field"><span>Long value multiplier <b>{longValue.toFixed(2)}</b></span><input type="range" min="0" max="1" step=".05" value={longValue} onChange={(e) => setLongValue(Number(e.target.value))} /></label>
              <label className="range-field"><span>Risk preference <b>{risk.toFixed(2)}</b></span><input type="range" min="-1" max="1" step=".1" value={risk} onChange={(e) => setRisk(Number(e.target.value))} /></label>
            </div>
            <button className="button green" style={{ width: '100%', marginTop: 15 }} onClick={simulate} disabled={simLoading}>{simLoading ? 'Recomputing…' : 'Recompute scenario'}</button>
            {simError && <p style={{ color: '#ff9f97' }}>{simError}</p>}
          </article>
        </section>
        <section className="grid two" style={{ marginTop: 18 }}>
          <article className="card"><div className="card-head"><div><h3>Policy cost comparison</h3><p>Historical scenario total · GBP</p></div></div><Bars rows={(policies.data?.data ?? []).filter((row) => row.policy !== 'perfect_foresight').slice(0, 6)} labelKey="policy" valueKey="total_cost_gbp" unit="GBP" color="var(--amber)" /></article>
          <article className="card"><h3>Decision context</h3><div className="detail-list"><div><span>Expected long exposure</span><b>{number(active?.expected_long_exposure_mwh, 2)} MWh</b></div><div><span>Model version</span><b>{String(active?.model_version ?? active?.hedge_model_version ?? 'hedge-decision-v1')}</b></div><div><span>Scenario total</span><b>{gbp(active?.total_cost_gbp)}</b></div></div><div className="callout warning-callout"><strong>Scenario only</strong><p>{simulation?.warnings?.[0] ?? 'Costs are modelled comparisons, not realised savings, financial advice or executable trades.'}</p></div></article>
        </section>
      </>}
    </>
  );
}
