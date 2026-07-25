# Model card — dem_warehouse_manchester

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Trafford Distribution` demo site. The stored stack includes a Ridge statistical model,
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
| rolling_same_period | 0.01642 | 0.02062 | 0.0285 | 0.00933 |
| previous_week | 0.01882 | 0.02564 | 0.0327 | 0.00195 |
| previous_day | 0.02097 | 0.02704 | 0.0365 | 0.00160 |
| hist_gradient_boosting | 0.01525 | 0.01913 | 0.0265 | 0.00288 |
| ridge | 0.01484 | 0.01866 | 0.0258 | 0.00442 |

The ML point model changes MAE by 7.09% versus the canonical
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
