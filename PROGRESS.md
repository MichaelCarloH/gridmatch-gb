# Progress

## Current phase

Phase 11 — Responsive artifact-backed product frontend: complete.

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
- Phase 12 QA and Phase 13 deployment were not started.

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
- Phase 12 and deployment not started.

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

## Next

Proceed to Phase 12 (`12_TESTING_AND_QA.md`) only when explicitly requested.
