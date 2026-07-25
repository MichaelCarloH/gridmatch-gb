# Model card — dem_manufacturing_sheffield

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Sheffield Works` demo site. The stored stack includes a Ridge statistical model,
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
| rolling_same_period | 0.04201 | 0.05682 | 0.0350 | 0.03206 |
| previous_week | 0.04213 | 0.05913 | 0.0351 | 0.01031 |
| previous_day | 0.05417 | 0.07707 | 0.0451 | 0.00506 |
| hist_gradient_boosting | 0.03466 | 0.04810 | 0.0289 | 0.00786 |
| ridge | 0.03567 | 0.05019 | 0.0297 | 0.01163 |

The ML point model changes MAE by 17.50% versus the canonical
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
