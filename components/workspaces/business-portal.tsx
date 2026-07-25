'use client';

import Link from 'next/link';
import { LineChart } from '@/components/charts/line-chart';
import { PageHeader } from '@/components/layout/page-header';
import { ActionCard } from '@/components/ui/action-card';
import { DataState } from '@/components/ui/data-state';
import { EvidenceTable } from '@/components/ui/evidence-table';
import { MetricCard } from '@/components/ui/metric-card';
import { useApi } from '@/lib/use-api';
import { BUSINESS_SITE_ID, portfolioTotals, sum } from '@/lib/product-analytics';
import { gbp, number, percent, titleCase } from '@/lib/format';
import type {
  Dictionary,
  Envelope,
  PortfolioPoint,
  Site
} from '@/lib/types';

type BusinessView =
  | 'overview'
  | 'sites'
  | 'site'
  | 'renewables'
  | 'energy-plan'
  | 'reports';

export function BusinessPortal({
  view,
  siteId = BUSINESS_SITE_ID
}: {
  view: BusinessView;
  siteId?: string;
}) {
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const forecast = useApi<Envelope<PortfolioPoint[]>>(
    '/api/portfolio/forecast?method=reconciled&limit=48'
  );
  const matching = useApi<Envelope<Dictionary>>('/api/matching/summary');
  const consumers = useApi<Envelope<Dictionary[]>>(
    '/api/matching/consumers?allocation_type=realised&matching_mode=local_preference'
  );
  const generators = useApi<Envelope<Dictionary[]>>(
    '/api/matching/generators?allocation_type=realised&matching_mode=local_preference'
  );
  const hedge = useApi<Envelope<Dictionary[]>>(
    '/api/market/hedge-recommendations?limit=48'
  );
  const policies = useApi<Envelope<Dictionary[]>>('/api/market/policy-summary');
  const site = useApi<Envelope<Site>>(
    view === 'site' ? `/api/sites/${siteId}` : null
  );
  const siteForecast = useApi<Envelope<Dictionary[]>>(
    view === 'site' ? `/api/sites/${siteId}/forecast?model=ml&limit=96` : null
  );
  const observations = useApi<Envelope<Dictionary[]>>(
    view === 'site' ? `/api/sites/${siteId}/observations?limit=96` : null
  );
  const quality = useApi<Envelope<Dictionary>>(
    view === 'site' ? `/api/sites/${siteId}/quality` : null
  );
  const alerts = useApi<Envelope<Dictionary[]>>(
    view === 'site' ? `/api/sites/${siteId}/alerts` : null
  );
  const hooks = [
    sites,
    forecast,
    matching,
    consumers,
    generators,
    hedge,
    policies,
    site,
    siteForecast,
    observations,
    quality,
    alerts
  ];
  const loading = hooks.some((hook) => hook.loading);
  const error = hooks.find((hook) => hook.error)?.error ?? null;
  const demandSites = (sites.data?.data ?? []).filter(
    (row) => row.site_role === 'demand'
  );
  const generationSites = (sites.data?.data ?? []).filter(
    (row) => row.site_role === 'generation'
  );
  const rows = forecast.data?.data ?? [];
  const totals = portfolioTotals(rows);
  const analysis = matching.data?.data.analysis;
  const policy =
    policies.data?.data.find((row) => row.policy === 'validation_optimised') ??
    policies.data?.data[0];
  const hedgeRows = hedge.data?.data ?? [];
  const recommended = sum(hedgeRows, 'recommended_mwh');
  const selectedConsumer =
    consumers.data?.data.find((row) => row.consumer_site_id === siteId) ??
    consumers.data?.data[0];
  const openActions = demandSites.filter((row) => row.quality_score < 98).length;
  const generatorSummaries = generators.data?.data ?? [];
  const windAvailable = generatorSummaries
    .filter((row) => generationSites.find((siteRow) => siteRow.site_id === row.generator_site_id)?.technology === 'wind')
    .reduce((value, row) => value + Number(row.available_generation_mwh ?? 0), 0);
  const solarAvailable = generatorSummaries
    .filter((row) => generationSites.find((siteRow) => siteRow.site_id === row.generator_site_id)?.technology === 'solar')
    .reduce((value, row) => value + Number(row.available_generation_mwh ?? 0), 0);
  const totalAvailable = windAvailable + solarAvailable;

  const header = {
    overview: ['Business customer', 'Your energy, explained.', 'Consumption, renewable coverage, residual exposure and next actions for the demo portfolio.'],
    sites: ['Business sites', 'Every load, in context.', 'Traceable demand, archetype and data-readiness evidence for each simulated business site.'],
    site: ['Site intelligence', site.data?.data.name ?? 'Business site', 'Half-hourly demand, probabilistic forecast, anomalies and data quality.'],
    renewables: ['Renewable supply', 'Commercial matching, made clear.', 'See the renewable generators allocated to business demand in the same half-hour.'],
    'energy-plan': ['Tomorrow’s energy plan', 'A practical day-ahead recommendation.', 'Expected demand, renewable supply, residual need and a bounded scenario recommendation.'],
    reports: ['Business report', 'A client-ready evidence pack.', 'A printable summary of consumption, renewable coverage, residual exposure and scenario cost.']
  }[view];

  return (
    <>
      <PageHeader
        eyebrow={header[0]}
        title={header[1]}
        description={header[2]}
        actions={
          view === 'reports' ? (
            <button className="button ghost" onClick={() => window.print()}>
              Print business report
            </button>
          ) : (
            <span className="badge origin-simulated">Simulated portfolio</span>
          )
        }
      />
      <DataState loading={loading} error={error} />
      {!loading && !error && (
        <>
          {view === 'overview' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Electricity consumed" value={`${number(totals.demand)} MWh`} detail="Next 48 half-hours · reconciled forecast" tone="blue" icon="chart" explanation={{ source: 'portfolio_forecasts.parquet', calculation: 'Sum of 48 half-hour demand point forecasts.', limitation: 'Simulated demand, not a bill.' }} />
                <MetricCard label="Renewable matched" value={`${number(totals.demand * Number(analysis?.average_forecast_renewable_match_rate ?? 0))} MWh`} detail="Commercial allocation estimate" tone="green" icon="match" explanation={{ source: 'matching_summary.json', calculation: 'Forecast demand multiplied by forecast match rate.', limitation: 'Commercial allocation, not physical routing.' }} />
                <MetricCard label="Renewable coverage" value={percent(analysis?.average_forecast_renewable_match_rate, 1)} detail="Target comparison · 70%" tone="green" icon="bolt" explanation={{ source: 'matching_summary.json', calculation: 'Matched renewable MWh divided by demand MWh.', limitation: 'Portfolio average over the saved evaluation window.' }} />
                <MetricCard label="Residual grid electricity" value={`${number(totals.demand * (1 - Number(analysis?.average_forecast_renewable_match_rate ?? 0)))} MWh`} detail="Expected unmatched demand" icon="grid" explanation={{ source: 'portfolio forecast + matching summary', calculation: 'Forecast demand less estimated matched renewable demand.' }} />
                <MetricCard label="Scenario energy cost" value={gbp(policy?.total_cost_gbp)} detail="Saved validation window · not an invoice" tone="amber" icon="market" explanation={{ source: 'hedge_policy_metrics.parquet', calculation: 'Scenario day-ahead and imbalance costs across the validation window.', limitation: 'Non-contemporaneous public reference prices.' }} />
                <MetricCard label="Open actions" value={String(openActions)} detail="Sites below 98 quality" tone="amber" icon="alert" explanation={{ source: 'site_quality_reports', calculation: 'Count of demand sites with quality score below 98.' }} />
                <MetricCard label="Data-quality score" value={`${number(demandSites.reduce((v, row) => v + row.quality_score, 0) / Math.max(demandSites.length, 1), 1)} / 100`} detail="Mean business-site score" tone="blue" icon="check" explanation={{ source: 'site_quality_reports', calculation: 'Mean documented 0–100 site quality score.' }} />
              </section>
              <div className="section-head"><div><h2>Action centre</h2><p>Only exceptions backed by saved quality, forecast and matching artifacts.</p></div></div>
              <section className="grid three">
                <ActionCard title="Review residual exposure" description={`What happened: forecast coverage is ${percent(analysis?.average_forecast_renewable_match_rate)}. Why it matters: unmatched demand remains price-exposed. Suggested action: review the energy plan. Evidence: matching summary.`} href="/business/energy-plan" icon="market" origin="simulated" />
                <ActionCard title="Inspect data readiness" description={`What happened: ${openActions} demand sites score below 98. Why it matters: weak inputs can degrade forecasts. Suggested action: review flagged observations. Evidence: site quality reports.`} href="/business/sites" icon="alert" origin="simulated" />
                <ActionCard title="Share the evidence" description="What happened: the reporting artifacts are ready. Why it matters: decisions need traceability. Suggested action: print the client view. Evidence: forecast, matching, quality and policy artifacts." href="/business/reports" icon="report" origin="simulated" />
              </section>
            </>
          )}

          {view === 'sites' && (
            <EvidenceTable
              caption="Business site readiness"
              headers={['Site', 'Archetype', 'Region', 'Capacity', 'Quality', 'Origin']}
              rows={demandSites.map((row) => [
                <Link className="site-link" href={`/business/sites/${row.site_id}`} key={row.site_id}>{row.name}</Link>,
                titleCase(row.business_archetype),
                row.region,
                `${number(row.installed_capacity_mw, 2)} MW`,
                `${number(row.quality_score, 1)} / 100`,
                <span className={`badge origin-${row.data_origin}`} key={row.data_origin}>{row.data_origin}</span>
              ])}
            />
          )}

          {view === 'site' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Average load" value={`${number(observations.data?.data.length ? sum(observations.data.data, 'energy_mwh') / observations.data.data.length * 2 : 0, 2)} MW`} detail="Latest 96 half-hours" tone="blue" icon="chart" explanation={{ source: 'observations.parquet', calculation: 'Mean half-hour energy multiplied by two.' }} />
                <MetricCard label="Peak load" value={`${number(Math.max(...(observations.data?.data ?? []).map((row) => Number(row.energy_mwh ?? 0) * 2)), 2)} MW`} detail="Observed maximum" icon="bolt" explanation={{ source: 'observations.parquet', calculation: 'Maximum half-hour energy multiplied by two.' }} />
                <MetricCard label="Overnight baseload" value={`${number((observations.data?.data ?? []).slice(0, 12).reduce((v, row) => v + Number(row.energy_mwh ?? 0), 0) / 6, 2)} MW`} detail="First six hours in preview" tone="amber" icon="grid" explanation={{ source: 'observations.parquet', calculation: 'Mean of first 12 half-hours converted to MW.', limitation: 'Preview-window proxy.' }} />
                <MetricCard label="Data quality" value={`${number(quality.data?.data.quality_score, 1)} / 100`} detail={String(quality.data?.data.site_readiness ?? 'Review')} tone="green" icon="check" explanation={{ source: 'site_quality_reports', calculation: 'Completeness and anomaly penalties under quality-v1.' }} />
              </section>
              <section className="grid two section-gap">
                <article className="card">
                  <div className="card-head"><div><h3>Load profile</h3><p>Observed and day-ahead forecast · MWh / half-hour</p></div></div>
                  <LineChart rows={siteForecast.data?.data ?? []} unit="MWh" series={[{ key: 'actual_mwh', label: 'Actual', color: '#0e121a' }, { key: 'point_mwh', label: 'Forecast', color: '#2f73d9' }]} />
                </article>
                <article className="card">
                  <div className="card-head"><div><h3>Forecast uncertainty</h3><p>P10 / P50 / P90 · client view</p></div></div>
                  <LineChart rows={siteForecast.data?.data ?? []} unit="MWh" series={[{ key: 'q10_mwh', label: 'P10', color: '#a9bad2' }, { key: 'q50_mwh', label: 'P50', color: '#2f73d9' }, { key: 'q90_mwh', label: 'P90', color: '#6f8eb8' }]} />
                </article>
              </section>
              <section className="grid two section-gap">
                <article className="card"><h3>Anomalies</h3><div className="detail-list">{(alerts.data?.data ?? []).map((row) => <div key={String(row.code)}><span>{String(row.message)}</span><b>{String(row.count)}</b></div>)}</div></article>
                <article className="card"><h3>Archetype comparison</h3><p className="muted">Compare this {titleCase(site.data?.data.business_archetype ?? '')} with the demo demand portfolio.</p><div className="detail-list"><div><span>Site capacity</span><b>{number(site.data?.data.installed_capacity_mw, 2)} MW</b></div><div><span>Archetype peer sites</span><b>{demandSites.filter((row) => row.business_archetype === site.data?.data.business_archetype).length}</b></div><div><span>Portfolio mean quality</span><b>{number(demandSites.reduce((v, row) => v + row.quality_score, 0) / Math.max(demandSites.length, 1), 1)}</b></div></div></article>
              </section>
            </>
          )}

          {view === 'renewables' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Wind share" value={percent(totalAvailable ? windAvailable / totalAvailable : 0, 1)} detail={`${number(windAvailable)} MWh available`} tone="green" icon="bolt" explanation={{ source: 'generator matching summaries + site registry', calculation: 'Wind available MWh divided by total available renewable MWh.' }} />
                <MetricCard label="Solar share" value={percent(totalAvailable ? solarAvailable / totalAvailable : 0, 1)} detail={`${number(solarAvailable)} MWh available`} tone="green" icon="bolt" explanation={{ source: 'generator matching summaries + site registry', calculation: 'Solar available MWh divided by total available renewable MWh.' }} />
                <MetricCard label="Residual grid share" value={percent(1 - Number(analysis?.average_realised_renewable_match_rate ?? 0), 1)} detail="Saved realised window" tone="blue" icon="grid" explanation={{ source: 'matching summary', calculation: 'One minus realised renewable match rate.' }} />
                <MetricCard label="Representative coverage" value={percent(selectedConsumer?.renewable_coverage, 1)} detail={String(selectedConsumer?.consumer_site_id ?? BUSINESS_SITE_ID)} tone="green" icon="match" explanation={{ source: 'consumer matching summary', calculation: 'Matched renewable MWh divided by consumer demand MWh.' }} />
              </section>
              <div className="callout section-gap"><strong>Commercial allocation disclosure</strong><p>Matching is a commercial allocation of metered renewable output to demand in the same half-hour. It is not the physical path of electricity.</p></div>
              <section className="grid four section-gap">
                {generationSites.map((generator) => {
                  const result = generators.data?.data.find((row) => row.generator_site_id === generator.site_id);
                  return <article className="card" key={generator.site_id}><span className="badge origin-simulated">simulated</span><h3>{generator.name}</h3><p>{titleCase(generator.technology)} · {generator.region}</p><div className="detail-list"><div><span>Matched output</span><b>{number(result?.matched_generation_mwh)} MWh</b></div><div><span>Offtake coverage</span><b>{percent(result?.offtake_coverage, 1)}</b></div></div></article>;
                })}
              </section>
            </>
          )}

          {view === 'energy-plan' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Expected demand" value={`${number(totals.demand)} MWh`} detail="Tomorrow · P50 point view" tone="blue" icon="chart" explanation={{ source: 'portfolio_forecasts.parquet', calculation: 'Sum of first 48 reconciled demand forecasts.' }} />
                <MetricCard label="Expected renewable generation" value={`${number(totals.generation)} MWh`} detail="Tomorrow · wind and solar" tone="green" icon="bolt" explanation={{ source: 'portfolio_forecasts.parquet', calculation: 'Sum of first 48 reconciled generation forecasts.' }} />
                <MetricCard label="Expected residual" value={`${number(totals.residual)} MWh`} detail="Positive net requirement" icon="grid" explanation={{ source: 'portfolio_forecasts.parquet', calculation: 'Sum of positive half-hour net demand.' }} />
                <MetricCard label="Recommended contracted volume" value={`${number(recommended)} MWh`} detail="Saved validation-optimised scenario" tone="amber" icon="market" explanation={{ source: 'hedge_recommendations.parquet', calculation: 'Sum of saved half-hour recommendations.', limitation: 'Decision support only; no trade execution.' }} />
              </section>
              <section className="grid two section-gap">
                <article className="card"><h3>Tomorrow’s position</h3><LineChart rows={rows} unit="MWh / half-hour" series={[{ key: 'demand_point_mwh', label: 'Demand', color: '#2f73d9' }, { key: 'generation_point_mwh', label: 'Renewables', color: '#4ca855' }, { key: 'net_point_mwh', label: 'Residual', color: '#0e121a' }]} /></article>
                <article className="card dark"><h3>Why this recommendation?</h3><p>The saved policy selects a contracted volume from the forecast distribution using asymmetric short and long scenario costs.</p><div className="detail-list"><div><span>Demand uncertainty</span><b>{number(totals.demandLow)}–{number(totals.demandHigh)} MWh</b></div><div><span>Selected policy</span><b>{titleCase(String(policy?.policy ?? 'validation_optimised'))}</b></div><div><span>Execution</span><b>Licensed supplier / partner</b></div></div><p className="micro">Quantiles describe forecast uncertainty. They are not confidence guarantees, prices, or executed trades.</p></article>
              </section>
            </>
          )}

          {view === 'reports' && (
            <section className="print-report card">
              <span className="badge origin-simulated">Simulated business report</span>
              <h2>Taff Retail Park · energy summary</h2>
              <p>Generated from saved GridMatch GB demo artifacts. Scenario pricing is not an invoice or realised saving.</p>
              <div className="detail-list">
                <div><span>Forecast demand · next 48 periods</span><b>{number(totals.demand)} MWh</b></div>
                <div><span>Portfolio renewable coverage</span><b>{percent(analysis?.average_forecast_renewable_match_rate, 1)}</b></div>
                <div><span>Residual requirement estimate</span><b>{number(totals.residual)} MWh</b></div>
                <div><span>Recommended contracted volume</span><b>{number(recommended)} MWh</b></div>
                <div><span>Scenario validation cost</span><b>{gbp(policy?.total_cost_gbp)}</b></div>
                <div><span>Data origin</span><b>Simulated portfolio · public price reference</b></div>
              </div>
              <div className="callout warning-callout section-gap"><strong>Method boundary</strong><p>Renewable matching is commercial allocation, not physical routing. Pricing is a non-contemporaneous scenario. Procurement remains with a licensed supplier or utility partner.</p></div>
            </section>
          )}
        </>
      )}
    </>
  );
}
