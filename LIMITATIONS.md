# Limitations

GridMatch GB is an independently built research-to-product prototype. It is
not a Volter production system and it does not represent Elexon, NESO, DESNZ,
a licensed supplier, or a generator contract.

## Data

- The 12-site business and generator portfolio is deterministic and simulated.
- REPD assets and cached GB market references are public-source evidence.
- The price window is non-contemporaneous with the forecast validation window,
  so all cost and revenue values are scenarios.
- Weather available in the prototype uses a realised-weather proxy. Production
  forecasting would require weather forecasts available at issue time.
- Browser fallback bundles are generated snapshots, not live feeds.
- Uploaded CSV files are validated in memory and are never permanently stored.

## Models and decisions

- Metrics come from temporal backtests, not live production monitoring.
- Model-operations incidents are artifact-derived checks, not alerts from a
  production feature store or scheduler.
- The compact API can run saved-model inference but never trains in a request.
- Scenario controls and portfolio additions use fixed documented
  approximations. They do not retrain models.
- Probabilistic intervals describe empirical uncertainty; they are not
  guarantees.
- Renewable matching is commercial same-half-hour allocation, not the physical
  route of electricity.
- Hedge recommendations are decision support. Procurement execution belongs to
  a licensed supplier or utility partner.

## Commercial boundary

- There are no real customers, meters, contracts, invoices, payments, tariffs,
  certificate claims or Volter terms.
- All contracts shown in the admin workspace are visibly simulated.
- Costs, revenue and underperformance values are scenarios, not realised
  savings, bills or financial advice.
- No emissions-saving claim is made because a governed carbon-factor and
  certificate methodology is outside the current evidence.

## Engineering boundary

- Public demo mode can read bundled static artifacts without FastAPI.
- Local technical mode includes FastAPI and OpenAPI.
- Authentication, authorization, rate limiting, distributed caching,
  production object storage, tracing and private-data governance are not
  implemented.
- The published URL may lag local uncommitted changes until an explicitly
  authorized deployment is performed.
