# GridMatch GB

Research-to-production prototype for forecasting, matching and hedging clean power across Great Britain.

This repository has completed **Phase 3: public and synthetic data collection**. It contains cached public-source clients, provenance manifests and a deterministic demonstration portfolio. Feature engineering, models, API logic and product pages remain intentionally deferred to later build-pack phases.

## Quick start

```bash
python -m pip install -e ".[dev]"
npm install
python -c "import gridmatch"
python scripts/fetch_public_data.py
python scripts/build_demo_dataset.py
npm run build
```

See [PLAN.md](PLAN.md) for phase-prioritised work and [PROGRESS.md](PROGRESS.md) for the current implementation record.

Independent prototype. It does not represent Volter, Elexon, NESO or DESNZ systems, contracts or data.
