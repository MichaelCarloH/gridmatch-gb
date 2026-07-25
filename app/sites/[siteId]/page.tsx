'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { PageHeader } from '@/components/layout/page-header';
import { LineChart } from '@/components/charts/line-chart';
import { DataState } from '@/components/ui/data-state';
import { MetricCard } from '@/components/ui/metric-card';
import { OriginBadge, StatusBadge } from '@/components/ui/badges';
import { useApi } from '@/lib/use-api';
import { number, timestamp, titleCase } from '@/lib/format';
import type { Dictionary, Envelope, Site } from '@/lib/types';

const tabs = ['overview', 'forecast', 'actuals', 'weather', 'anomalies', 'model', 'quality', 'financial / ESG'];

export default function SiteDetailPage() {
  const params = useParams<{ siteId: string }>();
  const id = encodeURIComponent(params.siteId);
  const [tab, setTab] = useState('overview');
  const site = useApi<Envelope<Site>>(`/api/sites/${id}`);
  const forecast = useApi<Envelope<Dictionary[]>>(`/api/sites/${id}/forecast?model=ml&limit=96`);
  const observations = useApi<Envelope<Dictionary[]>>(`/api/sites/${id}/observations?limit=96`);
  const metrics = useApi<Envelope<Dictionary[]>>(`/api/sites/${id}/metrics`);
  const quality = useApi<Envelope<Dictionary>>(`/api/sites/${id}/quality`);
  const alerts = useApi<Envelope<Dictionary[]>>(`/api/sites/${id}/alerts`);
  const modelCard = useApi<Envelope<Dictionary>>(`/api/sites/${id}/model-card`);
  const meta = site.data?.data;
  const forecastRows = forecast.data?.data ?? [];
  const observationRows = observations.data?.data ?? [];
  const mlMetric = metrics.data?.data.find((row) => row.model === 'ml' || row.algorithm === 'ml') ?? metrics.data?.data[0];
  const pointKey = forecastRows[0] && ('point_forecast_mwh' in forecastRows[0] ? 'point_forecast_mwh' : 'forecast_mwh');
  const actualKey = forecastRows[0] && ('actual_mwh' in forecastRows[0] ? 'actual_mwh' : 'actual');
  const totalEnergy = observationRows.reduce((sum, row) => sum + Number(row.energy_mwh ?? 0), 0);
  if (site.loading) return <DataState loading />;
  if (site.error || !meta) return <DataState error={site.error ?? 'Unknown site.'} onRetry={site.reload} />;
  const renderTab = () => {
    if (tab === 'overview') return <div className="grid two">
      <article className="card"><h3>Asset profile</h3><div className="detail-list">
        <div><span>Role</span><b>{titleCase(meta.site_role)}</b></div><div><span>Technology</span><b>{titleCase(meta.technology)}</b></div>
        <div><span>Region</span><b>{meta.region}</b></div><div><span>Capacity</span><b>{number(meta.installed_capacity_mw, 2)} MW</b></div>
        <div><span>Archetype</span><b>{titleCase(meta.business_archetype)}</b></div><div><span>Coordinates</span><b>{number(meta.latitude, 2)}, {number(meta.longitude, 2)}</b></div>
      </div></article>
      <article className="card dark"><h3>Operational brief</h3><div className="rank-list">
        <div className="rank-row"><i>Q</i><span>Data quality</span><b>{number(meta.quality_score, 1)} / 100</b></div>
        <div className="rank-row"><i>M</i><span>Model MAE</span><b>{number(mlMetric?.mae, 3)} MWh</b></div>
        <div className="rank-row"><i>A</i><span>Active alerts</span><b>{alerts.data?.meta?.count ?? '—'}</b></div>
      </div></article>
    </div>;
    if (tab === 'forecast') return <article className="card"><div className="card-head"><div><h3>Out-of-sample forecast</h3><p>Point, actual and q10–q90 evidence · MWh / half-hour</p></div></div>
      <DataState loading={forecast.loading} error={forecast.error} empty={!forecastRows.length} />
      {!!forecastRows.length && <LineChart rows={forecastRows} unit="MWh / half-hour" series={[
        { key: String(actualKey), label: 'Actual', color: '#0e121a' },
        { key: String(pointKey), label: 'ML point', color: meta.site_role === 'generation' ? '#4ca855' : '#2f73d9' },
        { key: 'q10_mwh', label: 'q10', color: '#b8c2cc' },
        { key: 'q90_mwh', label: 'q90', color: '#8593a0' }
      ]} />}</article>;
    if (tab === 'actuals') return <article className="card"><div className="card-head"><div><h3>Meter observations</h3><p>Latest bounded artifact window · UTC source timestamps</p></div><b>{number(totalEnergy, 2)} MWh</b></div>
      <DataState loading={observations.loading} error={observations.error} empty={!observationRows.length} />
      {!!observationRows.length && <LineChart rows={observationRows} unit="MWh / half-hour" series={[{ key: 'energy_mwh', label: 'Observed energy', color: meta.site_role === 'generation' ? '#4ca855' : '#2f73d9' }]} />}</article>;
    if (tab === 'weather') return <div className="grid two"><article className="card"><h3>Weather feature contract</h3><p className="muted">Forecast models use temperature, irradiance, cloud cover and wind-speed features enriched offline. Weather-at-issue limitations remain explicit in the model card.</p><div className="detail-list"><div><span>Storage</span><b>UTC</b></div><div><span>Display</span><b>Europe/London</b></div><div><span>Interval</span><b>30 minutes</b></div></div></article><article className="card"><h3>Latest model issue</h3><p className="muted">{timestamp(forecastRows[0]?.issue_time_utc)}</p><div className="callout"><strong>No live weather download</strong><p>The product reads saved forecast artifacts; external collection remains an offline process.</p></div></article></div>;
    if (tab === 'anomalies') return <article className="card"><h3>Artifact-derived alerts</h3><DataState loading={alerts.loading} error={alerts.error} empty={alerts.data?.data.length === 0} />{alerts.data?.data.map((alert, index) => <div className="callout warning-callout" key={index} style={{ marginTop: 10 }}><strong>{titleCase(String(alert.code ?? alert.type ?? 'quality alert'))}</strong><p>{String(alert.message ?? alert.description ?? 'Review the associated quality evidence.')}</p></div>)}</article>;
    if (tab === 'model') return <div className="grid two"><article className="card"><h3>Performance evidence</h3><div className="detail-list">{metrics.data?.data.slice(0, 8).map((row, index) => <div key={index}><span>{titleCase(String(row.model ?? row.algorithm ?? `model ${index + 1}`))}</span><b>MAE {number(row.mae, 3)} MWh</b></div>)}</div></article><article className="card dark"><h3>Model card</h3><p>{String(modelCard.data?.data.summary ?? modelCard.data?.data.intended_use ?? 'Saved day-ahead estimator with probabilistic intervals.')}</p><div className="callout warning-callout"><strong>Limitations</strong><p>{String(modelCard.data?.data.limitations ?? 'Simulated site data and realised-weather proxy; prototype use only.')}</p></div></article></div>;
    if (tab === 'quality') return <article className="card"><h3>Readiness and quality evidence</h3><div className="detail-list">{Object.entries(quality.data?.data ?? {}).filter(([, value]) => ['string', 'number', 'boolean'].includes(typeof value)).slice(0, 14).map(([key, value]) => <div key={key}><span>{titleCase(key)}</span><b>{String(value)}</b></div>)}</div></article>;
    return <div className="grid three"><MetricCard label="Observed window" value={`${number(totalEnergy, 2)} MWh`} detail="Bounded meter sample" tone={meta.site_role === 'generation' ? 'green' : 'blue'} icon="bolt" /><MetricCard label="Forecast MAE" value={`${number(mlMetric?.mae, 3)} MWh`} detail="Out-of-sample model evidence" icon="chart" /><MetricCard label="Data quality" value={`${number(meta.quality_score, 1)} / 100`} detail="Row-preserving validation score" tone="green" icon="check" /><div className="callout" style={{ gridColumn: '1 / -1' }}><strong>Reporting boundary</strong><p>Energy and forecast metrics are artifact-derived. Financial and emissions claims require tariff and carbon-factor assumptions and are not presented as realised outcomes.</p></div></div>;
  };
  return (
    <>
      <PageHeader eyebrow={`${meta.region} · ${meta.site_id}`} title={meta.name} description={`${titleCase(meta.business_archetype)} · ${number(meta.installed_capacity_mw, 2)} MW ${titleCase(meta.technology)}`} actions={<><OriginBadge origin={meta.data_origin} /><StatusBadge status={meta.site_readiness} /></>} />
      <div className="tabs" role="tablist">{tabs.map((item) => <button role="tab" aria-selected={tab === item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)} key={item}>{titleCase(item)}</button>)}</div>
      {renderTab()}
    </>
  );
}
