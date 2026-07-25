# Model card — dem_retail_cardiff

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Taff Retail Park` demo site. The stored stack includes a Ridge statistical model,
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
| rolling_same_period | 0.01157 | 0.01402 | 0.0351 | 0.00859 |
| previous_week | 0.01161 | 0.01461 | 0.0352 | 0.00298 |
| previous_day | 0.01441 | 0.01914 | 0.0437 | 0.00144 |
| hist_gradient_boosting | 0.00946 | 0.01180 | 0.0287 | 0.00336 |
| ridge | 0.01016 | 0.01266 | 0.0308 | 0.00302 |

The ML point model changes MAE by 18.19% versus the canonical
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
