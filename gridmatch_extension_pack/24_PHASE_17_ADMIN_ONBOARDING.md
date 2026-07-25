# Phase 17 — Onboarding, Contracts and Data Operations

## Goal

Demonstrate how customers, generators, meter data and simulated contracts enter the system.

## Routes

```text
/admin
/admin/customers
/admin/customers/new
/admin/generators
/admin/generators/new
/admin/contracts
/admin/data
/admin/data/uploads
/admin/data/incidents
```

## Customer onboarding

Fields include:

- legal/site name;
- archetype;
- location;
- annual consumption;
- meter ID placeholder;
- opening hours;
- renewable target;
- risk preference;
- data origin.

## Generator onboarding

Fields include:

- legal/site name;
- technology;
- capacity;
- location;
- meter/export ID placeholder;
- historical output;
- contract dates;
- price placeholder;
- certificate placeholder;
- data origin.

## Data upload

Reuse the Phase 4 validator. Show frequency, completeness, duplicates, anomalies, DST issues, readiness and an annotated preview.

## Simulated contracts

Show customer, generator, dates, pricing type, renewable target, limits and status. Mark all contracts simulated.

## Data operations

Show meter freshness, weather status, price status, quality score, manual-review queue and artifact update status.

## Acceptance

Demo onboarding works. Upload validation works. No real legal, billing or payment workflow is implied. Simulated contracts are visibly labelled. Tests and build pass.

## Execution prompt

```text
Read 24_PHASE_17_ADMIN_ONBOARDING.md and PROGRESS.md. Implement only onboarding, simulated contracts and data operations. Reuse the upload validator. Do not add real billing, legal execution or permanent private-data storage. Run tests and npm run build, update PROGRESS.md, and stop before Phase 18.
```
