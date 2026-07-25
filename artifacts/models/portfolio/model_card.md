# Portfolio forecast model card

## Purpose

Translate the 12 simulated site forecasts into aggregate demand, aggregate
generation and the operator's net position (`demand - generation`).

## Methods

- **Baseline:** aggregate the canonical site baselines.
- **Bottom-up:** exactly sum site point forecasts.
- **Bottom-up intervals:** 600 split-normal site simulations coupled by a
  one-factor Gaussian approximation with correlation `0.35`.
- **Direct:** HistGradientBoosting point/q10/q50/q90 models trained on aggregate
  weather, calendar, lag and site-composition features.
- **Reconciled:** direct and bottom-up forecasts blended using weights selected
  only from earlier rolling-origin validation evidence.

Final-fold reconciliation weights:

- demand: direct `0.30`, bottom-up `0.70`
- generation: direct `0.01`, bottom-up `0.99`
- net: direct `0.03`, bottom-up `0.97`

## Rolling-origin evidence

| Target | Method | MAE (MWh) | RMSE (MWh) | Bias (MWh) | Coverage |
|---|---|---:|---:|---:|---:|
| demand | baseline | 0.1126 | 0.1372 | 0.0911 | n/a |
| demand | bottom_up | 0.0878 | 0.1114 | 0.0268 | 0.764 |
| demand | direct | 0.0928 | 0.1163 | 0.0228 | 0.786 |
| demand | reconciled | 0.0878 | 0.1111 | 0.0248 | 0.797 |
| generation | baseline | 0.0585 | 0.0742 | -0.0033 | n/a |
| generation | bottom_up | 0.0683 | 0.0864 | -0.0172 | 0.893 |
| generation | direct | 0.1847 | 0.2729 | -0.0287 | 0.824 |
| generation | reconciled | 0.0890 | 0.1284 | -0.0195 | 0.931 |
| net | baseline | 0.1278 | 0.1599 | 0.0944 | n/a |
| net | bottom_up | 0.1113 | 0.1449 | 0.0440 | 0.701 |
| net | direct | 0.2349 | 0.3295 | 0.0872 | 0.799 |
| net | reconciled | 0.1356 | 0.1834 | 0.0678 | 0.768 |

The simulated hedge-cost column is a transparent diagnostic proxy:
absolute forecast error multiplied by £75/MWh. It is
not a Phase 9 hedge strategy or a claim about realised imbalance prices.

## Limitations

Site data and weather are simulated, weather is not a forecast-vintage archive,
and only two seven-day rolling folds are available. The Gaussian correlation
factor is a documented approximation, not a calibrated production copula.
Quantile blending is an approximation and should be recalibrated with longer
permissioned histories.

## Production recommendations

Archive issue-time weather vintages, estimate changing cross-site error
dependence, expand rolling seasons, monitor interval calibration and determine
reconciliation weights under an approved commercial loss function.
