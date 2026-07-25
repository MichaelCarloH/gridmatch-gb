'use client';

import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { Icon } from '@/components/ui/icon';
import { useApi } from '@/lib/use-api';
import { gbp, number, percent } from '@/lib/format';
import type { Dictionary, Envelope, PortfolioMetric, Site } from '@/lib/types';

export default function ReportsPage() {
  const matching = useApi<Envelope<Dictionary>>('/api/matching/summary');
  const consumers = useApi<Envelope<Dictionary[]>>('/api/matching/consumers?allocation_type=realised&matching_mode=local_preference');
  const generators = useApi<Envelope<Dictionary[]>>('/api/matching/generators?allocation_type=realised&matching_mode=local_preference');
  const policies = useApi<Envelope<Dictionary[]>>('/api/market/policy-summary');
  const metrics = useApi<Envelope<PortfolioMetric[]>>('/api/portfolio/metrics?method=reconciled');
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const loading = matching.loading || consumers.loading || policies.loading || metrics.loading;
  const analysis = matching.data?.data.analysis;
  const policy = policies.data?.data.find((row) => row.policy === 'validation_optimised') ?? policies.data?.data[0];
  const netMetric = metrics.data?.data.find((row) => row.target === 'net');
  const averageQuality = (sites.data?.data ?? []).reduce((sum, site) => sum + site.quality_score, 0) / Math.max(sites.data?.data.length ?? 0, 1);
  const reports = [
    ['Procurement position', 'market', `${number(policy?.mean_hedged_volume_mwh, 2)} MWh`, 'Mean scenario hedge per period'],
    ['Renewable match', 'match', percent(analysis?.average_realised_renewable_match_rate, 1), 'Realised local-preference coverage'],
    ['Generator offtake', 'bolt', `${generators.data?.meta?.count ?? 0} assets`, 'Renewable counterparties represented'],
    ['Emissions evidence', 'report', 'Method-ready', 'Carbon factors required for claims'],
    ['Forecast performance', 'chart', `${number(netMetric?.mae, 3)} MWh`, 'Reconciled net-position MAE'],
    ['Asset readiness', 'sites', `${number(averageQuality, 1)} / 100`, 'Mean portfolio data-quality score']
  ];
  return (
    <>
      <PageHeader eyebrow="Operational reporting" title="Evidence that travels." description="Procurement, renewable matching, performance and readiness summaries derived from the same governed artifacts." actions={<button className="button ghost" onClick={() => window.print()}>Print report view</button>} />
      <DataState loading={loading} error={matching.error || consumers.error || policies.error || metrics.error} />
      {!loading && <>
        <section className="grid three">
          {reports.map(([title, icon, value, detail]) => <article className="card report-card" key={title}><span className="metric-icon"><Icon name={icon} /></span><strong>{value}</strong><p>{title}</p><footer><span>{detail}</span><span>Artifact-backed</span></footer></article>)}
        </section>
        <section className="grid two" style={{ marginTop: 18 }}>
          <article className="card"><h3>Portfolio reporting summary</h3><div className="detail-list"><div><span>Scenario policy cost</span><b>{gbp(policy?.total_cost_gbp)}</b></div><div><span>Residual grid requirement</span><b>{number(analysis?.total_realised_residual_grid_requirement_mwh)} MWh</b></div><div><span>Unused generation</span><b>{number(analysis?.total_realised_unused_generation_mwh)} MWh</b></div><div><span>Consumer accounts</span><b>{consumers.data?.meta?.count ?? 0}</b></div></div></article>
          <article className="card dark"><h3>Reporting controls</h3><p>Every KPI on this view is sourced from Phase 4–10 artifacts. Origins, units and methodological boundaries remain visible.</p><div className="rank-list"><div className="rank-row"><i>1</i><span>Public market evidence</span><b>Labelled</b></div><div className="rank-row"><i>2</i><span>Simulated portfolio data</span><b>Labelled</b></div><div className="rank-row"><i>3</i><span>Model performance</span><b>Out-of-sample</b></div></div></article>
        </section>
        <div className="callout warning-callout" style={{ marginTop: 18 }}><strong>Claims boundary</strong><p>No emissions saving, generator revenue or procurement saving is asserted without an explicit tariff, carbon factor and settlement methodology. Scenario costs are not realised financial outcomes.</p></div>
      </>}
    </>
  );
}
