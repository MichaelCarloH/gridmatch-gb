# GridMatch GB

GridMatch GB is a research-to-product prototype for forecasting business
electricity demand and renewable generation, commercially matching clean power
each GB half-hour, and explaining residual portfolio risk.

The repository implements the full core build and Extension Phases 11–20:

- business customer, renewable generator, portfolio operations, model
  operations, research and data-administration workspaces;
- DST-safe 46/48/50 settlement-period validation and auditable quality scores;
- reproducible public and deterministic simulated data pipelines;
- site, bottom-up, direct and reconciled probabilistic forecasts;
- conservation-tested renewable allocation;
- bounded procurement, risk, diversification and stress scenarios;
- artifact-backed FastAPI and static browser fallback;
- guided demo, calculation lineage and print-safe audience reports.

Public repository:
[MichaelCarloH/gridmatch-gb](https://github.com/MichaelCarloH/gridmatch-gb)

Existing production URL:
[gridmatch-gb.vercel.app](https://gridmatch-gb.vercel.app)

The URL may lag local Extension Phase 12–20 changes until an explicitly
authorized commit, push and production deployment are completed.

## Start locally

Install and synchronize the Python environment with uv, then install frontend
dependencies:

```powershell
py -3 -m uv sync --extra dev
npm install
```

Run the complete technical product:

```powershell
cmd /c npm run dev
```

Open:

- Product: `http://127.0.0.1:3000`
- Guided demo: `http://127.0.0.1:3000/demo`
- OpenAPI: `http://127.0.0.1:8000/docs`

The development command starts FastAPI and Next.js together and proxies
same-origin API requests.

## Public static-demo mode

Regenerate the read-only browser bundles:

```powershell
py -3 -m uv run python scripts/build_frontend_fallback.py
```

Build and run Next.js without FastAPI:

```powershell
cmd /c npm run build
cmd /c npm start
```

Append `?data=static` to any product route. The frontend resolves 116 indexed,
bounded API views from `public/demo-data/fallback/`. Interactive onboarding
remains non-persistent; CSV validation uses the Phase 4 API when available and
a bounded schema mirror in static mode.

## Rebuild the quantitative artifacts

These are offline commands. HTTP requests never fetch source data, train a
model or run a historical backtest.

```powershell
py -3 -m uv run python scripts/fetch_public_data.py
py -3 -m uv run python scripts/build_demo_dataset.py
py -3 -m uv run python scripts/validate_upload.py tests/fixtures/upload_valid.csv
py -3 -m uv run python scripts/build_research_notebooks.py
py -3 -m uv run python scripts/execute_notebooks.py
py -3 -m uv run python scripts/train_site_models.py
py -3 -m uv run python scripts/build_portfolio_forecast.py
py -3 -m uv run python scripts/build_matching_allocations.py
py -3 -m uv run python scripts/build_hedge_backtest.py
py -3 -m uv run python scripts/build_model_registry.py
```

## Verify

```powershell
py -3 -m uv run python -m pytest -q
py -3 -m uv run python scripts/execute_notebooks.py
cmd /c npm test
cmd /c npm run build
```

Current local evidence: 86 Python tests, four executed notebooks, 16 frontend
tests, 50 production pages, 43/43 extension route smoke checks, and 116 static
fallback API views.

## Deployment

The repository supports:

1. Public Vercel demo using bundled static artifacts.
2. Local technical mode with FastAPI and OpenAPI.
3. The existing combined Vercel function, where bundle limits permit.

Production deployment command:

```powershell
npx vercel@latest --prod
```

Set `NEXT_PUBLIC_GRIDMATCH_API_URL` only for an intentionally separate API
origin. The standard local and same-origin Vercel configurations do not need
it.

## Read next

- [Product walkthrough](PRODUCT_WALKTHROUGH.md)
- [90-second demo](DEMO_SCRIPT.md)
- [Architecture](ARCHITECTURE.md)
- [Data sources](DATA_SOURCES.md)
- [Model cards](MODEL_CARDS.md)
- [Limitations](LIMITATIONS.md)
- [Interview talking points](INTERVIEW_TALKING_POINTS.md)
- [Final audit](FINAL_AUDIT.md)
- [Implementation evidence](PROGRESS.md)

Independent prototype. It does not represent Volter, Elexon, NESO or DESNZ
systems, data, contracts or commercial claims.
