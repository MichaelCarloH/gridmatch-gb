'use client';

import Link from 'next/link';
import { useState } from 'react';
import { PageHeader } from '@/components/layout/page-header';

const steps = [
  ['Onboard and validate a supermarket', '/admin/customers/new', 'Create a non-persistent preview, then validate a half-hour CSV.'],
  ['Explain consumption', '/business/sites/dem_retail_cardiff', 'Show load, peak, baseload, anomalies and quality.'],
  ['Show day-ahead demand', '/business/energy-plan', 'Use the reconciled demand forecast and uncertainty range.'],
  ['Show renewable supply', '/business/renewables', 'Separate wind, solar and residual-grid exposure.'],
  ['Show commercial matching', '/operations/matching', 'Explain same-half-hour allocation and the physical-routing boundary.'],
  ['Show residual requirement', '/operations/portfolio', 'Trace unmet demand period by period.'],
  ['Show recommended contracted volume', '/business/energy-plan', 'Open quantile and scenario-cost reasoning.'],
  ['Show the business report', '/business/reports', 'Print the client-ready evidence view.'],
  ['Switch perspectives', '/generator', 'Move from generator to operator views with the shared shell.'],
  ['Open model methodology', '/models', 'Explain hierarchy, calibration, incidents and limitations.']
] as const;

export function GuidedDemo() {
  const [current, setCurrent] = useState(0);
  const step = steps[current];
  return (
    <>
      <PageHeader eyebrow="Guided demo" title="The complete product in under two minutes." description="A ten-step walkthrough from non-persistent onboarding to client, generator, operator and model evidence." actions={<span className="badge origin-simulated">Public demo · saved artifacts</span>} />
      <section className="guided-demo">
        <aside className="card">
          <strong>{current + 1} / {steps.length}</strong>
          <ol className="demo-step-list">
            {steps.map(([label], index) => (
              <li className={index === current ? 'active' : index < current ? 'complete' : ''} key={label}>
                <button type="button" onClick={() => setCurrent(index)}><span>{index + 1}</span>{label}</button>
              </li>
            ))}
          </ol>
        </aside>
        <article className="card dark demo-stage">
          <span className="eyebrow">Step {current + 1}</span>
          <h2>{step[0]}</h2>
          <p>{step[2]}</p>
          <div className="demo-stage-actions">
            <Link className="button green" href={step[1]}>Open this evidence</Link>
            <button className="button ghost" type="button" disabled={current === 0} onClick={() => setCurrent((value) => Math.max(0, value - 1))}>Previous</button>
            <button className="button ghost" type="button" disabled={current === steps.length - 1} onClick={() => setCurrent((value) => Math.min(steps.length - 1, value + 1))}>Next</button>
          </div>
          <div className="callout section-gap"><strong>Presenter prompt</strong><p>State the data origin, unit, calculation and limitation before moving on. Use “How calculated” on any major KPI for full lineage.</p></div>
        </article>
      </section>
    </>
  );
}
