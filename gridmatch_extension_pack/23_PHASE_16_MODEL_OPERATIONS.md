# Phase 16 — Forecasting and Model Operations

## Goal

Build the workspace used by Luke and the data-science team to monitor forecast and model risk.

## Routes

```text
/models
/models/performance
/models/calibration
/models/registry
/models/incidents
/models/data-drift
```

## Performance

Show baseline, production and challenger metrics:

- MAE;
- RMSE;
- bias;
- pinball loss;
- coverage;
- interval width;
- horizon;
- settlement period;
- site;
- weather regime.

## Hierarchy

Explain:

```text
Site model
Global fallback
Bottom-up portfolio model
Direct portfolio model
Reconciled model
```

Show why the selected forecast is preferred.

## Calibration

Show empirical q10/q50/q90 reliability and interval coverage.

## Drift and incidents

Detect and display:

- load-profile drift;
- weather-response drift;
- data-quality deterioration;
- model performance decline;
- missing artifact;
- quantile crossing;
- physical-limit violation;
- challenger outperformance;
- persistent residual bias.

## Registry

Link model IDs to windows, features, metrics, intended use and limitations.

## Acceptance

Model selection, calibration and incidents are understandable and traceable. No fabricated production status. No retraining. Tests and build pass.

## Execution prompt

```text
Read 23_PHASE_16_MODEL_OPERATIONS.md and PROGRESS.md. Implement only the Model Operations workspace using current metrics, registry and quality artifacts. Do not retrain. Run tests and npm run build, update PROGRESS.md, and stop before Phase 17.
```
