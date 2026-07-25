# Model card — dem_warehouse_glasgow

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Clyde Logistics` demo site. The stored stack includes a Ridge statistical model,
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
| rolling_same_period | 0.01484 | 0.01975 | 0.0312 | 0.00856 |
| previous_week | 0.01650 | 0.02304 | 0.0347 | 0.00216 |
| previous_day | 0.01974 | 0.02650 | 0.0416 | 0.00107 |
| hist_gradient_boosting | 0.01329 | 0.01777 | 0.0280 | 0.00434 |
| ridge | 0.01307 | 0.01778 | 0.0275 | 0.00502 |

The ML point model changes MAE by 10.41% versus the canonical
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
