# Architecture

## System boundary

```text
Next.js workspace route
→ shared typed API client
→ FastAPI route and Pydantic boundary
→ domain service
→ allowlisted artifact repository / bounded model cache
→ Parquet, JSON, Markdown or Joblib artifact
```

In public fallback mode, the API-client step resolves the same response
envelopes from indexed JSON bundles:

```text
Next.js workspace route
→ canonical API path
→ public/demo-data/fallback/index.json
→ bounded bundle response
```

No browser or API request accepts a filesystem path, downloads source data,
trains a model or runs a portfolio backtest.

## Repository layers

- `app/`: 50 App Router pages, including six workspaces and legacy technical
  evidence routes.
- `components/layout/`: persisted workspace shell, navigation, breadcrumbs,
  disclosures and artifact status.
- `components/workspaces/`: audience product logic for business, generator,
  operations, diversification, models, admin, demo and reports.
- `components/ui/` and `components/charts/`: traceable KPI explanations,
  loading/error/empty states, accessible charts and print/report primitives.
- `lib/`: typed API and fallback clients, formatting, settlement display,
  deterministic scenario definitions and browser upload validation.
- `api/routes/`: bounded HTTP parsing and public response schemas.
- `api/services/`: site, portfolio, matching, market, upload, research and
  saved-model business logic.
- `src/gridmatch/`: reusable data, validation, features, forecasting, matching
  and hedge logic shared by scripts and API services.
- `scripts/`: offline collection, builds, training, notebook execution,
  fallback generation and benchmarks.
- `data/` and `artifacts/`: generated, governed runtime evidence.

## Workspace model

The shared shell persists one of six perspectives:

- Business: consumption, renewable coverage, residual exposure and actions.
- Generator: output, commercial offtake, performance and scenario value.
- Operations: half-hour position, matching, risk and deterministic scenarios.
- Models: hierarchy, performance, calibration, registry, incidents and drift.
- Research: executed notebooks, model cards and source lineage.
- Admin: non-persistent onboarding, simulated contracts and data validation.

The perspectives do not duplicate model outputs. They interpret the same site,
forecast, matching, market, quality and registry artifacts.

## Quantitative flow

```text
Meter observations
→ DST-safe settlement validation and quality flags
→ weather and calendar features
→ site point + q10/q50/q90 forecasts
→ bottom-up and direct portfolio forecasts
→ coherent reconciled demand / generation / net
→ same-half-hour renewable allocation
→ residual requirement
→ scenario procurement recommendation
→ planned-versus-realised reconciliation
→ audience reports
```

Site observations remain auditable when invalid: validators add flags and
reports rather than silently deleting rows. GB settlement conversion supports
spring 46-period, normal 48-period and autumn 50-period days.

## Serving and safety

- Artifact availability is checked at startup and exposed through `/health`.
- Parquet/JSON reads are lazy, modification-aware and bounded.
- Query limits and pagination prevent wholesale observations or allocation
  responses.
- Saved-model inference enforces timezone, settlement alignment, quantile
  ordering and physical limits.
- CSV uploads are size/type checked, validated in memory and not retained.
- Scenario endpoints call lightweight existing functions only.
- Public notebook links and model paths are allowlisted or logical IDs.
- Planned, realised and scenario values remain separately labelled.

## Deployment modes

### Public demo

Next.js reads 116 generated static response views. This mode has no Python
runtime dependency and works on Vercel's static product surface.

### Local technical mode

`npm run dev` starts Next.js at port 3000 and FastAPI at port 8000. OpenAPI,
upload validation and compact saved-model inference are available.

### Combined deployed API

`vercel.json` packages the bounded FastAPI function and required runtime
artifacts. This mode should be retained only while platform bundle and duration
limits remain stable.

## Deferred production controls

Authentication, authorization, private object storage, legal contract
execution, billing, payments, live trade execution, distributed tracing,
rate limiting, a feature store and automated model promotion are outside the
prototype. See `LIMITATIONS.md`.
