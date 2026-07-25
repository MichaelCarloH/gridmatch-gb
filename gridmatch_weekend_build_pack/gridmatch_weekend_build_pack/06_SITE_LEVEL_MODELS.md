# Phase 6 — Individual Site-Level Forecasting Models

## Goal

Train and store one forecasting stack per selected site.

## Forecast target

Day-ahead half-hourly:

- business consumption;
- solar generation;
- wind generation.

Forecast:

- point;
- q10;
- q50;
- q90.

## Baselines

Implement:

- previous day;
- previous week;
- rolling same-period mean;
- persistence for short-horizon generation;
- physical solar baseline;
- stylised wind power-curve baseline.

## Statistical model

Use Ridge, Elastic Net or GAM.

Features:

- settlement period;
- cyclic time;
- weekday;
- weekend;
- bank holiday;
- weather;
- lags;
- rolling statistics;
- site metadata.

## ML model

Use LightGBM when practical, otherwise HistGradientBoosting.

Per site:

- point model;
- q10 model;
- q50 model;
- q90 model.

Also train a global fallback model by technology or archetype.

## Demand features

- lags 1, 2, 48, 96, 336;
- rolling mean and standard deviation;
- temperature;
- heating/cooling degree;
- business archetype;
- operating schedule;
- recent residual.

## Solar features

- irradiance;
- cloud;
- sun elevation;
- day of year;
- temperature;
- installed capacity;
- lagged output;
- recent bias.

Post-process:

- no negative output;
- no night-time output;
- no output above capacity.

## Wind features

- wind speed;
- squared and cubed wind speed;
- wind direction sine/cosine;
- gusts;
- pressure;
- capacity;
- lagged output;
- recent capacity factor.

Post-process:

- no negative output;
- no output above capacity.

## Validation

Use rolling-origin evaluation.

Store:

- issue time;
- valid time;
- horizon;
- training cutoff;
- model version;
- feature version.

Metrics:

- MAE;
- RMSE;
- nMAE;
- bias;
- pinball loss;
- interval coverage;
- interval width.

## Model artifacts

```text
artifacts/models/{site_id}/
├── baseline.json
├── point.joblib
├── q10.joblib
├── q50.joblib
├── q90.joblib
├── metadata.json
└── model_card.md
```

## Forecast artifacts

```text
artifacts/forecasts/site_forecasts.parquet
artifacts/metrics/site_metrics.parquet
artifacts/metrics/site_metrics.json
```

## Quantile invariant

Enforce:

```text
q10 <= q50 <= q90
```

Use sorting or monotonic repair after prediction when necessary.

## Acceptance criteria

- every selected site has forecasts;
- every site has baseline comparison;
- model artifacts load;
- forecasts include issue and valid times;
- quantile ordering holds;
- physical constraints hold;
- at least one model improves on the baseline.

## Codex execution prompt

```text
Implement Phase 6 from 06_SITE_LEVEL_MODELS.md. Train individual baseline, statistical and ML models for every demo site. Produce q10/q50/q90 forecasts, metrics, model cards and saved artifacts. Run rolling validation and enforce physical and quantile constraints. Do not proceed until all sites have loadable models and forecast artifacts.
```
