# Phase 12 — Testing and Quality Assurance

## Goal

Make the project trustworthy enough to demonstrate live.

## Python tests

Required:

- settlement period conversion;
- spring DST;
- autumn DST;
- data schema validation;
- upload validation;
- deterministic simulation;
- feature generation;
- model prediction shape;
- q10 <= q50 <= q90;
- physical forecast limits;
- portfolio aggregation;
- reconciliation;
- matching conservation;
- hedge calculation;
- API health;
- API site response.

## Frontend checks

Required:

- lint;
- TypeScript compile;
- production build;
- route rendering;
- no console errors;
- responsive layout;
- empty state;
- error state;
- invalid site;
- failed API response.

## Data invariants

```text
portfolio demand = sum site demand
portfolio generation = sum site generation
net position = demand - generation
matched <= generation
matched <= demand
spill >= 0
residual demand >= 0
q10 <= q50 <= q90
solar <= capacity
wind <= capacity
```

## Manual demo checklist

- landing loads;
- dashboard loads;
- map markers render;
- site drawer opens;
- site detail opens;
- forecast chart loads;
- matching period changes;
- hedge assumptions change output;
- research page displays notebooks;
- reports page prints cleanly.

## Acceptance criteria

- all automated tests pass;
- frontend build passes;
- no fabricated values;
- no broken links;
- no visible placeholder copy;
- no credentials required for demo;
- cached fallback works without internet.

## Codex execution prompt

```text
Execute Phase 12 from 12_TESTING_AND_QA.md. Add missing tests, run the full suite, run the frontend production build, inspect all routes, fix every failing invariant and remove all placeholders. Update PROGRESS.md with evidence.
```
