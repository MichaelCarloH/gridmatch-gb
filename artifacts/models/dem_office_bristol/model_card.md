# Model card — dem_office_bristol

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Harbourside Offices` demo site. The stored stack includes a Ridge statistical model,
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
| rolling_same_period | 0.01000 | 0.01226 | 0.0323 | 0.00724 |
| previous_week | 0.01041 | 0.01323 | 0.0336 | 0.00227 |
| previous_day | 0.01478 | 0.02269 | 0.0477 | 0.00206 |
| hist_gradient_boosting | 0.00874 | 0.01121 | 0.0282 | 0.00176 |
| ridge | 0.01074 | 0.01350 | 0.0346 | 0.00294 |

The ML point model changes MAE by 12.58% versus the canonical
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
