# Model card — gen_solar_cambridge

## Purpose

Day-ahead half-hourly generation forecasting for the simulated
`Fenland Solar` demo site. The stored stack includes a Ridge statistical model,
HistGradientBoosting point model and q10/q50/q90 quantile models.

## Training and validation

- Data origin: **simulated**
- Feature version: `site-features-v1`
- Model version: `site-forecast-v1`
- Final rolling-origin training cutoff: `2025-06-22T23:00:00+00:00`
- Validation: two expanding-window seven-day folds; no random split
- Forecast issue convention: exactly 48 half-hour periods before valid time
- Canonical baseline: `physical_solar`

## Performance

| Model | MAE (MWh) | RMSE (MWh) | nMAE | Bias (MWh) |
|---|---:|---:|---:|---:|
| physical_solar | 0.01307 | 0.02013 | 0.0062 | -0.00037 |
| persistence | 0.07976 | 0.13465 | 0.0380 | -0.00139 |
| previous_day | 0.07976 | 0.13465 | 0.0380 | -0.00139 |
| rolling_same_period | 0.10562 | 0.17223 | 0.0503 | 0.00438 |
| previous_week | 0.15975 | 0.25208 | 0.0761 | 0.02960 |
| hist_gradient_boosting | 0.01961 | 0.03361 | 0.0093 | -0.01043 |
| ridge | 0.01484 | 0.02283 | 0.0071 | -0.00701 |

The ML point model changes MAE by -50.02% versus the canonical
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
