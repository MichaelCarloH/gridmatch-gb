# Phase 8 — Renewable Matching Engine

## Goal

Allocate renewable generation to business demand for each settlement period.

This is a commercial/accounting allocation, not a physical electron-flow model.

## Inputs

Per period:

- generator available MWh;
- consumer demand MWh;
- optional contractual preference;
- generator price;
- consumer preference;
- geographic distance;
- technology preference.

## Constraints

For every generator:

```math
\sum_c x_{g,c,t} \le generation_{g,t}
```

For every consumer:

```math
\sum_g x_{g,c,t} \le demand_{c,t}
```

And:

```math
x_{g,c,t} \ge 0
```

## Objective

P0:

- maximise matched renewable MWh.

P1:

- maximise renewable matching;
- minimise distance;
- prefer contractual pairs;
- prefer lower cost;
- preserve fairness.

## Implementation

Preferred:

- linear programming with SciPy.

Fallback:

- deterministic greedy allocation.

## Outputs

- matched MWh;
- residual business demand;
- unmatched renewable generation;
- consumer renewable coverage;
- generator offtake coverage;
- portfolio renewable match rate;
- allocation matrix;
- average matching distance;
- weighted matched price.

## Map arcs

For the frontend:

- generator coordinate;
- consumer coordinate;
- matched MWh;
- settlement period;
- technology;
- distance;
- allocation score.

## Conservation tests

```text
matched <= generation
matched <= demand
matched >= 0
residual_demand = demand - matched
spill = generation - matched
```

## Required artifacts

```text
artifacts/matching/allocations.parquet
artifacts/matching/summary.json
```

## Acceptance criteria

- every settlement period can be solved;
- allocation is deterministic;
- conservation holds;
- map-ready arcs exist;
- summary metrics exist;
- commercial-versus-physical interpretation is documented.

## Codex execution prompt

```text
Implement Phase 8 from 08_RENEWABLE_MATCHING.md. Build a deterministic LP or greedy allocator, export allocations and map arcs, write conservation tests, and document that the output represents commercial matching rather than physical electricity flow.
```
