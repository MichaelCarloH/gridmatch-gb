# Model card — gen_wind_cumbria

## Purpose

Day-ahead half-hourly generation forecasting for the simulated
`Solway Wind` demo site. The stored stack includes a Ridge statistical model,
HistGradientBoosting point model and q10/q50/q90 quantile models.

## Training and validation

- Data origin: **simulated**
- Feature version: `site-features-v1`
- Model version: `site-forecast-v1`
- Final rolling-origin training cutoff: `2025-06-22T23:00:00+00:00`
- Validation: two expanding-window seven-day folds; no random split
- Forecast issue convention: exactly 48 half-hour periods before valid time
- Canonical baseline: `physical_wind`

## Performance

| Model | MAE (MWh) | RMSE (MWh) | nMAE | Bias (MWh) |
|---|---:|---:|---:|---:|
| physical_wind | 0.03373 | 0.04411 | 0.0112 | 0.00220 |
| persistence | 0.60240 | 0.85166 | 0.2008 | 0.06979 |
| previous_day | 0.60240 | 0.85166 | 0.2008 | 0.06979 |
| previous_week | 0.60453 | 0.86718 | 0.2015 | 0.09819 |
| rolling_same_period | 0.71381 | 0.90784 | 0.2379 | 0.03548 |
| hist_gradient_boosting | 0.03829 | 0.04991 | 0.0128 | 0.00042 |
| ridge | 0.05756 | 0.07911 | 0.0192 | 0.00310 |

The ML point model changes MAE by -13.51% versus the canonical
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
