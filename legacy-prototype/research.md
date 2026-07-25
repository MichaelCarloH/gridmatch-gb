# Research note: forecasting, matching and hedge logic

## Forecasting design

Each site is modelled independently to preserve weather sensitivity, operating hours and asset characteristics. A production implementation would train quantile models using lagged meter values, calendar features, weather forecasts, capacity and recent residuals. Forecasts are emitted for all GB settlement periods (46, 48 or 50 around clock changes), then aggregated into a bottom-up portfolio forecast.

The dashboard compares that forecast with a direct portfolio model. A reconciliation layer would minimise weighted deviations from both while retaining coherent quantiles. The demo uses simulated figures and illustrates P10/P50/P90 rather than claiming live predictive performance.

## Matching and settlement

For every settlement period, matched clean energy is `min(demand, renewable generation)`. Grid residual is `max(demand - generation, 0)` and export/spill is `max(generation - demand, 0)`. The green match rate is matched energy divided by total demand.

## Hedge policy

The proposed day-ahead hedge is the quantile selected by asymmetric imbalance costs: select a higher demand quantile when short costs exceed long costs, and a lower quantile when the reverse is true. A trading decision should also consider liquidity, shape risk, credit terms and human approval. This is a research demonstration, not trading advice.

## Data quality rules

Records are expected in half-hourly settlement periods, with monotonic timestamps, non-negative energy and site capacity constraints. Missing intervals, duplicates, flatlines and material expected-versus-actual gaps become alerts before data flows to forecasts or financial reports.
