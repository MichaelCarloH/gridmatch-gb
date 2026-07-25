# GridMatch GB

**Forecast, match and optimise clean power across Great Britain.**

GridMatch GB is an independent prototype built with public-market concepts and simulated meter data. It is not affiliated with or endorsed by Volter, Elexon, NESO or DESNZ.

## Run locally

```bash
npm run dev
```

Open `http://localhost:3000`. The dashboard has no external runtime dependencies. `GET /api/summary` exposes the portfolio snapshot used by the interface.

## Included prototype capabilities

- Day-ahead site and portfolio forecasting with 10th–90th percentile uncertainty bands
- Half-hourly demand/generation matching, grid residual and spill analysis
- Asymmetric-cost hedge recommendation
- Asset-performance, availability and anomaly monitoring
- Procurement, revenue, carbon and reporting views
- Deterministic synthetic half-hourly data generation and validation checks

## Data and research notes

`scripts/generate_synthetic_data.py` creates reproducible 48-period data for two business demand sites and three renewable assets. The model approach and its intended production evolution are recorded in [docs/research.md](docs/research.md). This project deliberately does not make claims about proprietary trading logic or customer data.

## Deploy

Import the repository in Vercel. Static files are served directly and `api/summary.js` is deployed as a serverless function. No environment variables are required for the demonstration build.
