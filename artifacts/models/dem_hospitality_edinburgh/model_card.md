# Model card — dem_hospitality_edinburgh

## Purpose

Day-ahead half-hourly demand forecasting for the simulated
`Old Town Hotel` demo site. The stored stack includes a Ridge statistical model,
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
| rolling_same_period | 0.00924 | 0.01147 | 0.0319 | 0.00716 |
| previous_week | 0.00945 | 0.01184 | 0.0326 | 0.00229 |
| previous_day | 0.00992 | 0.01243 | 0.0342 | 0.00057 |
| hist_gradient_boosting | 0.00813 | 0.01022 | 0.0280 | 0.00111 |
| ridge | 0.00849 | 0.01069 | 0.0293 | 0.00270 |

The ML point model changes MAE by 12.09% versus the canonical
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
