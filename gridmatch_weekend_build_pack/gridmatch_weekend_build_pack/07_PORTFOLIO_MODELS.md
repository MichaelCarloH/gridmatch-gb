# Phase 7 — Portfolio Forecasting and Reconciliation

## Goal

Translate site forecasts into the quantity that an energy operator must manage.

## Definitions

```math
Demand_t = \sum_i demand_{i,t}
```

```math
Generation_t = \sum_j generation_{j,t}
```

```math
NetPosition_t = Demand_t - Generation_t
```

Positive net position means electricity must be procured.

Negative net position means excess generation.

## Bottom-up forecast

Sum site forecasts.

For probabilistic intervals, start with empirical simulation or a documented approximation. Do not blindly sum q10 and q90 and call the result statistically exact.

Minimum acceptable approach:

- sample from each site’s predictive interval;
- preserve a simple portfolio correlation factor;
- aggregate samples;
- calculate portfolio quantiles.

## Direct portfolio model

Train directly on:

- aggregate demand;
- aggregate generation;
- net position.

Use:

- weather aggregates;
- calendar;
- recent portfolio lags;
- site-composition features.

## Reconciled forecast

Minimum version:

```math
Forecast^{REC}_t
=
w Forecast^{DIR}_t
+
(1-w) Forecast^{BU}_t
```

Select `w` from validation performance.

## Comparisons

Evaluate:

- site model aggregation;
- direct model;
- reconciled model;
- baseline.

Metrics:

- MAE;
- RMSE;
- bias;
- peak error;
- pinball loss;
- interval coverage;
- simulated hedge cost.

## Error attribution

Produce:

- site contribution to portfolio error;
- technology contribution;
- region contribution;
- correlated forecast-error heatmap.

## Required outputs

```text
artifacts/forecasts/portfolio_forecasts.parquet
artifacts/metrics/portfolio_metrics.json
artifacts/figures/portfolio_comparison.png
```

## Acceptance criteria

- bottom-up forecast exists;
- direct model exists;
- reconciled forecast exists;
- portfolio intervals exist;
- portfolio totals equal site aggregation;
- comparison metrics exist;
- dashboard-ready output exists.

## Codex execution prompt

```text
Implement Phase 7 from 07_PORTFOLIO_MODELS.md. Build bottom-up, direct and reconciled portfolio forecasts. Generate probabilistic portfolio intervals using a documented simulation approach, compare performance and export dashboard-ready artifacts.
```
