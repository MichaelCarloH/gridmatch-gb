'use client';

import { useState } from 'react';
import Link from 'next/link';
import { MetricExplanation } from './metric-explanation';
import { calculationLineage } from '@/lib/product-analytics';

export function HowCalculatedDrawer({
  source,
  calculation,
  limitation
}: {
  source: string;
  calculation: string;
  limitation?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="calculation-drawer">
      <button
        type="button"
        className="calculation-trigger"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        How calculated
      </button>
      {open && (
        <div className="calculation-panel">
          <MetricExplanation
            source={source}
            calculation={calculation}
            limitation={limitation}
          />
          <details>
            <summary>Full calculation lineage</summary>
            <ol className="lineage-list">
              {calculationLineage.map(([step, version, output], index) => (
                <li key={step}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{step}</strong>
                    <small>Version: {version} · Output: {output}</small>
                    <small>Timestamp: saved artifact build · Input: previous governed stage</small>
                  </div>
                </li>
              ))}
            </ol>
            <Link className="site-link micro" href="/research">
              Open methodology evidence →
            </Link>
          </details>
        </div>
      )}
    </div>
  );
}
