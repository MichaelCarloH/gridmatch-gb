'use client';

import { useEffect, useState } from 'react';
import { useApi } from '@/lib/use-api';
import {
  getDataDeliveryMode,
  subscribeDataDeliveryMode,
  type DataDeliveryMode
} from '@/lib/static-fallback';
import type { HealthStatus } from '@/lib/types';

export function ArtifactStatus() {
  const health = useApi<HealthStatus>('/health');
  const [mode, setMode] = useState<DataDeliveryMode>('checking');

  useEffect(() => {
    setMode(getDataDeliveryMode());
    return subscribeDataDeliveryMode(setMode);
  }, []);

  const available = health.data
    ? Object.values(health.data.artifact_availability).filter(Boolean).length
    : null;
  const total = health.data
    ? Object.keys(health.data.artifact_availability).length
    : null;
  const state = health.error
    ? 'unavailable'
    : mode === 'static'
      ? 'static'
      : health.data?.status ?? 'checking';
  const label =
    state === 'static'
      ? 'Static fallback'
      : state === 'healthy'
        ? 'API + artifacts'
        : state === 'degraded'
          ? 'Artifacts degraded'
          : state === 'unavailable'
            ? 'Data unavailable'
            : 'Checking artifacts';
  return (
    <div className={`artifact-status ${state}`} title={health.error ?? undefined}>
      <span className="live-dot" />
      <span>
        <b>{label}</b>
        <small>
          {available == null || total == null
            ? 'Validating delivery mode'
            : `${available}/${total} required bundles available`}
        </small>
      </span>
    </div>
  );
}
