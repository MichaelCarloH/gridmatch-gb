# GridMatch GB

Research-to-production prototype for forecasting, matching and hedging clean power across Great Britain.

This repository has completed **Phase 11: product frontend**. It contains cached public-source clients, a deterministic demonstration portfolio, DST-safe validation, reproducible notebooks, site and portfolio forecast stacks, commercial renewable matching, leakage-aware hedge scenarios, an artifact-backed FastAPI service, and a responsive Next.js clean-energy product.

## Quick start

```powershell
py -3 -m uv sync --extra dev
.\.venv\Scripts\Activate.ps1
npm install
python scripts/fetch_public_data.py
python scripts/build_demo_dataset.py
python scripts/validate_upload.py tests/fixtures/upload_valid.csv
python scripts/build_research_notebooks.py
python scripts/execute_notebooks.py
python scripts/train_site_models.py
python scripts/build_portfolio_forecast.py
python scripts/build_matching_allocations.py
python scripts/build_hedge_backtest.py
python scripts/build_model_registry.py
python -m pytest
npm run build
```

Run the complete local product:

```powershell
cmd /c npm run dev
```

OpenAPI documentation is available at `http://127.0.0.1:8000/docs`. The API
serves bounded generated artifacts and lightweight saved-model/scenario
inference only; it never trains or downloads data during a request.
Open the product at `http://127.0.0.1:3000`. The development command starts
both FastAPI and Next.js and proxies browser API requests through Next.js.
Use `npm run dev:frontend` or `npm run dev:api` only when intentionally
running the processes separately.

## Deploy

The repository is configured for a single Vercel deployment: Next.js serves
the product and the FastAPI application serves same-origin `/api/*` requests.
The bounded runtime artifacts required by the demo are included in the
deployment bundle, so production requests do not train models or fetch source
data.

```powershell
npx vercel@latest --prod
```

Set `NEXT_PUBLIC_GRIDMATCH_API_URL` only when the browser should use a separate
API origin. Local development and the standard Vercel deployment do not
require it.

See [PLAN.md](PLAN.md) for phase-prioritised work and [PROGRESS.md](PROGRESS.md) for the current implementation record.

Independent prototype. It does not represent Volter, Elexon, NESO or DESNZ systems, contracts or data.
