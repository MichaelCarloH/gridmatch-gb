'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { EvidenceTable } from '@/components/ui/evidence-table';
import { MetricCard } from '@/components/ui/metric-card';
import { apiUpload } from '@/lib/api';
import { number, percent, titleCase } from '@/lib/format';
import { useApi } from '@/lib/use-api';
import { validateMeterCsv } from '@/lib/upload-validation';
import type { Dictionary, Envelope, HealthStatus, Site } from '@/lib/types';

type AdminView = 'overview' | 'customers' | 'customer-new' | 'generators' | 'generator-new' | 'contracts' | 'data' | 'uploads' | 'incidents';

const contracts = [
  { id: 'SIM-C001', customer: 'Taff Retail Park', generator: 'Fenland Solar', dates: '01 Jul–31 Dec 2025', pricing: 'Reference-index scenario', target: '70%', limits: '0–0.8 MWh / period', status: 'Simulated active' },
  { id: 'SIM-C002', customer: 'Trafford Distribution', generator: 'Solway Wind', dates: '01 Jul–31 Dec 2025', pricing: 'Fixed scenario placeholder', target: '65%', limits: '0–1.2 MWh / period', status: 'Simulated review' }
];

export function AdminOperations({ view }: { view: AdminView }) {
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const health = useApi<HealthStatus>('/health');
  const [submitted, setSubmitted] = useState<Dictionary | null>(null);
  const [upload, setUpload] = useState<Dictionary | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);
  const loading = sites.loading || health.loading;
  const error = sites.error || health.error;
  const siteRows = sites.data?.data ?? [];
  const customerRows = siteRows.filter((row) => row.site_role === 'demand');
  const generatorRows = siteRows.filter((row) => row.site_role === 'generation');
  const reviewRows = siteRows.filter((row) => row.quality_score < 98);

  async function validateFile(file: File) {
    setValidating(true);
    setUploadError(null);
    try {
      const result = await apiUpload<Envelope<Dictionary>>('/api/upload/validate', file);
      setUpload({ ...result.data, validation_mode: 'Phase 4 API validator' });
    } catch {
      try {
        const result = validateMeterCsv(await file.text());
        setUpload(result);
      } catch (reason) {
        setUploadError(reason instanceof Error ? reason.message : String(reason));
      }
    } finally {
      setValidating(false);
    }
  }

  const title = {
    overview: ['Data administration', 'Onboard, validate and review.', 'Non-persistent demo workflows for customers, generators, simulated contracts and data operations.'],
    customers: ['Customer administration', 'Business sites and readiness.', 'Demo customers remain simulated and link directly to their governed data evidence.'],
    'customer-new': ['Customer onboarding', 'Preview a business site.', 'Validate the intended customer fields without creating legal, billing or private-data records.'],
    generators: ['Generator administration', 'Renewable assets and readiness.', 'Simulated generators with capacity, technology, quality and origin evidence.'],
    'generator-new': ['Generator onboarding', 'Preview a renewable asset.', 'Capture demo fields without creating a contract, payment record or permanent private-data entry.'],
    contracts: ['Simulated contracts', 'Commercial structure without legal execution.', 'Visible demo-only customer-generator terms, targets, limits and statuses.'],
    data: ['Data operations', 'Freshness, quality and artifacts.', 'Meter readiness, weather and price status, manual review and artifact update evidence.'],
    uploads: ['CSV upload validation', 'Validate before use.', 'Phase 4 schema, half-hour frequency, completeness, duplicates, anomalies, DST review and annotated preview.'],
    incidents: ['Data incidents', 'A manual-review queue with evidence.', 'Quality exceptions are flagged and preserved; observations are never silently removed.']
  }[view];

  return (
    <>
      <PageHeader eyebrow={title[0]} title={title[1]} description={title[2]} actions={<span className="badge origin-simulated">Demo administration</span>} />
      <DataState loading={loading} error={error} />
      {!loading && !error && (
        <>
          {view === 'overview' && (
            <section className="kpi-grid">
              <MetricCard label="Customers" value={String(customerRows.length)} detail="Simulated demand sites" tone="blue" icon="sites" explanation={{ source: 'site registry', calculation: 'Count of demand-role sites.' }} />
              <MetricCard label="Generators" value={String(generatorRows.length)} detail="Simulated renewable sites" tone="green" icon="bolt" explanation={{ source: 'site registry', calculation: 'Count of generation-role sites.' }} />
              <MetricCard label="Simulated contracts" value={String(contracts.length)} detail="No legal execution" tone="amber" icon="report" explanation={{ source: 'documented demo fixtures', calculation: 'Count of visibly simulated contract records.' }} />
              <MetricCard label="Manual review queue" value={String(reviewRows.length)} detail="Sites below 98 / 100" tone="amber" icon="alert" explanation={{ source: 'site quality reports', calculation: 'Quality threshold count.' }} />
              <MetricCard label="Artifact status" value={health.data?.status ?? 'Unavailable'} detail="Read-only health manifest" tone="green" icon="check" explanation={{ source: '/health', calculation: 'Required artifact availability check.' }} />
            </section>
          )}

          {(view === 'customers' || view === 'generators') && (
            <EvidenceTable caption={`${view} readiness`} headers={['Site', 'Type', 'Region', 'Capacity', 'Quality', 'Origin', 'Readiness']} rows={(view === 'customers' ? customerRows : generatorRows).map((row) => [row.name, titleCase(view === 'customers' ? row.business_archetype : row.technology), row.region, `${number(row.installed_capacity_mw, 2)} MW`, `${number(row.quality_score, 1)} / 100`, <span className={`badge origin-${row.data_origin}`} key={row.site_id}>{row.data_origin}</span>, titleCase(row.site_readiness)])} />
          )}

          {(view === 'customer-new' || view === 'generator-new') && (
            <form className="card onboarding-form" onSubmit={(event) => {
              event.preventDefault();
              const data = Object.fromEntries(new FormData(event.currentTarget).entries());
              setSubmitted(data);
            }}>
              <span className="badge origin-simulated">Preview only · not retained</span>
              <div className="form-grid section-gap">
                <label className="field">Legal / site name<input required name="name" /></label>
                <label className="field">{view === 'customer-new' ? 'Archetype' : 'Technology'}<select name="type">{(view === 'customer-new' ? ['office', 'supermarket', 'warehouse', 'factory'] : ['solar', 'wind']).map((value) => <option key={value}>{value}</option>)}</select></label>
                <label className="field">Location<input required name="location" placeholder="Town or GB region" /></label>
                <label className="field">{view === 'customer-new' ? 'Annual consumption (MWh)' : 'Capacity (MW)'}<input required min="0" step=".1" type="number" name="capacity" /></label>
                <label className="field">{view === 'customer-new' ? 'Meter ID placeholder' : 'Meter / export ID placeholder'}<input name="meter_id" placeholder="DEMO-ONLY" /></label>
                {view === 'customer-new' ? <><label className="field">Opening hours<input name="opening_hours" placeholder="08:00–20:00" /></label><label className="field">Renewable target (%)<input min="0" max="100" type="number" name="target" /></label><label className="field">Risk preference<select name="risk"><option>balanced</option><option>conservative</option><option>flexible</option></select></label></> : <><label className="field">Historical output<input name="history" placeholder="Validated CSV reference" /></label><label className="field">Contract dates<input name="dates" placeholder="Demo dates" /></label><label className="field">Price placeholder<input name="price" placeholder="Scenario only" /></label><label className="field">Certificate placeholder<input name="certificate" placeholder="Not verified" /></label></>}
                <label className="field">Data origin<select name="data_origin"><option>simulated</option><option>uploaded</option></select></label>
              </div>
              <button className="button section-gap" type="submit">Validate preview</button>
              {submitted && <div className="callout section-gap"><strong>Preview validated</strong><p>{String(submitted.name)} is ready for demo review. Nothing was stored and no contract, account, invoice or payment workflow was created.</p></div>}
            </form>
          )}

          {view === 'contracts' && (
            <>
              <div className="callout warning-callout"><strong>All contracts are simulated</strong><p>These records demonstrate product structure only. They are not offers, executed agreements, invoices, certificate claims or payment instructions.</p></div>
              <EvidenceTable caption="Simulated contract records" headers={['ID', 'Customer', 'Generator', 'Dates', 'Pricing type', 'Target', 'Limits', 'Status']} rows={contracts.map((row) => [row.id, row.customer, row.generator, row.dates, row.pricing, row.target, row.limits, <span className="badge scenario-badge" key={row.id}>{row.status}</span>])} />
            </>
          )}

          {view === 'data' && (
            <>
              <section className="kpi-grid">
                <MetricCard label="Meter freshness" value="Saved window" detail="No live meter feed connected" tone="amber" icon="chart" explanation={{ source: 'artifact timestamps', calculation: 'Static demo artifact freshness status.' }} />
                <MetricCard label="Weather status" value="Artifact ready" detail="Realised-weather prototype proxy" tone="green" icon="check" explanation={{ source: '/health artifact manifest', calculation: 'Required weather-enriched dataset available.' }} />
                <MetricCard label="Price status" value="Public scenario" detail="Non-contemporaneous reference" tone="blue" icon="market" explanation={{ source: 'public price artifact', calculation: 'Cached public scenario data available.' }} />
                <MetricCard label="Mean quality" value={`${number(siteRows.reduce((v, row) => v + row.quality_score, 0) / Math.max(siteRows.length, 1), 1)} / 100`} detail="Across all demo sites" tone="green" icon="check" explanation={{ source: 'site quality reports', calculation: 'Mean quality score.' }} />
                <MetricCard label="Manual review" value={String(reviewRows.length)} detail="Quality score below 98" tone="amber" icon="alert" explanation={{ source: 'site quality reports', calculation: 'Threshold count.' }} />
                <MetricCard label="Artifact update" value={health.data?.last_artifact_update ? new Date(health.data.last_artifact_update).toLocaleDateString('en-GB') : 'Unavailable'} detail="Health manifest timestamp" icon="report" explanation={{ source: '/health', calculation: 'Most recent required artifact modification timestamp.' }} />
              </section>
            </>
          )}

          {view === 'uploads' && (
            <>
              <article className="card upload-drop">
                <h3>Validate a meter CSV</h3>
                <p>Required columns: <code>timestamp</code>, <code>consumption_kwh</code>. Expected cadence: 30 minutes. Files are validated in memory and not retained.</p>
                <input aria-label="Meter CSV" accept=".csv,text/csv" type="file" onChange={(event) => { const file = event.target.files?.[0]; if (file) void validateFile(file); }} />
                {validating && <p>Validating file…</p>}
                {uploadError && <div className="callout warning-callout"><strong>Validation failed</strong><p>{uploadError}</p></div>}
              </article>
              {upload && <>
                <section className="kpi-grid section-gap">
                  <MetricCard label="Frequency" value={upload.inferred_frequency_minutes == null ? 'Invalid' : `${number(Number(upload.inferred_frequency_minutes), 0)} min`} detail="Expected 30 minutes" tone={upload.inferred_frequency_minutes === 30 ? 'green' : 'amber'} icon="chart" explanation={{ source: String(upload.validation_mode), calculation: 'Median positive interval between ordered timestamps.' }} />
                  <MetricCard label="Completeness" value={percent(Number(upload.completeness), 1)} detail={`${upload.received_rows} received / ${upload.expected_rows} expected`} tone="blue" icon="check" explanation={{ source: String(upload.validation_mode), calculation: 'Distinct valid timestamps divided by expected periods.' }} />
                  <MetricCard label="Duplicates" value={String(upload.duplicates)} detail="Rows remain visible in preview" tone="amber" icon="alert" explanation={{ source: String(upload.validation_mode), calculation: 'Repeated timestamp count.' }} />
                  <MetricCard label="Anomalies" value={String(upload.anomalies)} detail={`DST review: ${upload.dst_issues ?? upload.dst_period_errors ?? 0}`} tone="amber" icon="alert" explanation={{ source: String(upload.validation_mode), calculation: 'Flagged invalid timestamp, value, duplicate and settlement checks.' }} />
                  <MetricCard label="Quality score" value={`${number(Number(upload.quality_score), 1)} / 100`} detail={titleCase(String(upload.readiness ?? upload.site_readiness))} tone="green" icon="check" explanation={{ source: String(upload.validation_mode), calculation: 'Documented completeness, anomaly and frequency score bounded to 0–100.' }} />
                </section>
                <EvidenceTable caption="Annotated CSV preview" headers={['Timestamp', 'Consumption kWh', 'Quality flag']} rows={(upload.annotated_preview as Dictionary[] ?? []).map((row) => [String(row.timestamp ?? row.timestamp_utc), String(row.consumption_kwh ?? row.energy_kwh), String(row.quality_flag)])} />
                <div className="callout section-gap"><strong>Readiness: {titleCase(String(upload.readiness ?? upload.site_readiness))}</strong><p>{String((upload.recommended_actions as string[])?.[0] ?? 'Review validation evidence.')} Permanent storage: disabled.</p></div>
              </>}
            </>
          )}

          {view === 'incidents' && (
            <EvidenceTable caption="Manual data-review queue" headers={['Site', 'Quality', 'Readiness', 'Incident', 'Required action']} rows={reviewRows.map((row) => [row.name, `${number(row.quality_score, 1)} / 100`, titleCase(row.site_readiness), 'Quality threshold breach', 'Inspect flags before operational use'])} />
          )}
        </>
      )}
    </>
  );
}
