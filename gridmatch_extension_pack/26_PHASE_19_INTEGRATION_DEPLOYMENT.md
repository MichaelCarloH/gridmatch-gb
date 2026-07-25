# Phase 19 — Integration, QA and Deployment

## Goal

Make the multi-workspace platform reliable enough to send externally.

## Audit

Verify consistent:

- site IDs;
- units;
- dates;
- forecast methods;
- data-origin labels;
- planned/realised values;
- scenario assumptions;
- model versions.

## Required checks

- direct navigation to every route;
- no 404s;
- no false zero values;
- no permanent loading states;
- no placeholders;
- no filesystem paths;
- static fallback without API;
- local FastAPI mode;
- production build;
- mobile;
- slow network;
- incognito;
- accessibility;
- chart descriptions;
- pagination and response sizes.

## Deployment modes

### Public demo

Static bundled artifacts on Vercel.

### Local technical mode

Full FastAPI and OpenAPI.

### Optional deployed API

Only if stable and free-tier compatible.

## Acceptance

Public URL works. All main routes load directly. Static fallback works. Tests, notebooks and build pass. README deployment steps are accurate.

## Execution prompt

```text
Read 26_PHASE_19_INTEGRATION_DEPLOYMENT.md and PROGRESS.md. Perform the full integration, route, accessibility, performance and deployment audit. Fix every P0 issue. Preserve quantitative outputs. Run all tests, notebooks and the production build. Update PROGRESS.md and stop only when Phase 19 criteria pass.
```
