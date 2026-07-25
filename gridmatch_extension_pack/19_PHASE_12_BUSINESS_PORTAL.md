# Phase 12 — Business Customer Portal

## Goal

Make the product understandable to a supermarket, warehouse, office or factory.

Use one representative client throughout the guided flow, for example:

```text
Bristol Fresh Market
Archetype: supermarket
Data origin: simulated
```

## Routes

```text
/business
/business/sites
/business/sites/[siteId]
/business/renewables
/business/energy-plan
/business/reports
```

## Overview

Headline:

> Your energy, explained.

KPIs:

- electricity consumed;
- renewable energy matched;
- renewable coverage;
- residual grid electricity;
- scenario energy cost;
- open actions;
- data-quality score.

Every KPI needs a unit, comparison or target, tooltip, source and data-origin label.

## Site experience

Show:

- load profile;
- average and peak load;
- overnight baseload;
- day-ahead forecast;
- P10/P50/P90;
- anomalies;
- data quality;
- archetype comparison.

## Renewable supply

Show wind, solar and residual-grid shares plus generator cards.

Disclosure:

> Matching is a commercial allocation of metered renewable output to demand in the same half-hour. It is not the physical path of electricity.

## Tomorrow's energy plan

Show:

- expected demand;
- expected renewable generation;
- expected residual requirement;
- uncertainty range;
- recommended contracted volume.

Use client language by default. Put quantile and hedge details in `Why this recommendation?`.

## Action centre

Each action contains:

```text
What happened
Why it matters
Suggested action
Evidence
```

Use artifact-backed actions only.

## Acceptance

A non-technical user understands consumption, renewable coverage, residual exposure, cost and action within 30 seconds. All values are traceable. Print reports work. Tests and build pass.

## Execution prompt

```text
Read 19_PHASE_12_BUSINESS_PORTAL.md and PROGRESS.md. Implement only the Business Customer workspace using existing artifacts and API results. Do not change model outputs. Run tests and npm run build, update PROGRESS.md, and stop before Phase 13.
```
