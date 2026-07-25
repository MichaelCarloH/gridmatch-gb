# Phase 14 — Portfolio and Risk Control Room

## Goal

Build the internal workspace for Volter, a portfolio operator or licensed utility partner.

## Routes

```text
/operations
/operations/portfolio
/operations/forecasts
/operations/matching
/operations/risk
/operations/scenarios
```

## Portfolio position

For each settlement period show:

- total demand;
- renewable generation;
- matched renewable volume;
- residual requirement;
- current contracted volume;
- recommended adjustment;
- q10/q50/q90;
- realised result.

## Planned versus realised

Attribute deviations to:

- demand error;
- solar error;
- wind error;
- matching deviation;
- price exposure.

## Risk

Show:

- expected short/long volume;
- scenario cost;
- p95 and CVaR95;
- worst periods;
- bias;
- concentration;
- data/model incidents.

## Scenarios

Bounded controls:

- short-cost multiplier;
- long-value multiplier;
- forecast method;
- generator outage;
- customer demand shock;
- low-wind stress;
- solar shortfall;
- missing-data degradation.

No model retraining and no trade execution.

## Acceptance

The operator sees the complete half-hourly position, uncertainty, recommended adjustment and risk drivers. Planned and realised states remain separate. Tests and build pass.

## Execution prompt

```text
Read 21_PHASE_14_OPERATIONS_CONTROL_ROOM.md and PROGRESS.md. Implement only the Operations workspace using Phase 7–10 artifacts and lightweight scenario functions. Do not add live trading or alter model outputs. Run tests and npm run build, update PROGRESS.md, and stop before Phase 15.
```
