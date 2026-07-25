# Model card — gen_wind_aberdeenshire

## Purpose

Day-ahead half-hourly generation forecasting for the simulated
`Dee Wind` demo site. The stored stack includes a Ridge statistical model,
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
| physical_wind | 0.04170 | 0.05582 | 0.0111 | -0.00492 |
| persistence | 0.70737 | 1.01478 | 0.1886 | 0.03844 |
| previous_day | 0.70737 | 1.01478 | 0.1886 | 0.03844 |
| previous_week | 0.71373 | 1.02722 | 0.1903 | 0.00748 |
| rolling_same_period | 0.92370 | 1.17343 | 0.2463 | 0.06558 |
| hist_gradient_boosting | 0.04678 | 0.05946 | 0.0125 | -0.00523 |
| ridge | 0.06836 | 0.09849 | 0.0182 | -0.01134 |

The ML point model changes MAE by -12.20% versus the canonical
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
