# Progress

## Current phase

Phase 7 — Portfolio forecasting and reconciliation: complete.

## Preserved work and scope

- Phase 3 data pipelines, Phase 4 settlement/quality validation, Phase 5 notebooks and Phase 6 site models remain operational.
- The deterministic demo still contains 103,680 observations, 5,086 retained quality flags and 12 ready sites with scores from 95.55 to 99.84.
- Explicit simulated regions were added to site metadata for error attribution without advancing the seeded observation generator.
- `legacy-prototype/` remains archived and unchanged.
- No renewable matching, hedge policy, API route, frontend product page or Phase 8 work was started.

## Completed Phase 7 implementation

- `src/gridmatch/features/portfolio.py`: aggregate demand, generation and net-position targets plus issue-safe weather, calendar, lag and site-composition features.
- `src/gridmatch/portfolio/simulation.py`: deterministic split-normal site simulations with a one-factor Gaussian dependence approximation.
- `src/gridmatch/portfolio/metrics.py`: MAE, RMSE, nMAE, bias, peak error, probabilistic metrics and a transparent fixed-price hedge-cost proxy.
- `src/gridmatch/portfolio/training.py`: exact bottom-up aggregation, direct models, prior-fold reconciliation weights, metrics, error attribution, figures and model artifacts.
- `scripts/build_portfolio_forecast.py`: builds every Phase 7 output outside the web request path.
- `tests/python/test_portfolio_models.py`: six tests for feature timing, simulation, aggregation equality, direct-model loading, reconciliation, intervals, metrics and attribution.

## Portfolio methodology

- Definitions:
  - demand is the sum of eight demand sites;
  - generation is the sum of four renewable sites;
  - net position is demand minus generation;
  - positive net position means electricity must be procured.
- Bottom-up point forecasts exactly sum Phase 6 site forecasts.
- Bottom-up q10/q50/q90 intervals use 600 deterministic simulations per period, split-normal site marginals and a documented 0.35 common correlation factor.
- Direct HistGradientBoosting point/q10/q50/q90 models are trained separately for aggregate demand, generation and net position.
- Reconciled forecasts blend direct and bottom-up values. Fold 1 uses a documented 50/50 default; fold 2 weights are selected only from fold 1 MAE.
- Final-fold direct weights are 0.30 for demand, 0.01 for generation and 0.03 for net position.
- Validation uses the same two leakage-safe rolling-origin windows as Phase 6; training stops no later than the earliest forecast issue time.

## Generated Phase 7 artifacts

Forecasts and metrics:

- `artifacts/forecasts/portfolio_forecasts.parquet` — 626 dashboard-ready out-of-sample periods with actual, baseline, bottom-up, direct and reconciled forecasts.
- `artifacts/metrics/portfolio_metrics.json`
- `artifacts/metrics/portfolio_metrics.parquet`
- `artifacts/metrics/portfolio_metrics_by_fold.parquet`
- `artifacts/metrics/site_error_contributions.parquet`
- `artifacts/metrics/technology_error_contributions.parquet`
- `artifacts/metrics/region_error_contributions.parquet`
- `artifacts/metrics/site_error_correlation.parquet`

Direct portfolio model artifacts:

- `artifacts/models/portfolio/demand/`
- `artifacts/models/portfolio/generation/`
- `artifacts/models/portfolio/net/`
- `artifacts/models/portfolio/model_card.md`

Figures:

- `artifacts/figures/portfolio_comparison.png`
- `artifacts/figures/portfolio_error_correlation_heatmap.png`

## Observed Phase 7 evidence

- Best demand MAE: reconciled, approximately 0.0878 MWh.
- Best generation MAE: aggregate physics-informed baseline, approximately 0.0585 MWh.
- Best net-position MAE: bottom-up, approximately 0.1113 MWh.
- Reconciliation appropriately places 97–99% weight on bottom-up renewable/net forecasts after prior-fold validation.
- Bottom-up actual and point totals equal the underlying site aggregation.
- Every bottom-up, direct and reconciled interval satisfies q10 ≤ q50 ≤ q90.
- All 626 rows satisfy `training_cutoff_utc <= issue_time_utc < valid_time_utc`.
- Site, technology and regional contributions are exported, and the 12×12 error-correlation matrix is visualised.

## Phase 7 P0 acceptance audit

- Bottom-up demand, generation and net forecasts exist: passed.
- Bottom-up point totals exactly equal site aggregation: passed and computed, not assumed.
- Portfolio intervals use a documented correlated simulation rather than summed quantiles: passed.
- Direct demand, generation and net models exist and load: passed.
- Reconciled forecasts and validation-selected weights exist: passed.
- Baseline, bottom-up, direct and reconciled metrics include MAE, RMSE, bias, peak error, pinball loss, coverage and simulated hedge cost: passed.
- Site, technology and region error contributions exist: passed.
- Correlated forecast-error heatmap exists: passed.
- Dashboard-ready forecast output exists: passed.
- No Phase 7 P0 gaps remain.

## Verification evidence

- `.\.venv\Scripts\python.exe scripts\build_demo_dataset.py`: passed; regions added while prior observation and quality evidence remained unchanged.
- `.\.venv\Scripts\python.exe scripts\build_portfolio_forecast.py`: passed; 626 periods, two folds, 600 simulations per period and all required artifacts generated.
- `.\.venv\Scripts\python.exe scripts\execute_notebooks.py`: passed; all four Phase 5 notebooks still execute.
- `.\.venv\Scripts\python.exe -m pytest`: 49 passed without warnings.
- `cmd /c npm run build`: passed; Next.js compiled, type-checked and generated four static pages.
- Visual audit: comparison and correlation figures render legibly and support the recorded findings.

## Known prototype limitations

- Site, meter and weather inputs are simulated; results are pipeline evidence rather than production performance claims.
- The 0.35 dependence factor is a documented approximation, not a calibrated production copula.
- Quantile reconciliation is an approximation and requires longer calibration histories.
- The simulated hedge-cost metric is absolute error multiplied by £75/MWh; it is not a Phase 9 hedge strategy or realised imbalance-cost estimate.
- Direct generation and net models currently trail stronger bottom-up/physics approaches and should not replace them.

## Next

Proceed to Phase 8 (`08_RENEWABLE_MATCHING.md`) only when explicitly requested.
