# GridMatch GB

Research-to-production prototype for forecasting, matching and hedging clean power across Great Britain.

This repository has completed **Phase 5: research notebook framework and notebooks 00–03**. It contains cached public-source clients, a deterministic demonstration portfolio, typed domain schemas, DST-safe settlement utilities, row-preserving quality reports, CSV upload validation and four reproducible research notebooks. Feature engineering, forecasting, portfolio models, APIs and product pages remain intentionally deferred.

## Quick start

```bash
python -m pip install -e ".[dev]"
npm install
python -c "import gridmatch"
python scripts/fetch_public_data.py
python scripts/build_demo_dataset.py
python scripts/validate_upload.py tests/fixtures/upload_valid.csv
python scripts/build_research_notebooks.py
python scripts/execute_notebooks.py
python -m pytest
npm run build
```

See [PLAN.md](PLAN.md) for phase-prioritised work and [PROGRESS.md](PROGRESS.md) for the current implementation record.

Independent prototype. It does not represent Volter, Elexon, NESO or DESNZ systems, contracts or data.
