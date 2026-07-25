# Phase 13 — Renewable Generator Portal

## Goal

Explain generation, matched offtake, unmatched output, performance and revenue context.

## Routes

```text
/generator
/generator/output
/generator/offtake
/generator/revenue
/generator/assets
/generator/sites/[siteId]
```

## Overview KPIs

- generation;
- forecast generation;
- matched business demand;
- offtake coverage;
- unmatched generation;
- performance versus expectation;
- scenario revenue;
- alerts.

## Output

Show actual, forecast, q10/q50/q90, capacity factor, weather and availability.

## Offtake

Show matched business customers, matched MWh, unmatched output, distance and matching mode.

Disclosure:

> Customer links are commercial allocations, not physical electricity routing.

## Revenue

Use scenario values only:

- reference price;
- matched volume;
- unmatched volume;
- scenario gross revenue;
- scenario lost revenue from underperformance.

Do not imply real invoices or Volter contract terms.

## Asset intelligence

Show outages, zero runs, weather-adjusted underperformance, lost MWh and data incidents.

## Acceptance

Generator understands output, offtake, performance and scenario revenue. No fabricated contract/payment claims. Tests and build pass.

## Execution prompt

```text
Read 20_PHASE_13_GENERATOR_PORTAL.md and PROGRESS.md. Implement only the Generator workspace using existing forecasts, matching and quality artifacts. Preserve all quantitative outputs. Run tests and npm run build, update PROGRESS.md, and stop before Phase 14.
```
