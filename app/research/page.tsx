'use client';

import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { OriginBadge, StatusBadge } from '@/components/ui/badges';
import { useApi } from '@/lib/use-api';
import { number, timestamp, titleCase } from '@/lib/format';
import type { Envelope, ModelRecord, Notebook } from '@/lib/types';

export default function ResearchPage() {
  const notebooks = useApi<Envelope<Notebook[]>>('/api/research/notebooks');
  const models = useApi<Envelope<ModelRecord[]>>('/api/models?limit=12');
  const loading = notebooks.loading || models.loading;
  const error = notebooks.error || models.error;
  return (
    <>
      <PageHeader eyebrow="Research evidence" title="Transparent by construction." description="Executed notebooks, model cards, lineage and limitations behind every product surface." actions={<span className="badge status-executed">{notebooks.loading ? <span className="inline-skeleton" aria-label="Loading" /> : notebooks.error ? 'Unavailable' : `${notebooks.data?.meta?.count} notebooks executed`}</span>} />
      <DataState loading={loading} error={error} />
      {!loading && !error && <>
        <section className="grid two">
          {(notebooks.data?.data ?? []).map((notebook, index) => <article className="card" key={notebook.name}>
            <div className="card-head"><div><span className="eyebrow">Notebook {String(index).padStart(2, '0')}</span><h3>{titleCase(notebook.name.replace(/^\d+_/, ''))}</h3></div><StatusBadge status={notebook.status} /></div>
            <p className="muted">{notebook.summary}</p><div className="callout"><strong>Key result</strong><p>{notebook.key_result}</p></div>
            <div className="detail-list"><div><span>Executed</span><b>{timestamp(notebook.execution_timestamp)}</b></div><div><span>Runtime</span><b>{number(notebook.duration_seconds, 2)} s</b></div><div><span>Generated artifacts</span><b>{notebook.artifact_links.length}</b></div></div>
          </article>)}
        </section>
        <div className="section-head"><div><span className="eyebrow">Model lineage</span><h2>Registry evidence</h2><p>A compact view of the 90 logical model records.</p></div><span className="badge status-active">{models.data?.meta?.count} registered</span></div>
        <div className="table-wrap"><table><thead><tr><th>Model</th><th>Scope</th><th>Target</th><th>Algorithm</th><th>MAE</th><th>Coverage</th><th>Status</th></tr></thead><tbody>{models.data?.data.map((model) => <tr key={model.model_id}><td><b>{model.model_id}</b><div className="micro muted">{model.site_id ?? 'portfolio/global'}</div></td><td>{titleCase(model.scope)}</td><td>{titleCase(model.target)}</td><td>{titleCase(model.algorithm)}</td><td>{number(model.mae, 4)}</td><td>{model.coverage == null ? '—' : `${number(model.coverage * 100, 1)}%`}</td><td><StatusBadge status={model.status} /></td></tr>)}</tbody></table></div>
        <section className="grid three" style={{ marginTop: 18 }}>
          <article className="card"><h3>Public data</h3><p className="muted">REPD operational assets and cached Elexon price references.</p><OriginBadge origin="public" /></article>
          <article className="card"><h3>Simulated data</h3><p className="muted">Deterministic portfolio meters, volumes and forecasts, clearly labelled.</p><OriginBadge origin="simulated" /></article>
          <article className="card"><h3>Uploaded data</h3><p className="muted">Validated in memory, never persisted by the demo API.</p><OriginBadge origin="uploaded" /></article>
        </section>
        <div className="callout warning-callout" style={{ marginTop: 18 }}><strong>Limitations</strong><p>This independent prototype does not reproduce a supplier settlement or trading platform. Portfolio data is simulated; price evidence is non-contemporaneous; model training remains offline.</p></div>
      </>}
    </>
  );
}
