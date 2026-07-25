# Progress

## Current phase

Phase 6 — Individual site-level forecasting models: complete.

## Preserved work and scope

- Phase 3 public and simulated pipelines, Phase 4 settlement/quality validation, and Phase 5 notebooks remain operational.
- The additional simulated wind-direction, gust and pressure fields do not advance the original seeded random generator; the prior 103,680 observations, 5,086 flags, 12 ready sites and 95.55–99.84 score range are preserved.
- `legacy-prototype/` remains archived and unchanged.
- No portfolio forecasting, reconciliation, renewable matching, hedge modelling, API routes or frontend product pages were started.

## Completed Phase 6 implementation

- `src/gridmatch/features/site.py`: 41 leakage-aware calendar, bank-holiday, weather, lag, rolling, physical and site-metadata features.
- `src/gridmatch/models/baselines.py`: previous-day, previous-week, rolling same-period, generation persistence, physical solar and stylised wind baselines.
- `src/gridmatch/models/site_forecasting.py`: Ridge statistical model and HistGradientBoosting point/q10/q50/q90 models with quantile repair and physical post-processing.
- `src/gridmatch/models/metrics.py`: MAE, RMSE, nMAE, bias, pinball loss, interval coverage and interval width.
- `src/gridmatch/models/training.py`: two-fold expanding rolling-origin training, artifact persistence, model cards, global fallbacks and strict JSON summaries.
- `scripts/train_site_models.py`: trains all 12 demo sites and three global fallback stacks outside the web request path.
- `tests/python/test_site_models.py`: seven tests covering issue-time safety, rolling splits, required baselines, model loading, quantiles, physical constraints, artifacts, metrics and improvement.
- `pyproject.toml` and `uv.lock`: reproducible scikit-learn, joblib and UK-bank-holiday dependencies managed with `uv`.

## Feature and validation design

- Target: simulated half-hourly demand or generation energy in MWh.
- Forecast issue convention: exactly 48 half-hour periods before each valid time.
- Every stored forecast has issue time, valid time, horizon, settlement date/period, training cutoff, model version and feature version.
- Each rolling fold stops training no later than the earliest forecast issue time in that fold.
- Validation uses two expanding seven-day folds and never uses a random split.
- Weather is treated as a forecast-weather methodology proxy; current simulated realised weather is explicitly disclosed as a limitation.

## Generated Phase 6 artifacts

Per-site artifacts under `artifacts/models/{site_id}/` for all 12 sites:

- `baseline.json`
- `statistical.joblib`
- `point.joblib`
- `q10.joblib`
- `q50.joblib`
- `q90.joblib`
- `metadata.json`
- `model_card.md`

Global fallbacks:

- `artifacts/models/global_demand/`
- `artifacts/models/global_solar/`
- `artifacts/models/global_wind/`

Forecast and metric artifacts:

- `artifacts/forecasts/site_forecasts.parquet` — 7,512 out-of-sample forecast rows across 12 sites and two folds.
- `artifacts/metrics/site_metrics_by_fold.parquet` — fold-level evidence.
- `artifacts/metrics/site_metrics.parquet` — 68 aggregate site/model comparison rows.
- `artifacts/metrics/site_metrics.json` — strict JSON summary and per-site baseline comparison.

## Observed Phase 6 evidence

- All 12 sites have forecasts, a statistical model, point and q10/q50/q90 models, baseline evidence, metadata and a model card.
- All stored estimators load and expose `predict`.
- All 7,512 forecast rows satisfy `training_cutoff_utc <= issue_time_utc < valid_time_utc`.
- All quantiles satisfy `q10 <= q50 <= q90`.
- Forecast energy is non-negative; solar is zero at night; generation never exceeds installed capacity for a half-hour.
- HistGradientBoosting improves the canonical rolling same-period baseline on all eight demand sites.
- The physical solar and wind baselines remain slightly stronger than ML on the four renewable sites; this is retained as an honest result rather than hidden.
- Probabilistic interval coverage across site ML models ranges from approximately 76.7% to 94.1%.

## Phase 6 P0 acceptance audit

- Every selected site has day-ahead point/q10/q50/q90 forecasts: passed.
- Previous-day, previous-week, rolling same-period, persistence, physical solar and wind baselines are implemented where applicable: passed.
- Ridge statistical and HistGradientBoosting ML models are trained per site: passed.
- Demand, solar and wind feature requirements, including lags, rolling values, weather and metadata, are represented: passed.
- Global demand, solar and wind fallback stacks are saved: passed.
- Rolling-origin evaluation, versioned timing fields and all required metrics are stored: passed.
- Per-site model artifacts load: passed.
- Quantile ordering and physical constraints hold: passed.
- At least one model improves on its canonical baseline; eight sites improve: passed.
- Model cards disclose simulated data, realised-weather proxy use and production limitations: passed.
- No Phase 6 P0 gaps remain.

## Verification evidence

- `py -3 -m uv lock`: passed; reproducible lockfile created.
- `py -3 -m uv sync --extra dev`: passed; Phase 6 dependencies installed in `.venv`.
- `.\.venv\Scripts\python.exe scripts\build_demo_dataset.py`: passed; preserved Phase 3/4 evidence and added deterministic weather fields.
- `.\.venv\Scripts\python.exe scripts\train_site_models.py`: passed; 12 site stacks, three fallbacks and all forecast/metric artifacts generated.
- `.\.venv\Scripts\python.exe scripts\execute_notebooks.py`: passed; all four Phase 5 notebooks still execute.
- `.\.venv\Scripts\python.exe -m pytest`: 43 passed without warnings.
- `cmd /c npm run build`: passed; Next.js compiled, type-checked and generated four static pages.

## Known prototype limitations

- Site and meter data are simulated; metrics are not production-performance claims.
- Weather inputs are simulated realised values, not archived forecast vintages.
- The 180-day history and two validation folds are sufficient for prototype evidence, not seasonal production approval.
- Renewable physics baselines outperform ML in current validation; model complexity should not replace them without stronger evidence.
- Forecasts do not yet include portfolio reconciliation, matching or hedge decisions.

## Next

Proceed to Phase 7 (`07_PORTFOLIO_MODELS.md`) only when explicitly requested.
