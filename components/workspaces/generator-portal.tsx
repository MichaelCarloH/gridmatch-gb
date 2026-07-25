'use client';

import Link from 'next/link';
import { LineChart } from '@/components/charts/line-chart';
import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { EvidenceTable } from '@/components/ui/evidence-table';
import { MetricCard } from '@/components/ui/metric-card';
import { gbp, number, percent, titleCase } from '@/lib/format';
import { GENERATOR_SITE_ID, mean, sum } from '@/lib/product-analytics';
import { useApi } from '@/lib/use-api';
import type { Dictionary, Envelope, Site } from '@/lib/types';

type GeneratorView =
  | 'overview'
  | 'output'
  | 'offtake'
  | 'revenue'
  | 'assets'
  | 'site';

export function GeneratorPortal({
  view,
  siteId = GENERATOR_SITE_ID
}: {
  view: GeneratorView;
  siteId?: string;
}) {
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const generators = useApi<Envelope<Dictionary[]>>(
    '/api/matching/generators?allocation_type=realised&matching_mode=local_preference'
  );
  const allocations = useApi<Envelope<Dictionary[]>>(
    '/api/matching/allocations?allocation_type=realised&matching_mode=local_preference&settlement_period=1&limit=100'
  );
  const prices = useApi<Envelope<Dictionary[]>>('/api/market/prices?limit=58');
  const site = useApi<Envelope<Site>>(`/api/sites/${siteId}`);
  const forecast = useApi<Envelope<Dictionary[]>>(
    `/api/sites/${siteId}/forecast?model=ml&limit=96`
  );
  const observations = useApi<Envelope<Dictionary[]>>(
    `/api/sites/${siteId}/observations?limit=96`
  );
  const quality = useApi<Envelope<Dictionary>>(`/api/sites/${siteId}/quality`);
  const alerts = useApi<Envelope<Dictionary[]>>(`/api/sites/${siteId}/alerts`);
  const hooks = [sites, generators, allocations, prices, site, forecast, observations, quality, alerts];
  const loading = hooks.some((hook) => hook.loading);
  const error = hooks.find((hook) => hook.error)?.error ?? null;
  const generationSites = (sites.data?.data ?? []).filter((row) => row.site_role === 'generation');
  const selected = generators.data?.data.find((row) => row.generator_site_id === siteId) ?? generators.data?.data[0];
  const forecastRows = forecast.data?.data ?? [];
  const observedRows = observations.data?.data ?? [];
  const generation = sum(observedRows, 'energy_mwh');
  const forecastGeneration = sum(forecastRows, 'point_mwh');
  const capacityMwh = Number(site.data?.data.installed_capacity_mw ?? 0) * observedRows.length * 0.5;
  const referencePrice = mean(prices.data?.data ?? [], 'price');
  const matched = Number(selected?.matched_generation_mwh ?? 0);
  const unmatched = Number(selected?.unused_generation_mwh ?? 0);
  const underperformance = forecastRows.reduce(
    (total, row) => total + Math.max(Number(row.point_mwh ?? 0) - Number(row.actual_mwh ?? 0), 0),
    0
  );
  const linkedAllocations = (allocations.data?.data ?? []).filter((row) => row.generator_site_id === siteId);

  const header = {
    overview: ['Renewable generator', 'Output to offtake, explained.', 'Generation, performance, commercial matching and clearly bounded revenue context.'],
    output: ['Generator output', 'Actual, forecast and weather context.', 'Half-hourly output with uncertainty, capacity and availability evidence.'],
    offtake: ['Commercial offtake', 'See where output was allocated.', 'Matched business demand, unused generation, distance and allocation mode.'],
    revenue: ['Revenue context', 'Scenario value, never an invoice.', 'Reference-price arithmetic for matched, unmatched and underperforming volume.'],
    assets: ['Asset intelligence', 'Exceptions before averages.', 'Outages, zero runs, weather-adjusted underperformance and data incidents.'],
    site: ['Generator site', site.data?.data.name ?? 'Renewable asset', 'Asset-level output, forecast, matching and quality evidence.']
  }[view];

  return (
    <>
      <PageHeader eyebrow={header[0]} title={header[1]} description={header[2]} actions={<span className="badge origin-simulated">Simulated generator data</span>} />
      <DataState loading={loading} error={error} />
      {!loading && !error && (
        <>
          {(view === 'overview' || view === 'site') && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Generation" value={`${number(generation)} MWh`} detail="Latest 96 observed half-hours" tone="green" icon="bolt" explanation={{ source: 'observations.parquet', calculation: 'Sum of observed half-hour energy.' }} />
                <MetricCard label="Forecast generation" value={`${number(forecastGeneration)} MWh`} detail="Saved point forecast" tone="blue" icon="chart" explanation={{ source: 'site_backtest_predictions.parquet', calculation: 'Sum of point forecast over the displayed window.' }} />
                <MetricCard label="Matched business demand" value={`${number(matched)} MWh`} detail="Saved realised allocation window" tone="green" icon="match" explanation={{ source: 'generator_matching_summary.parquet', calculation: 'Sum of output allocated to consumers.' }} />
                <MetricCard label="Offtake coverage" value={percent(selected?.offtake_coverage, 1)} detail="Target comparison · 80%" tone="green" icon="match" explanation={{ source: 'generator_matching_summary.parquet', calculation: 'Matched generation divided by available generation.' }} />
                <MetricCard label="Unmatched generation" value={`${number(unmatched)} MWh`} detail="Available but not allocated" tone="amber" icon="alert" explanation={{ source: 'generator_matching_summary.parquet', calculation: 'Available generation less matched generation.' }} />
                <MetricCard label="Performance vs expectation" value={percent(forecastGeneration ? generation / forecastGeneration - 1 : 0, 1)} detail="Observed versus point forecast" tone="blue" icon="chart" explanation={{ source: 'observations + site forecast', calculation: 'Observed generation divided by forecast generation, less one.', limitation: 'Displayed backtest window.' }} />
                <MetricCard label="Scenario gross revenue" value={gbp(matched * referencePrice)} detail={`${number(referencePrice, 2)} GBP/MWh public reference`} tone="amber" icon="market" explanation={{ source: 'matching summary + public price artifact', calculation: 'Matched MWh multiplied by mean public reference price.', limitation: 'Not an invoice or contract term.' }} />
                <MetricCard label="Alerts" value={String(alerts.data?.data.length ?? 0)} detail={`${number(quality.data?.data.quality_score, 1)} / 100 quality`} icon="alert" explanation={{ source: 'site quality report', calculation: 'Count of artifact-backed site alerts.' }} />
              </section>
              {view === 'overview' && <div className="section-head"><div><h2>Generator workflows</h2><p>Move from output to matching evidence and scenario context.</p></div></div>}
              {view === 'overview' && <section className="grid four">{[
                ['Output and uncertainty', '/generator/output', 'Actual, forecast and q10/q50/q90.'],
                ['Commercial offtake', '/generator/offtake', 'Matched customers and unused generation.'],
                ['Revenue context', '/generator/revenue', 'Scenario-only reference-price arithmetic.'],
                ['Asset intelligence', '/generator/assets', 'Quality and underperformance exceptions.']
              ].map(([label, href, detail]) => <Link className="card feature-card" href={href} key={href}><h3>{label}</h3><p>{detail}</p><span className="site-link">Open evidence →</span></Link>)}</section>}
            </>
          )}

          {(view === 'output' || view === 'site') && (
            <section className="grid two section-gap">
              <article className="card"><div className="card-head"><div><h3>Actual versus forecast</h3><p>MWh per half-hour</p></div></div><LineChart rows={forecastRows} unit="MWh" series={[{ key: 'actual_mwh', label: 'Actual', color: '#0e121a' }, { key: 'point_mwh', label: 'Forecast', color: '#4ca855' }]} /></article>
              <article className="card"><div className="card-head"><div><h3>Forecast range</h3><p>q10, q50 and q90</p></div></div><LineChart rows={forecastRows} unit="MWh" series={[{ key: 'q10_mwh', label: 'q10', color: '#a9bad2' }, { key: 'q50_mwh', label: 'q50', color: '#2f73d9' }, { key: 'q90_mwh', label: 'q90', color: '#6f8eb8' }]} /></article>
              <article className="card"><h3>Capacity and weather</h3><div className="detail-list"><div><span>Installed capacity</span><b>{number(site.data?.data.installed_capacity_mw, 2)} MW</b></div><div><span>Observed capacity factor</span><b>{percent(capacityMwh ? generation / capacityMwh : 0, 1)}</b></div><div><span>Mean wind speed</span><b>{number(mean(observedRows, 'wind_speed_mps'), 1)} m/s</b></div><div><span>Mean irradiance</span><b>{number(mean(observedRows, 'irradiance_wm2'), 0)} W/m²</b></div></div></article>
              <article className="card"><h3>Availability evidence</h3><div className="detail-list"><div><span>Outage / curtailment flags</span><b>{observedRows.filter((row) => row.outage_or_curtailment_flag).length}</b></div><div><span>Zero-run flags</span><b>{String(quality.data?.data.long_zero_run_count ?? 0)}</b></div><div><span>Data readiness</span><b>{titleCase(String(quality.data?.data.site_readiness ?? 'review'))}</b></div></div></article>
            </section>
          )}

          {view === 'offtake' && (
            <>
              <div className="callout"><strong>Allocation boundary</strong><p>Customer links are commercial allocations, not physical electricity routing.</p></div>
              <section className="kpi-grid section-gap">
                <MetricCard label="Matched MWh" value={`${number(matched)} MWh`} detail="Realised local-preference mode" tone="green" icon="match" explanation={{ source: 'generator matching summary', calculation: 'Sum of generator-to-consumer allocations.' }} />
                <MetricCard label="Unmatched output" value={`${number(unmatched)} MWh`} detail="Available output not allocated" tone="amber" icon="alert" explanation={{ source: 'generator matching summary', calculation: 'Available less matched generation.' }} />
                <MetricCard label="Business customers" value={String(selected?.number_of_consumers ?? 0)} detail="Distinct allocated consumers" tone="blue" icon="sites" explanation={{ source: 'generator matching summary', calculation: 'Distinct consumers with non-zero allocations.' }} />
                <MetricCard label="Weighted distance" value={`${number(selected?.weighted_average_distance_km, 0)} km`} detail="Commercial local-preference signal" icon="map" explanation={{ source: 'matching allocations', calculation: 'Matched-MWh-weighted great-circle distance.' }} />
              </section>
              <EvidenceTable caption="Commercial allocation links" headers={['Customer', 'Matched', 'Distance', 'Mode']} rows={linkedAllocations.slice(0, 12).map((row) => [String(row.consumer_name), `${number(row.matched_mwh, 3)} MWh`, `${number(row.distance_km, 0)} km`, titleCase(String(row.matching_mode))])} />
            </>
          )}

          {view === 'revenue' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Reference price" value={`${number(referencePrice, 2)} GBP/MWh`} detail="Mean cached public scenario price" tone="blue" icon="market" origin="public" explanation={{ source: 'public_prices.parquet', calculation: 'Arithmetic mean of displayed public price records.', limitation: 'Non-contemporaneous reference.' }} />
                <MetricCard label="Matched volume" value={`${number(matched)} MWh`} detail="Saved allocation window" tone="green" icon="match" explanation={{ source: 'generator matching summary', calculation: 'Allocated generator output.' }} />
                <MetricCard label="Unmatched volume" value={`${number(unmatched)} MWh`} detail="No allocated business demand" tone="amber" icon="alert" explanation={{ source: 'generator matching summary', calculation: 'Available generation less allocated output.' }} />
                <MetricCard label="Scenario gross revenue" value={gbp(matched * referencePrice)} detail="Matched volume × reference price" tone="green" icon="market" explanation={{ source: 'matching + public price artifacts', calculation: 'Matched MWh multiplied by mean reference price.', limitation: 'Not a real invoice or Volter contract.' }} />
                <MetricCard label="Underperformance value" value={gbp(underperformance * referencePrice)} detail="Scenario lost revenue proxy" tone="amber" icon="alert" explanation={{ source: 'site forecast + public prices', calculation: 'Positive forecast shortfall multiplied by reference price.', limitation: 'Scenario proxy, not a claim.' }} />
              </section>
              <div className="callout warning-callout section-gap"><strong>Scenario disclosure</strong><p>All values are analytical scenarios. They do not represent invoices, payments, certificate value, or Volter contract terms.</p></div>
            </>
          )}

          {view === 'assets' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Outage flags" value={String(observedRows.filter((row) => row.outage_or_curtailment_flag).length)} detail={site.data?.data.name ?? siteId} tone="amber" icon="alert" explanation={{ source: 'site observations', calculation: 'Count of outage or curtailment flags in the displayed window.' }} />
                <MetricCard label="Long zero runs" value={String(quality.data?.data.long_zero_run_count ?? 0)} detail="Physical and availability review" tone="amber" icon="alert" explanation={{ source: 'site quality report', calculation: 'Count of validator-detected long zero runs.' }} />
                <MetricCard label="Weather-adjusted underperformance" value={`${number(underperformance)} MWh`} detail="Positive forecast shortfall" tone="blue" icon="chart" explanation={{ source: 'weather-feature site forecast + actuals', calculation: 'Sum of positive point forecast minus actual generation.' }} />
                <MetricCard label="Scenario lost value" value={gbp(underperformance * referencePrice)} detail="Lost-MWh reference-price proxy" tone="amber" icon="market" explanation={{ source: 'forecast shortfall + public price', calculation: 'Underperformance MWh multiplied by mean public reference price.', limitation: 'Not realised revenue.' }} />
                <MetricCard label="Data incidents" value={String(alerts.data?.data.length ?? 0)} detail={`${number(quality.data?.data.quality_score, 1)} / 100 quality`} tone="amber" icon="alert" explanation={{ source: 'site alerts and quality report', calculation: 'Count of preserved artifact-backed alert records.' }} />
              </section>
              <div className="section-gap">
                <EvidenceTable caption="Generator asset intelligence" headers={['Asset', 'Technology', 'Capacity', 'Quality', 'Offtake', 'Status']} rows={generationSites.map((row) => {
                  const result = generators.data?.data.find((item) => item.generator_site_id === row.site_id);
                  return [
                    <Link className="site-link" href={`/generator/sites/${row.site_id}`} key={row.site_id}>{row.name}</Link>,
                    titleCase(row.technology),
                    `${number(row.installed_capacity_mw, 1)} MW`,
                    `${number(row.quality_score, 1)} / 100`,
                    percent(result?.offtake_coverage, 1),
                    row.quality_score < 98 ? 'Review incident' : 'Ready'
                  ];
                })} />
              </div>
            </>
          )}
        </>
      )}
    </>
  );
}
