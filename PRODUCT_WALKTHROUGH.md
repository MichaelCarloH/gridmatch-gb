# Product walkthrough

## Business customer

`/business` answers five questions quickly: how much electricity is expected,
how much is commercially matched to renewables, how much remains on the grid,
what the saved price scenario implies, and what requires attention. Site pages
add load shape, P10/P50/P90, anomalies, data quality and archetype context.
`/business/energy-plan` turns the same artifacts into client language, with
technical quantile and hedge detail under “How calculated.”

## Renewable generator

`/generator` explains actual and forecast output, offtake coverage, unmatched
generation, performance and scenario value. Output, offtake, revenue and asset
views retain separate boundaries. Revenue is reference-price arithmetic, never
an invoice or contract claim.

## Portfolio operations

`/operations/portfolio` shows demand, generation, matched MWh, residual,
contracted-volume proxy, adjustment and realised outcome by settlement period.
Risk exposes short/long volume, cost, p95, CVaR95, bias and error contribution.
Scenario controls are bounded and deterministic; they never retrain or trade.

## Diversification

The lab uses saved error correlations and attribution with deterministic HHI,
stress and hypothetical-site approximations. Every stress has a stable ID and
fixed factors, making results reproducible.

## Model operations

The models workspace explains the hierarchy from site models to reconciled
portfolio output. It compares metrics, states aggregate calibration limits,
links registry IDs to intended use and limitations, and derives visible
incidents without claiming a live MLOps platform.

## Administration

Customer and generator forms produce non-persistent previews. Contracts are
visibly simulated. Upload validation calls the Phase 4 API validator in local
technical mode and uses a bounded browser schema mirror in static mode. Both
preserve annotated preview rows and disable storage.

## Research and explainability

Executed notebooks, model cards and source lineage remain under `/research`.
“How calculated” expands from a metric-specific source and formula into the
full meter → validation → weather → forecast → aggregation → allocation →
residual → recommendation → reconciliation → report chain.
