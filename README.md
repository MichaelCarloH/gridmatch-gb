# GridMatch GB

Research-to-production prototype for forecasting, matching and hedging clean power across Great Britain.

This repository has completed **Phase 6: individual site-level forecasting models**. It contains cached public-source clients, a deterministic demonstration portfolio, DST-safe settlement and quality validation, four reproducible research notebooks, and loadable per-site baseline/statistical/probabilistic forecast stacks. Portfolio models, matching, hedging, APIs and product pages remain intentionally deferred.

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
python -m pytest
npm run build
```

See [PLAN.md](PLAN.md) for phase-prioritised work and [PROGRESS.md](PROGRESS.md) for the current implementation record.

Independent prototype. It does not represent Volter, Elexon, NESO or DESNZ systems, contracts or data.
