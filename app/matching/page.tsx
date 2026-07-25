'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/layout/page-header';
import { LineChart } from '@/components/charts/line-chart';
import { DataState } from '@/components/ui/data-state';
import { MetricCard } from '@/components/ui/metric-card';
import { useApi } from '@/lib/use-api';
import { number, percent } from '@/lib/format';
import type { Dictionary, Envelope, MatchingPeriod } from '@/lib/types';

export default function MatchingPage() {
  const [period, setPeriod] = useState(1);
  const [allocationType, setAllocationType] = useState('realised');
  const [mode, setMode] = useState('local_preference');
  const summary = useApi<Envelope<Dictionary>>('/api/matching/summary');
  const periods = useApi<Envelope<MatchingPeriod[]>>(`/api/matching/periods?allocation_type=${allocationType}&matching_mode=${mode}&limit=96`);
  const allocations = useApi<Envelope<Dictionary[]>>(`/api/matching/allocations?allocation_type=${allocationType}&matching_mode=${mode}&settlement_period=${period}&limit=100`);
  const analysis = summary.data?.data.analysis;
  const rows = periods.data?.data ?? [];
  const selected = rows.find((row) => row.settlement_period === period) ?? rows[0];
  const allocationRows = allocations.data?.data ?? [];
  const generatorIds = [...new Set(allocationRows.map((row) => String(row.generator_site_id)))].slice(0, 4);
  const consumerIds = [...new Set(allocationRows.map((row) => String(row.consumer_site_id)))].slice(0, 4);
  return (
    <>
      <PageHeader eyebrow="Renewable allocation" title="Match every half-hour." description="Commercially allocate renewable generation to demand while preserving settlement-period conservation." actions={<><label className="field">Basis<select value={allocationType} onChange={(e) => setAllocationType(e.target.value)}><option value="realised">Realised</option><option value="forecast">Forecast</option></select></label><label className="field">Mode<select value={mode} onChange={(e) => setMode(e.target.value)}><option value="local_preference">Local preference</option><option value="maximum_match">Maximum match</option></select></label></>} />
      <DataState loading={summary.loading || periods.loading} error={summary.error || periods.error} />
      {!summary.loading && !summary.error && <>
        <section className="kpi-grid">
          <MetricCard label="Matched energy" value={`${number(selected?.matched_mwh, 2)} MWh`} detail={`Settlement period ${selected?.settlement_period ?? '—'}`} tone="green" icon="match" />
          <MetricCard label="Renewable coverage" value={percent(selected?.renewable_match_rate, 1)} detail="Demand served by allocation" tone="green" icon="bolt" />
          <MetricCard label="Residual grid import" value={`${number(selected?.residual_grid_demand_mwh, 2)} MWh`} detail="Unmatched demand" tone="blue" icon="grid" />
          <MetricCard label="Unused generation" value={`${number(selected?.unused_generation_mwh, 2)} MWh`} detail="Available renewable spill" tone="amber" icon="alert" />
        </section>
        <section className="split" style={{ marginTop: 18 }}>
          <article className="card"><div className="card-head"><div><h3>Matching profile</h3><p>{allocationType} · {mode.replaceAll('_', ' ')}</p></div></div><LineChart rows={rows} unit="MWh / half-hour" series={[{ key: 'total_demand_mwh', label: 'Demand', color: '#2f73d9' }, { key: 'total_generation_mwh', label: 'Generation', color: '#4ca855' }, { key: 'matched_mwh', label: 'Matched', color: '#0e121a' }]} /></article>
          <aside className="card dark"><h3>Period control</h3><p className="muted">Slide through the GB settlement day.</p><label className="range-field" style={{ display: 'block', color: 'var(--ink)' }}><span style={{ display: 'flex', justifyContent: 'space-between' }}>Settlement period <b>{period}</b></span><input type="range" min="1" max="50" value={period} onChange={(e) => setPeriod(Number(e.target.value))} /></label><div className="rank-list" style={{ marginTop: 18 }}><div className="rank-row"><i>✓</i><span>Conservation check</span><b>{summary.data?.data.conservation_passed ? 'Passed' : 'Review'}</b></div><div className="rank-row"><i>↔</i><span>Mean match distance</span><b>{number(analysis?.average_realised_matching_distance_km)} km</b></div></div></aside>
        </section>
        <article className="card" style={{ marginTop: 18 }}><div className="card-head"><div><h3>Allocation matrix</h3><p>Generator → consumer matched MWh for period {period}</p></div><span className="badge status-active">{allocationRows.length} allocations</span></div>
          {!allocationRows.length ? <DataState empty /> : <div className="allocation-matrix"><div className="matrix-head">Generator</div>{consumerIds.map((id) => <div className="matrix-head" key={id}>{id.replace('dem_', '')}</div>)}{generatorIds.flatMap((generator) => [<div className="matrix-head" key={`${generator}-name`}>{generator.replace('gen_', '')}</div>, ...consumerIds.map((consumer) => { const value = Number(allocationRows.find((row) => row.generator_site_id === generator && row.consumer_site_id === consumer)?.matched_mwh ?? 0); return <div className="heat" style={{ '--heat': `${Math.min(85, 12 + value * 180)}%` } as React.CSSProperties} key={`${generator}-${consumer}`}>{number(value, 3)}</div>; })])}</div>}
        </article>
        <div className="callout" style={{ marginTop: 18 }}><strong>Commercial matching, not physical routing</strong><p>Allocations are an accounting construct. Electricity continues to flow through the GB network according to physical constraints.</p></div>
      </>}
    </>
  );
}
