'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { PageHeader } from '@/components/layout/page-header';
import { GBMap } from '@/components/map/gb-map';
import { DataState } from '@/components/ui/data-state';
import { OriginBadge } from '@/components/ui/badges';
import { useApi } from '@/lib/use-api';
import { number, titleCase } from '@/lib/format';
import type { Dictionary, Envelope, GeoCollection, GeoFeature } from '@/lib/types';

export default function MapPage() {
  const resource = useApi<GeoCollection>('/api/map/sites.geojson');
  const arcs = useApi<Envelope<Dictionary[]>>('/api/map/matching-arcs?settlement_period=1&allocation_type=realised&matching_mode=local_preference&minimum_matched_mwh=0.01&limit=200');
  const [publicFeatures, setPublicFeatures] = useState<GeoFeature[]>([]);
  const [role, setRole] = useState('all');
  const [technology, setTechnology] = useState('all');
  const [region, setRegion] = useState('all');
  const [origin, setOrigin] = useState('all');
  const [minCapacity, setMinCapacity] = useState(0);
  const [alertsOnly, setAlertsOnly] = useState(false);
  const [modelled, setModelled] = useState('all');
  const [selected, setSelected] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/demo-data/repd_operational_sites.geojson', { signal: controller.signal })
      .then((response) => response.json())
      .then((collection) => setPublicFeatures(collection.features.map((feature: Dictionary, index: number) => ({
        type: 'Feature',
        geometry: feature.geometry,
        properties: {
          site_id: `repd-${index}`,
          name: feature.properties.project_name,
          site_role: 'generation',
          technology: feature.properties.technology,
          business_archetype: 'operational_public_asset',
          latitude: feature.geometry.coordinates[1],
          longitude: feature.geometry.coordinates[0],
          installed_capacity_mw: feature.properties.installed_capacity_mw,
          region: feature.properties.region,
          data_origin: 'public',
          quality_score: 100,
          site_readiness: 'operational',
          modelled: false
        }
      }))))
      .catch(() => setPublicFeatures([]));
    return () => controller.abort();
  }, []);
  const all = useMemo(() => [...(resource.data?.features ?? []), ...publicFeatures], [resource.data, publicFeatures]);
  const regions = [...new Set(all.map((f) => f.properties.region))].sort();
  const technologies = [...new Set(all.map((f) => f.properties.technology))].sort();
  const features = useMemo(() => all.filter((feature) => {
    const site = feature.properties;
    return (role === 'all' || site.site_role === role) &&
      (technology === 'all' || site.technology === technology) &&
      (region === 'all' || site.region === region) &&
      (origin === 'all' || site.data_origin === origin) &&
      site.installed_capacity_mw >= minCapacity &&
      (modelled === 'all' || site.modelled === (modelled === 'yes')) &&
      (!alertsOnly || site.quality_score < 98);
  }), [all, role, technology, region, origin, minCapacity, modelled, alertsOnly]);
  const selectedFeature =
    features.find((feature) => feature.properties.site_id === selected) ??
    features[0];
  const site = selectedFeature?.properties;
  return (
    <>
      <PageHeader eyebrow="Great Britain asset view" title="Generation meets demand." description="Modelled business and renewable sites, with public REPD evidence available as the wider research layer." actions={<span className="badge status-active">{features.length} visible sites</span>} />
      <div className="filter-row">
        <label className="field">Technology<select value={technology} onChange={(e) => setTechnology(e.target.value)}><option value="all">All technologies</option>{technologies.map((v) => <option key={v}>{v}</option>)}</select></label>
        <label className="field">Role<select value={role} onChange={(e) => setRole(e.target.value)}><option value="all">All roles</option><option value="demand">Demand</option><option value="generation">Generation</option></select></label>
        <label className="field">Region<select value={region} onChange={(e) => setRegion(e.target.value)}><option value="all">All regions</option>{regions.map((v) => <option key={v}>{v}</option>)}</select></label>
        <label className="field">Origin<select value={origin} onChange={(e) => setOrigin(e.target.value)}><option value="all">All origins</option><option value="simulated">Simulated</option><option value="public">Public</option></select></label>
        <label className="field">Min capacity<input type="number" min="0" step=".5" value={minCapacity} onChange={(e) => setMinCapacity(Number(e.target.value))} /></label>
        <label className="field">Modelled<select value={modelled} onChange={(e) => setModelled(e.target.value)}><option value="all">All assets</option><option value="yes">Modelled portfolio</option><option value="no">Public research layer</option></select></label>
        <label className="field">Alert state<select value={alertsOnly ? 'alerts' : 'all'} onChange={(e) => setAlertsOnly(e.target.value === 'alerts')}><option value="all">All states</option><option value="alerts">Needs attention</option></select></label>
      </div>
      <DataState loading={resource.loading} error={resource.error} empty={!resource.loading && !features.length} onRetry={resource.reload} />
      {!!features.length && <section className="split">
        <GBMap features={features} arcs={arcs.data?.data ?? []} selected={site?.site_id} onSelect={setSelected} />
        {site && <aside className="card site-inspector">
          <div className="card-head"><div><span className="eyebrow">Selected asset</span><h2>{site.name}</h2></div><OriginBadge origin={site.data_origin} /></div>
          <p className="muted">{titleCase(site.business_archetype)} in {site.region}.</p>
          <div className="detail-list">
            <div><span>Role</span><b>{titleCase(site.site_role)}</b></div>
            <div><span>Technology</span><b>{titleCase(site.technology)}</b></div>
            <div><span>Capacity</span><b>{number(site.installed_capacity_mw, 2)} MW</b></div>
            <div><span>Quality score</span><b>{number(site.quality_score, 1)} / 100</b></div>
            <div><span>Coordinates</span><b>{number(selectedFeature.geometry.coordinates[1], 2)}, {number(selectedFeature.geometry.coordinates[0], 2)}</b></div>
          </div>
          {site.modelled ? <Link className="button green" style={{ width: '100%', marginTop: 18 }} href={`/sites/${site.site_id}`}>Open site intelligence</Link> : <div className="callout" style={{ marginTop: 18 }}><strong>Public research asset</strong><p>Available as geographic and capacity evidence; no simulated site model is attached.</p></div>}
        </aside>}
      </section>}
      <div className="callout" style={{ marginTop: 18 }}><strong>Map interpretation</strong><p>{publicFeatures.length.toLocaleString('en-GB')} operational public REPD projects and 12 modelled portfolio sites. Green lines are commercial allocations, not physical grid flows. Coastline: Natural Earth public-domain geometry.</p></div>
    </>
  );
}
