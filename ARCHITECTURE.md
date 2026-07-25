# Architecture

## Current boundary

GridMatch separates the presentation shell (`app/`, `components/`, `lib/`),
the HTTP boundary (`api/`), reusable research/domain logic
(`src/gridmatch/`), offline build scripts (`scripts/`) and generated
artifacts (`data/`, `artifacts/`).

The product follows this request path:

```text
Next.js product route
→ shared client hook
→ typed HTTP client
→ FastAPI route
→ domain service
→ allowlisted artifact repository / saved-model cache
→ Parquet, JSON, Markdown or Joblib artifact
```

Route handlers parse bounded inputs and select response schemas. Services own
filtering, business rules, conservation checks and lightweight inference.
The artifact repository owns approved logical paths, lazy reads,
modification-aware cache invalidation and bounded least-recently-used caching.
No endpoint accepts a filesystem path.

## Frontend product

`app/` contains ten P0 product routes: landing, dashboard, GB map, sites,
site detail, forecast lab, matching, market, research and reports.
`components/` contains the responsive application shell, units-aware SVG
charts, the GB projection and shared loading/error/empty states. `lib/`
contains the runtime API boundary, display types and Europe/London-aware
formatting.

The browser reads the Phase 10 API at
same-origin `/api/*` paths, which Next.js rewrites locally to
`GRIDMATCH_API_INTERNAL_URL` (default `http://127.0.0.1:8000`). A public
`NEXT_PUBLIC_GRIDMATCH_API_URL` override is reserved for deliberately
split-host deployments. On Vercel, `/api/*` is served by the bundled FastAPI
function. Public REPD map evidence is exported as a static
GeoJSON research layer; portfolio sites, matching arcs and all decision
metrics come from bounded API endpoints. `npm run dev` starts both FastAPI and
Next.js and terminates them together.
No frontend route trains a model, runs a backtest or downloads external data.

## API package

```text
api/
├── index.py                 application factory, CORS and routers
├── dependencies.py          typed environment configuration
├── errors.py                stable error envelopes
├── schemas/                 public Pydantic requests/responses
├── routes/                  thin HTTP handlers
└── services/
    ├── artifact_repository.py
    ├── site_service.py
    ├── portfolio_service.py
    ├── matching_service.py
    ├── market_service.py
    ├── upload_service.py
    ├── research_service.py
    └── model_service.py
```

## Serving behaviour

- Required artifacts are inspected when the app is created. `/health` is
  `degraded`, never `healthy`, if any required P0 artifact is missing.
- Parquet and JSON reads are lazy. Cached entries are reused until file
  modification time changes and the configured cache remains bounded.
- Response rows and query limits are bounded. Observations and 19,024 matching
  arcs are never returned wholesale by default.
- CSV uploads are size- and content-type checked, decoded as UTF-8, validated
  in memory and not retained.
- Compact prediction reconstructs the documented site feature vector and
  loads existing Joblib estimators. It enforces GB settlement alignment,
  quantile ordering and physical constraints.
- Hedge simulation calls the Phase 9 single-scenario function. It does not run
  a historical backtest.
- Notebook and model paths returned publicly are allowlisted relative links or
  logical `model://` identifiers.

## Offline-only work

Public-data collection, demo generation, validation artifact generation,
notebook execution, model training, portfolio backtests, renewable-allocation
builds, hedge backtests and model-registry creation remain command-line build
steps. They are never triggered by HTTP requests.

## Configuration and deployment

The API reads `GRIDMATCH_DATA_DIR`, `GRIDMATCH_ARTIFACT_DIR`,
`GRIDMATCH_DEMO_MODE`, `GRIDMATCH_CORS_ORIGINS`,
`GRIDMATCH_MAX_RESPONSE_ROWS`, `GRIDMATCH_MODEL_CACHE_SIZE` and
`GRIDMATCH_UPLOAD_MAX_BYTES`. Demo mode needs no credentials and makes no
network request. CORS has no wildcard default; local development allows only
`http://localhost:3000`.

The current application is a local prototype. Authentication, production
object storage, distributed caching, observability, rate limiting, Phase 12
QA and deployment are later-phase concerns.
