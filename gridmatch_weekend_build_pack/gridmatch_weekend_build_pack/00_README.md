# GridMatch GB — Weekend Build Pack

## Objective

Build a credible research-to-production prototype for Great Britain energy forecasting, renewable matching, asset intelligence and portfolio hedging.

The project should resemble the working style of a quantitative research platform such as Mosaic:

```text
research question
→ reproducible data
→ notebooks
→ reusable Python modules
→ model artifacts
→ validation
→ APIs
→ deployed product
→ documented decisions
```

The final product should not be a static dashboard. Every visible KPI should trace back to a generated dataset, model artifact or calculation.

## Final deliverables

By the end of the weekend, the repository should contain:

- a reproducible Python package;
- public-data ingestion modules;
- deterministic synthetic business-site data;
- individual site models;
- probabilistic forecasts;
- portfolio aggregation and reconciliation;
- renewable matching;
- a hedge simulator;
- a FastAPI backend;
- a Next.js frontend;
- a Great Britain site map;
- executed research notebooks;
- model cards;
- tests;
- a live deployment;
- a short demo script.

## Build order

Complete these files in order:

1. `01_PRODUCT_SCOPE.md`
2. `02_REPOSITORY_STRUCTURE.md`
3. `03_DATA_COLLECTION.md`
4. `04_DATA_MODEL_AND_VALIDATION.md`
5. `05_RESEARCH_NOTEBOOKS.md`
6. `06_SITE_LEVEL_MODELS.md`
7. `07_PORTFOLIO_MODELS.md`
8. `08_RENEWABLE_MATCHING.md`
9. `09_HEDGE_ENGINE.md`
10. `10_API_AND_MODEL_SERVING.md`
11. `11_FRONTEND_PRODUCT.md`
12. `12_TESTING_AND_QA.md`
13. `13_DEPLOYMENT.md`
14. `14_WEEKEND_EXECUTION_PLAN.md`
15. `15_INTERVIEW_DEMO.md`
16. `16_CODEX_EXECUTION_PROTOCOL.md`

## Core product flow

```text
Site onboarding
→ meter and market data
→ data-quality checks
→ weather enrichment
→ site-level forecasts
→ portfolio forecast
→ renewable allocation
→ hedge recommendation
→ asset alerts
→ financial and ESG reporting
```

## Non-negotiable rules

- Public, simulated and uploaded data must be labelled separately.
- No random train/test split for time series.
- All heavy research code belongs in reusable Python modules, not only notebooks.
- Every model must beat or be compared with a simple baseline.
- Every forecast must record its issue time and valid time.
- Store timestamps in UTC and display in `Europe/London`.
- Handle 46, 48 and 50 settlement-period days.
- Do not fabricate performance metrics.
- Do not claim the prototype reproduces Volter’s private systems or supplier contracts.
- Do not deploy model training inside a web request.
