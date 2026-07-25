# Model card — dem_retail_birmingham

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Bullring Retail` demo site. The stored stack includes a Ridge statistical model,
HistGradientBoosting point model and q10/q50/q90 quantile models.

## Training and validation

- Data origin: **simulated**
- Feature version: `site-features-v1`
- Model version: `site-forecast-v1`
- Final rolling-origin training cutoff: `2025-06-22T23:00:00+00:00`
- Validation: two expanding-window seven-day folds; no random split
- Forecast issue convention: exactly 48 half-hour periods before valid time
- Canonical baseline: `rolling_same_period`

## Performance

| Model | MAE (MWh) | RMSE (MWh) | nMAE | Bias (MWh) |
|---|---:|---:|---:|---:|
| rolling_same_period | 0.01201 | 0.01519 | 0.0334 | 0.00853 |
| previous_week | 0.01288 | 0.01649 | 0.0358 | 0.00303 |
| previous_day | 0.01564 | 0.02081 | 0.0435 | 0.00190 |
| hist_gradient_boosting | 0.00983 | 0.01311 | 0.0273 | 0.00386 |
| ridge | 0.01075 | 0.01417 | 0.0299 | 0.00227 |

The ML point model changes MAE by 18.11% versus the canonical
baseline. Negative forecasts are clipped; generation is capped at installed
capacity, and solar output is forced to zero at night.

## Limitations

The meter and site data are simulated. Weather inputs are simulated realised
weather used as a forecast-weather proxy, not archived operational forecast
vintages. Metrics therefore demonstrate pipeline behaviour, not expected
production or commercial performance. Outage and curtailment availability are
not separately forecast.

## Production recommendations

Replace the weather proxy with issue-time forecast vintages, calibrate intervals
on a longer history, review flagged observations per use case, monitor drift and
coverage, and obtain human approval before forecasts influence trading.
