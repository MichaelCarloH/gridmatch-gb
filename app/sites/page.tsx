'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { PageHeader } from '@/components/layout/page-header';
import { DataState } from '@/components/ui/data-state';
import { OriginBadge, StatusBadge } from '@/components/ui/badges';
import { useApi } from '@/lib/use-api';
import { number, titleCase } from '@/lib/format';
import type { Envelope, Site } from '@/lib/types';

export default function SitesPage() {
  const resource = useApi<Envelope<Site[]>>('/api/sites?limit=100');
  const [query, setQuery] = useState('');
  const [role, setRole] = useState('all');
  const [origin, setOrigin] = useState('all');
  const sites = useMemo(() => (resource.data?.data ?? []).filter((site) =>
    (role === 'all' || site.site_role === role) &&
    (origin === 'all' || site.data_origin === origin) &&
    `${site.name} ${site.region} ${site.technology}`.toLowerCase().includes(query.toLowerCase())
  ), [resource.data, query, role, origin]);
  return (
    <>
      <PageHeader eyebrow="Asset intelligence" title="Sites" description="Operational metadata, readiness, quality and modelling status for the demonstration portfolio." actions={<span className="badge status-active">{resource.data?.meta?.count ?? '—'} registered</span>} />
      <div className="filter-row">
        <label className="field">Search<input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Name, region or technology" /></label>
        <label className="field">Role<select value={role} onChange={(e) => setRole(e.target.value)}><option value="all">All roles</option><option value="demand">Demand</option><option value="generation">Generation</option></select></label>
        <label className="field">Data origin<select value={origin} onChange={(e) => setOrigin(e.target.value)}><option value="all">All origins</option><option value="simulated">Simulated</option><option value="public">Public</option></select></label>
      </div>
      <DataState loading={resource.loading} error={resource.error} empty={!resource.loading && !sites.length} onRetry={resource.reload} />
      {!!sites.length && <div className="table-wrap"><table>
        <thead><tr><th>Site</th><th>Role / technology</th><th>Location</th><th>Capacity</th><th>Quality</th><th>Origin</th><th>Status</th></tr></thead>
        <tbody>{sites.map((site) => <tr key={site.site_id}>
          <td><Link className="site-link" href={`/sites/${site.site_id}`}>{site.name}</Link><div className="micro muted">{site.business_archetype.replaceAll('_', ' ')}</div></td>
          <td>{titleCase(site.site_role)}<div className="micro muted">{titleCase(site.technology)}</div></td>
          <td>{site.region}</td><td>{number(site.installed_capacity_mw, 2)} MW</td>
          <td><div className="quality-cell"><div className="quality-track"><i style={{ width: `${site.quality_score}%` }} /></div>{number(site.quality_score, 1)}</div></td>
          <td><OriginBadge origin={site.data_origin} /></td><td><StatusBadge status={site.site_readiness} /></td>
        </tr>)}</tbody>
      </table></div>}
    </>
  );
}
