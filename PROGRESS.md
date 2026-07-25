# Progress

## Current phase

Extension Phases 11–20: complete locally.

The Phase 11-only statements below are retained as historical evidence from
the earlier checkpoint; the final extension status and verification appear at
the end of this file.

Extension Phase 11 — Shared multi-workspace product shell: complete.
Original Phase 11 — Responsive artifact-backed product frontend: complete.
Requested GitHub publication and Vercel production deployment: complete.

## Preserved work and scope

- Phase 3 data pipelines, Phase 4 settlement and quality validation, Phase 5
  notebooks, Phase 6 site forecasts, Phase 7 portfolio forecasts, Phase 8
  renewable matching and Phase 9 hedge scenarios remain operational.
- All Phase 3–9 source artifacts and results remain unchanged.
- Training, data collection, historical backtesting and notebook execution
  remain offline commands and are never run inside API requests.
- `legacy-prototype/` remains archived and unchanged.
- The completed Phase 10 API contract remains unchanged and is the runtime
  data boundary for the product.
- Extension Phases 12–20 build on the preserved Phase 3–10 evidence without
  changing saved model outputs.
- The earlier GitHub publication and Vercel deployment remain available; the
  new local extension changes have not been externally published without
  explicit authorization.

## Extension Phase 11 shared product shell

Implemented workspace roots:

- `/business`
- `/generator`
- `/operations`
- `/models`
- `/research`
- `/admin`

Shared platform infrastructure:

- `WorkspaceProvider` and `WorkspaceSwitcher` persist the selected workspace
  in `gridmatch.workspace` and route to the selected workspace root.
- `PrimaryNav`, `SecondaryNav` and `Breadcrumbs` adapt the existing completed
  evidence routes to the active workspace.
- The shell persistently shows the exact forecast window, public/simulated/
  uploaded disclosure and API/artifact availability.
- `MetricExplanation`, `HowCalculatedDrawer`, `ActionCard`,
  `DataOriginBadge`, `ScenarioBadge`, `ArtifactStatus`,
  `LoadingSkeleton`, `ErrorState` and `EmptyState` are shared components.
- Root loading, error and not-found boundaries are implemented.
- First-render KPI placeholders use loading skeletons or explicit unavailable
  states; no count, zero or em dash is presented as hydrated evidence.
- Existing dashboard, forecast, map, matching, market, research, report and
  site calculations are unchanged.

Static fallback:

- `scripts/build_frontend_fallback.py` deterministically exports existing API
  responses from the committed artifacts.
- `public/demo-data/fallback/` contains seven route-grouped JSON bundles,
  an index and 115 read-only API views.
- Total fallback size is 2.25 MB.
- GET requests fall back automatically after API/network failure.
- `NEXT_PUBLIC_GRIDMATCH_FORCE_STATIC=true`, `?data=static` or the
  `gridmatch.data-delivery=static` local-storage setting forces the read-only
  fallback.
- Interactive POST recomputation remains live-API-only and reports that
  boundary explicitly.

Extension Phase 11 acceptance audit:

- Workspace switcher: passed.
- Primary and secondary navigation: passed.
- Route breadcrumbs: passed.
- Exact demo-period badge: passed.
- Persistent data-origin disclosure: passed.
- Global loading, error, empty and not-found states: passed.
- API and artifact availability indicator: passed.
- Static fallback without FastAPI: passed.
- Direct navigation for all workspace roots and `/research`: passed.
- No P0 workspace route returns 404: passed.
- No false first-render KPI: passed.
- Existing Phase 3–10 artifacts and calculations unchanged: passed.
- No Extension Phase 12 detail page started: passed.

## Phase 11 product surface

Implemented P0 routes:

- `/`: research-backed landing page with live site, model and matching counts.
- `/dashboard`: demand, generation, net position, hedge, uncertainty,
  matching, scenario cost and quality alerts.
- `/map`: 3,096 coordinate-valid operational public REPD assets from the
  3,100-project analysis, 12 modelled portfolio sites, active commercial
  matching arcs and the required asset filters.
- `/sites`: searchable/filterable operational table with origin, capacity,
  readiness and quality evidence.
- `/sites/[siteId]`: overview, forecast, actuals, weather, anomalies, model,
  quality and financial/ESG tabs.
- `/forecasts`: baseline, bottom-up, direct and reconciled comparison,
  probabilistic calibration, rolling forecasts and error attribution.
- `/matching`: matched energy, coverage, spill, residual import, period slider
  and generator-consumer allocation matrix.
- `/market`: public prices, hedge distribution, policy cost comparison and
  interactive lightweight assumption recomputation.
- `/research`: executed notebook summaries, registry evidence, lineage, data
  origins and limitations.
- `/reports`: procurement, matching, generator, emissions-method,
  forecast-performance and readiness reporting.

## Frontend architecture and design

- `components/layout/app-shell.tsx`: responsive dark navigation shell with
  active-route and mobile states.
- `lib/api.ts` and `lib/use-api.ts`: configurable runtime API boundary,
  abortable reads, stable loading/error state and retry.
- `scripts/dev.mjs`: one-command FastAPI + Next.js development orchestration;
  browser requests use same-origin `/api/*` rewrites, avoiding local CORS
  and hostname mismatches.
- `components/charts/`: dependency-free, units-aware SVG line and bar charts.
- `components/map/gb-map.tsx`: lightweight GB projection for public/modelled
  sites and commercial allocation arcs, using public-domain Natural Earth
  coastline geometry rather than a decorative silhouette.
- `components/ui/`: shared metric, badge, icon and state primitives.
- `app/globals.css`: the Phase 11 paper/surface/ink, green, blue, amber and red
  system, responsive grids, restrained cards and reduced-motion support.
- No external font, chart or map runtime dependency was added.

Data origins remain visible as public, simulated or uploaded. Charts label
MWh, MW, GBP or GBP/MWh. All API-backed pages have loading, error and empty
states. Scenario costs and matching arcs carry their required interpretation
warnings.

## Phase 11 acceptance audit

- No placeholder product pages: passed.
- Every P0 route consumes generated artifacts through Phase 10 endpoints or
  the exported public REPD GeoJSON: passed.
- Landing, dashboard, map, sites/detail, forecast lab, matching, market,
  research and reports: passed.
- Responsive desktop, tablet and mobile layouts: passed.
- Visible units, origins, warnings and methodological boundaries: passed.
- Loading, error, empty and retry states: passed.
- Production TypeScript, lint and Next.js build: passed.
- Phase 12 not started; the separately requested publication/deployment slice
  is complete.

## API architecture

The request path is:

```text
typed FastAPI route
→ domain service
→ allowlisted artifact repository / saved-model cache
→ Parquet, JSON, Markdown or Joblib artifact
```

- `api/index.py`: application factory, OpenAPI description, CORS, response
  limits and router registration.
- `api/dependencies.py`: typed environment configuration.
- `api/errors.py`: stable error envelopes for domain, validation and internal
  errors.
- `api/schemas/`: Pydantic public requests and responses.
- `api/routes/`: thin health, site, portfolio, matching, market, upload,
  research and model handlers.
- `api/services/artifact_repository.py`: approved logical paths, lazy loading,
  bounded LRU caching and modification-time invalidation.
- `api/services/*_service.py`: filtering, mapping, validation and lightweight
  business logic.

## Implemented endpoints

Health and metadata:

- `GET /health`
- `GET /api/meta`

Sites:

- `GET /api/sites`
- `GET /api/sites/{site_id}`
- `GET /api/sites/{site_id}/observations`
- `GET /api/sites/{site_id}/quality`
- `GET /api/sites/{site_id}/forecast`
- `GET /api/sites/{site_id}/metrics`
- `GET /api/sites/{site_id}/alerts`
- `GET /api/sites/{site_id}/model-card`

Portfolio and map:

- `GET /api/portfolio/forecast`
- `GET /api/portfolio/metrics`
- `GET /api/portfolio/error-attribution`
- `GET /api/portfolio/correlation`
- `GET /api/map/sites.geojson`
- `GET /api/map/matching-arcs`

Matching:

- `GET /api/matching/summary`
- `GET /api/matching/periods`
- `GET /api/matching/allocations`
- `GET /api/matching/consumers`
- `GET /api/matching/generators`
- `GET /api/matching/comparison`

Market and hedge:

- `GET /api/market/prices`
- `GET /api/market/hedge-recommendations`
- `GET /api/market/policy-summary`
- `GET /api/market/sensitivity`
- `POST /api/market/hedge-simulate`
- `POST /api/hedge/simulate` compatibility route

Upload, research and models:

- `POST /api/upload/validate`
- `GET /api/research/notebooks`
- `GET /api/research/notebooks/{notebook_id}`
- `GET /api/models`
- `GET /api/models/{model_id}`
- `POST /api/forecast/predict`

OpenAPI is available at `/docs` and `/openapi.json`. The schema contains 34
operations.

## Configuration and safety

- Supported environment variables:
  - `GRIDMATCH_DATA_DIR`
  - `GRIDMATCH_ARTIFACT_DIR`
  - `GRIDMATCH_DEMO_MODE`
  - `GRIDMATCH_CORS_ORIGINS`
  - `GRIDMATCH_MAX_RESPONSE_ROWS`
  - `GRIDMATCH_MODEL_CACHE_SIZE`
  - `GRIDMATCH_UPLOAD_MAX_BYTES`
- Demo mode needs no credentials and no external network access.
- Local CORS defaults only to `http://localhost:3000`; wildcard origins are
  ignored.
- Required artifact availability is checked when the app is created.
  `/health` reports `degraded`, never `healthy`, when any P0 artifact is
  missing.
- Response and upload sizes are bounded. Observations and 19,024 map arcs are
  never returned wholesale by default.
- Uploads require CSV content type and extension, are decoded as UTF-8,
  validated in memory, previewed compactly and never permanently stored.
- Notebook paths are allowlisted artifact links; model paths are logical
  `model://` identifiers.
- Errors never expose filesystem paths or stack traces.

## Model registry and inference

Generated:

- `artifacts/models/model_registry.parquet`
- `artifacts/models/model_registry.json`

Registry contents:

- 90 total estimator records.
- 60 site estimator records across 12 sites.
- 15 global demand/solar/wind fallback records.
- 15 direct portfolio demand/generation/net records.
- Every artifact path is a logical `model://` identifier.

Compact prediction:

- accepts one valid site, one to 48 future rows, issue time, weather fields and
  documented lag/rolling inputs;
- reconstructs all 41 Phase 6 features;
- verifies timezone, half-hour alignment and Europe/London settlement period;
- loads existing point/q10/q50/q90 models from the bounded cache;
- applies non-negativity, capacity, night-solar and quantile-ordering rules;
- never trains or downloads models.

## Upload validation

`POST /api/upload/validate` returns inferred frequency, date range, received
and expected rows, completeness, duplicates, a bounded 0–100 score, readiness,
anomaly counts, recommended actions and a ten-row annotated preview. It reuses
`gridmatch.data.uploads.validate_csv_upload`.

## Performance evidence

Local TestClient benchmark, 15 warm repetitions:

| Endpoint | Cold | Warm mean | Warm p95 | Target |
|---|---:|---:|---:|---:|
| Health | 6.144 ms | 4.670 ms | 5.914 ms | 100 ms |
| Site list | 61.234 ms | 10.031 ms | 11.080 ms | 250 ms |
| Portfolio forecast | 42.476 ms | 40.060 ms | 37.778 ms | 500 ms |
| Matching summary | 3.612 ms | 2.109 ms | 2.492 ms | 500 ms |
| Hedge scenario | 20.895 ms | 8.085 ms | 8.651 ms | 100 ms |

All warm targets passed. These are local prototype measurements, not a
production service-level agreement.

Generated benchmark evidence:

- `artifacts/metrics/api_benchmark.json`

## Phase 10 P0 acceptance audit

- Typed environment configuration and documented local defaults: passed.
- Route → service → artifact repository separation: passed.
- Lazy, bounded, modification-aware artifact cache: passed.
- Healthy/degraded artifact and registry reporting: passed.
- Site metadata, filtering, search and pagination: passed.
- Bounded and date-filtered observations with quality flags: passed.
- Site forecasts, ordered quantiles, metrics, quality, alerts and cards:
  passed.
- Portfolio methods, totals, intervals, metrics, attribution and correlation:
  passed.
- Valid site GeoJSON and filtered matching arcs: passed.
- Forecast/realised and maximum/local matching separation: passed.
- Matching conservation exposed and tested: passed.
- Public prices, recommendations, policy metrics and sensitivity: passed.
- Hedge scenario reuses the Phase 9 lightweight function and enforces
  assumptions and a ±10 MWh operational limit: passed.
- Safe in-memory CSV validation with size/content checks: passed.
- Existing saved-model inference with physical constraints and no training:
  passed.
- Allowlisted research metadata: passed.
- Consolidated 90-record logical model registry: passed.
- Pydantic public schemas, ISO timestamps, units and JSON-safe numbers: passed.
- Stable 400/404/413/415/422/500/503 error handling: passed.
- OpenAPI descriptions, warnings and scenario disclaimers: passed.
- Environment-only CORS allowlist and bounded responses: passed.
- Cold/warm benchmark and all local targets: passed.
- No Phase 10 P0 gaps remain.

## Verification evidence

- `py -3 -m uv lock`: passed; 84 packages resolved.
- `py -3 -m uv sync --extra dev`: passed; FastAPI, Uvicorn, multipart and
  TestClient dependencies installed.
- `.\.venv\Scripts\python.exe scripts\build_model_registry.py`: passed; 90
  logical model records generated.
- `.\.venv\Scripts\python.exe -m uvicorn api.index:app --host 127.0.0.1
  --port 8000`: started successfully.
- Live `GET http://127.0.0.1:8000/health`: returned `healthy` with all required
  artifacts available.
- Uvicorn PID 29424 was verified by command line and stopped cleanly after the
  health check.
- `.\.venv\Scripts\python.exe scripts\benchmark_api.py`: passed; every target
  met.
- `.\.venv\Scripts\python.exe -m pytest`: 83 passed in 16.18 seconds without
  warnings.
- `.\.venv\Scripts\python.exe scripts\execute_notebooks.py`: passed; all four
  existing notebooks executed.
- `cmd /c npm run lint`: passed with no warnings or errors.
- `cmd /c npm test`: 4 Phase 11 product acceptance tests passed.
- `cmd /c npm run build`: passed; Next.js compiled, linted, type-checked and
  generated 12 routes (ten P0 product routes plus the not-found route).
- Production-server route smoke test: `/`, `/dashboard`, `/map`, `/sites`,
  `/sites/dem_office_london`, `/forecasts`, `/matching`, `/market`,
  `/research` and `/reports` all returned HTTP 200.
- Live development proxy smoke test: health, 12 sites, 626 portfolio forecast
  rows, matching summary and 58 public-price records loaded through port 3000.

## GitHub and Vercel publication

- Public repository:
  `https://github.com/MichaelCarloH/gridmatch-gb`
- Draft publication pull request:
  `https://github.com/MichaelCarloH/gridmatch-gb/pull/1`
- Production product:
  `https://gridmatch-gb.vercel.app`
- Vercel is connected to the GitHub repository.
- Deployment packages Next.js and FastAPI under one origin; production
  `/api/*` requests route to `api/index.py`.
- Research/notebook dependencies remain available through
  `uv sync --extra dev` but are excluded from the production Python
  dependency set.
- Runtime artifacts are committed and included in the function bundle;
  production requests do not fetch source data or train models.
- Final Python function bundle: 422.98 MB, below Vercel's 500 MB limit.
- External HTTP checks passed for `/`, `/dashboard`, `/map` and `/sites`.
- External artifact-backed API checks returned HTTP 200 with data for
  `/api/sites?limit=1`, `/api/portfolio/forecast?limit=1`,
  `/api/matching/summary` and `/api/market/prices?limit=1`.
- Publication verification: 83 Python tests passed, 4 frontend tests passed,
  and the Next.js 15.5.21 production build passed.

## Extension Phase 11 verification

- `.\.venv\Scripts\python.exe scripts\build_frontend_fallback.py`: passed;
  115 indexed static API views generated across seven bundles.
- `.\.venv\Scripts\python.exe -m pytest -q`: 86 passed in 23.40 seconds.
- `cmd /c npm test`: 10 tests passed across the original product and extension
  shell suites.
- `cmd /c npm run build`: passed; Next.js generated 17 static pages and listed
  every required workspace root.
- `cmd /c npm start -- -p 3100`: production server started without FastAPI.
- Direct HTTP navigation returned 200 for `/business`, `/generator`,
  `/operations`, `/models`, `/research`, `/admin` and
  `/dashboard?data=static`.
- `/demo-data/fallback/index.json` and `core.json` returned HTTP 200 while
  `/api/sites` correctly returned 404 with FastAPI absent; the forced-static
  frontend test loaded the bundled 12-site response instead.
- The exact port-3100 Node test process was stopped after verification.
- `cmd /c npm run dev`: the combined local stack started successfully;
  `/business`, `/generator`, `/operations`, `/models`, `/research`, `/admin`,
  `/health` and `/api/sites?limit=1` all returned HTTP 200.
- The exact port-3000 and port-8000 test listeners were stopped after the
  local-API verification.

## Known prototype limitations

- Portfolio, forecast, allocation and hedge-volume inputs are simulated.
- Phase 9 prices remain a non-contemporaneous public scenario reference.
- The artifact cache is in-process; multi-worker production deployment would
  need shared storage/cache and observability.
- Compact prediction requires caller-supplied lag and rolling features and
  assumes weather inputs were available at issue time.
- Authentication, rate limiting, distributed tracing and production object
  storage are intentionally deferred.
- Scenario costs are not realised savings, financial advice or executable
  trading instructions.

## Extension Phases 12–20

Status: implemented and verified locally on 25 July 2026.

### Phase 12 — business customer portal

Generated:

- `/business`, `/business/sites`, `/business/sites/[siteId]`,
  `/business/renewables`, `/business/energy-plan` and `/business/reports`.
- Artifact-backed consumption, renewable match, coverage, residual, scenario
  cost, action and quality KPIs with units, source, calculation and limitation.
- Site load, peak, baseload, probabilistic forecast, anomalies, quality and
  archetype context.
- Client-language energy plan and print-safe business report.

### Phase 13 — renewable generator portal

Generated:

- `/generator`, `/generator/output`, `/generator/offtake`,
  `/generator/revenue`, `/generator/assets`, `/generator/sites/[siteId]` and
  `/generator/reports`.
- Output, q10/q50/q90, capacity factor, weather, availability, commercial
  allocation, unused output and asset incidents.
- Reference-price revenue and underperformance scenarios with explicit
  invoice, contract and physical-routing boundaries.

### Phase 14 — operations control room

Generated:

- `/operations`, `/operations/portfolio`, `/operations/forecasts`,
  `/operations/matching`, `/operations/risk` and `/operations/scenarios`.
- Half-hour demand, generation, matching, residual, contracted-volume proxy,
  adjustment, quantiles and realised-result table.
- Planned/realised charts; short/long risk, scenario cost, p95, CVaR95, bias,
  quality and error drivers.
- Explicit demand, solar, wind, matching and price deviation attribution.
- Bounded short/long price, demand, low-wind, solar-shortfall, generator-outage,
  missing-data and model controls with no trade execution or retraining.

### Phase 15 — diversification lab

Generated:

- `/operations/diversification`, `/operations/concentration`,
  `/operations/stress-tests` and `/operations/portfolio-addition`.
- Saved 12 × 12 site-error correlation view and site risk-contribution
  estimates.
- Largest, top-five and HHI concentration by customer, generator, region,
  technology and archetype.
- Eight stable deterministic stress scenarios and four hypothetical addition
  profiles. No request-time training.

The static fallback now includes `/api/portfolio/correlation`.

### Phase 16 — model operations

Generated:

- `/models`, `/models/performance`, `/models/calibration`, `/models/registry`,
  `/models/incidents` and `/models/data-drift`.
- Site → global fallback → bottom-up → direct → reconciled hierarchy and
  selection rationale.
- MAE, RMSE, bias, pinball loss, q10/q50/q90 empirical reliability, aggregate
  interval coverage/width and registry lineage.
- Horizon, settlement-period, representative-site and deterministic
  weather-regime performance drill-down.
- Missing-artifact, quantile-crossing, physical-limit, challenger, bias and
  quality checks.
- Drift proxies are labelled as short-window artifact monitoring, not
  fabricated production MLOps.

### Phase 17 — admin and data operations

Generated:

- `/admin`, `/admin/customers`, `/admin/customers/new`, `/admin/generators`,
  `/admin/generators/new`, `/admin/contracts`, `/admin/data`,
  `/admin/data/uploads` and `/admin/data/incidents`.
- Non-persistent customer and generator previews.
- Visibly simulated contracts with no legal, billing, certificate or payment
  claim.
- Meter/weather/price/artifact readiness and manual-review queue.
- Live mode uses the Phase 4 upload API. Static mode uses a bounded browser
  schema mirror. Both preserve annotated preview rows and disable storage.

### Phase 18 — demo, reports and explainability

Generated:

- `/demo` ten-step guided client flow.
- Business, generator and portfolio print-safe reports.
- Full metric lineage:
  meter → validation → weather → site forecast → portfolio → allocation →
  residual → recommendation → reconciliation → reporting.
- Each lineage step exposes version, timestamp context, input/output and a
  methodology link.

### Phase 19 — integration and deployment audit

- All 43 extension and supporting routes returned HTTP 200 through a production
  Next.js server with FastAPI absent and `?data=static`.
- Static fallback version `extension-phase20-v1` contains 116 canonical API
  views across seven bundles.
- Correlation fallback contains 12 site IDs and 12 matrix rows.
- Local combined mode returned HTTP 200 for representative business,
  diversification, model-incident and upload pages, plus `/health`,
  `/api/sites?limit=1`, `/api/portfolio/correlation` and
  `/api/market/policy-summary`.
- Live upload validation returned 100 / 100, `ready`, three annotated preview
  rows and `permanent_storage=false`.
- The production build generated 50 pages with shared first-load JavaScript of
  103 kB; route-specific first-load totals were 107–117 kB.
- Responsive, reduced-motion, print, chart-label and table-caption rules are
  present.
- The existing GitHub/Vercel publication remains documented. These local
  extension changes were not pushed or redeployed because this implementation
  request did not explicitly authorize external publication.

### Phase 20 — interview packaging

Generated or refreshed:

- `README.md`
- `ARCHITECTURE.md`
- `DATA_SOURCES.md`
- `MODEL_CARDS.md`
- `LIMITATIONS.md`
- `DEMO_SCRIPT.md`
- `INTERVIEW_TALKING_POINTS.md`
- `PRODUCT_WALKTHROUGH.md`
- `FINAL_AUDIT.md`

The package includes a 90-second walkthrough, product narrative, claims
guardrails, expected interview questions, verification evidence and the honest
coding-agent statement.

## Extension verification commands and results

- `py -3 -m uv run python scripts/build_frontend_fallback.py`: passed; 116
  static API views across seven bundles.
- `cmd /c npx tsc --noEmit`: passed.
- `cmd /c npm test`: the first sandboxed launch could not let esbuild read the
  config root; the authorized rerun passed 16 / 16 tests in three files.
- `cmd /c npm run build`: initial corrective runs identified the missing
  `PortfolioMetric.interval_width` type and two over-narrow literal state
  types. After fixes, the final build passed and generated 50 pages.
- `cmd /c npm start -- -p 3100`: passed; 43 / 43 direct static-mode routes
  returned HTTP 200.
- `cmd /c npm run dev`: passed; Next.js and FastAPI started together and all
  representative page/API checks returned HTTP 200.
- `curl.exe -sS -F
  "file=@tests/fixtures/upload_valid.csv;type=text/csv"
  http://127.0.0.1:3000/api/upload/validate`: passed; score 100, ready, zero
  anomalies, three preserved preview rows and no storage.
- `py -3 -m uv run pytest -q`: failed because the console entry point did not
  include the repository root on `sys.path`.
- `py -3 -m uv run python -m pytest -q`: passed; 86 tests in 17.71 seconds.
- `py -3 -m uv run python scripts/execute_notebooks.py`: passed; all four
  notebooks executed in 5.510, 3.494, 4.331 and 3.855 seconds. Jupyter emitted
  its expected local TCP-without-encryption warning.

## Current state

Extension Phases 11–20 are complete locally. The next external action is an
intentional commit, push and production deployment, which requires explicit
authorization because it changes the public repository and live URL.
