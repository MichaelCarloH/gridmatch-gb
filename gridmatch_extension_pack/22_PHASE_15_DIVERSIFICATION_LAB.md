# Phase 15 — Diversification and Portfolio Construction Lab

## Goal

Evaluate customers and generators as parts of a portfolio rather than only as individual contracts.

## Routes

```text
/operations/diversification
/operations/concentration
/operations/stress-tests
/operations/portfolio-addition
```

## Required analytics

### Error correlation

Use existing error-correlation artifacts to show site, region and technology clusters.

### Risk contribution

For each site estimate:

- contribution to portfolio error;
- contribution to variance;
- contribution to shortfall risk;
- diversification benefit.

### Concentration

Show largest share, top-five share and HHI by customer, generator, region, technology and archetype.

### Stress tests

- largest generator outage;
- low-wind Scotland;
- widespread cloud;
- cold-demand shock;
- supermarket demand spike;
- delayed meter;
- missing weather;
- high-price scenario.

### Portfolio addition

Add deterministic hypothetical sites without retraining:

- office;
- supermarket;
- solar;
- wind.

Show effect on renewable coverage, residual demand, uncertainty, concentration, matching and scenario cost.

## Acceptance

All results use existing artifacts or documented deterministic approximations. No retraining in requests. Stress tests are reproducible. Tests and build pass.

## Execution prompt

```text
Read 22_PHASE_15_DIVERSIFICATION_LAB.md and PROGRESS.md. Implement only diversification, concentration, stress-test and portfolio-addition tools. Reuse current artifacts and do not retrain models in requests. Run tests and npm run build, update PROGRESS.md, and stop before Phase 16.
```
