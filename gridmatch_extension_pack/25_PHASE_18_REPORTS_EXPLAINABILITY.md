# Phase 18 — Reports, Explainability and Guided Demo

## Goal

Make the complete system understandable in under two minutes while preserving technical depth.

## Guided demo

Button:

> Run the client demo

Steps:

1. Onboard and validate a supermarket.
2. Explain consumption.
3. Show day-ahead demand.
4. Show renewable supply.
5. Show commercial matching.
6. Show residual requirement.
7. Show recommended contracted volume.
8. Show business report.
9. Switch to generator and operator perspectives.
10. Open model methodology.

## How this was calculated

Add a reusable drawer:

```text
Meter data
→ validation
→ weather enrichment
→ site forecast
→ portfolio aggregation
→ renewable allocation
→ residual requirement
→ procurement recommendation
→ realised reconciliation
→ reporting
```

For each step show timestamp, version, input, output and methodology link.

## Reports

Create:

- business report;
- generator report;
- portfolio report.

All must print cleanly and disclose simulated data and scenario pricing.

## Acceptance

Guided demo works end to end. Every major metric has client, operational and technical explanations. No 404s or false first-render values. Tests and build pass.

## Execution prompt

```text
Read 25_PHASE_18_REPORTS_EXPLAINABILITY.md and PROGRESS.md. Implement only the guided demo, explainability drawer, reports and methodology polish. Preserve all outputs. Run route tests and npm run build, update PROGRESS.md, and stop before Phase 19.
```
