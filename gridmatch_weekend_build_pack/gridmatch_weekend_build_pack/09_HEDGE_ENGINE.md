# Phase 9 — Market and Hedge Decision Engine

## Goal

Convert a forecast distribution into a day-ahead procurement decision.

## Inputs

- portfolio q10/q50/q90 or sampled distribution;
- market reference price;
- system imbalance price;
- short-cost assumption;
- long-cost assumption;
- risk preference;
- realised net demand for historical backtests.

## Prototype cost model

```math
Cost_t
=
H_t P^{ref}_t
+
ImbalanceCost(Y_t - H_t)
```

Where:

- `H_t` is hedged volume;
- `Y_t` is realised net demand;
- `P_ref` is a public market-price reference;
- imbalance is settled using a documented simplified rule.

State clearly that this is not a full licensed-supplier settlement engine.

## Hedge policies

Compare:

- no hedge;
- q50;
- q60;
- q70;
- q80;
- validation-optimised quantile;
- perfect foresight.

## Asymmetric cost logic

When short and long errors have different costs:

```math
H^*_t = Q_\tau(Y_t)
```

The selected quantile depends on the cost ratio.

## Outputs

- recommended quantile;
- recommended MWh;
- expected short exposure;
- expected long exposure;
- historical total cost;
- cost versus baseline;
- risk distribution;
- sensitivity to cost assumptions.

## Interactive controls

Frontend inputs:

- short-cost multiplier;
- long-cost multiplier;
- risk preference;
- forecast model;
- date;
- settlement period.

## Required artifacts

```text
artifacts/metrics/hedge_backtest.json
artifacts/forecasts/hedge_recommendations.parquet
```

## Acceptance criteria

- every portfolio forecast period has a recommendation;
- at least five hedge policies are compared;
- cost assumptions are visible;
- perfect foresight is only a lower-bound benchmark;
- historical backtest is leakage-aware;
- the API can recompute a scenario quickly.

## Codex execution prompt

```text
Implement Phase 9 from 09_HEDGE_ENGINE.md. Build the prototype cost model, compare hedge policies, optimise a validation quantile, export recommendations, and expose a lightweight scenario function for the API. Add explicit limitations.
```
