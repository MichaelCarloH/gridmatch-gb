# Model card — dem_office_london

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Civic Quarter Offices` demo site. The stored stack includes a Ridge statistical model,
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
| rolling_same_period | 0.01473 | 0.01797 | 0.0347 | 0.01130 |
| previous_week | 0.01493 | 0.01843 | 0.0351 | 0.00396 |
| previous_day | 0.02128 | 0.03162 | 0.0501 | 0.00300 |
| hist_gradient_boosting | 0.01192 | 0.01488 | 0.0280 | 0.00422 |
| ridge | 0.01468 | 0.01855 | 0.0345 | 0.00590 |

The ML point model changes MAE by 19.10% versus the canonical
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
