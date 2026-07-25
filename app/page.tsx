'use client';

import Link from 'next/link';
import { Icon } from '@/components/ui/icon';
import { useApi } from '@/lib/use-api';
import type { Envelope, Site, Dictionary, ModelRecord } from '@/lib/types';

const features = [
  ['Forecasting', 'chart', '/forecasts', 'Day-ahead demand and renewable output with calibrated uncertainty.'],
  ['Renewable matching', 'match', '/matching', 'Allocate local generation to business demand every settlement period.'],
  ['Hedge intelligence', 'market', '/market', 'Turn probabilistic net-position forecasts into scenario-aware decisions.'],
  ['Asset monitoring', 'sites', '/sites', 'Trace quality, anomalies, model performance and operational readiness.'],
  ['GB asset map', 'map', '/map', 'Explore public and simulated clean-energy assets across Great Britain.'],
  ['Research evidence', 'book', '/research', 'Inspect executed notebooks, model cards, lineage and limitations.']
];

export default function HomePage() {
  const sites = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const matching = useApi<Envelope<Dictionary>>('/api/matching/summary');
  const models = useApi<Envelope<ModelRecord[]>>('/api/models?limit=1');
  const analysis = matching.data?.data.analysis;
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="badge status-active">Artifact-backed prototype</span>
          <h1>Forecast, match and <em>optimise</em> clean power across Great Britain.</h1>
          <p>Operational intelligence for half-hourly demand, renewable generation, commercial matching and portfolio risk—grounded in reproducible evidence.</p>
          <div className="hero-actions">
            <Link className="button green" href="/dashboard">Open live dashboard <Icon name="arrow" /></Link>
            <Link className="button ghost" href="/research">Explore methodology</Link>
          </div>
        </div>
        <div className="hero-stats" aria-label="Live artifact counts">
          <div className="hero-stat"><strong>{sites.data?.meta?.count ?? '—'}</strong><span>modelled sites</span></div>
          <div className="hero-stat"><strong>{models.data?.meta?.count ?? '—'}</strong><span>registered models</span></div>
          <div className="hero-stat"><strong>{analysis ? `${(analysis.average_realised_renewable_match_rate * 100).toFixed(1)}%` : '—'}</strong><span>renewable match</span></div>
        </div>
      </section>
      <div className="section-head"><div><span className="eyebrow">One decision system</span><h2>From raw meter data to action</h2><p>Every number links back to generated data, a saved model or a documented calculation.</p></div></div>
      <section className="grid three">
        {features.map(([title, icon, href, copy]) => (
          <article className="card feature-card" key={href}>
            <span className="metric-icon"><Icon name={icon} /></span>
            <h3>{title}</h3><p>{copy}</p>
            <Link href={href}>Explore capability →</Link>
          </article>
        ))}
      </section>
    </>
  );
}
