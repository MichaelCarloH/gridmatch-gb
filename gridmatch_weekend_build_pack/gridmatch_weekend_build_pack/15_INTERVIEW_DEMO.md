# Phase 15 — Interview Demo and Talking Points

## 90-second demo

### 0–15 seconds

Open the dashboard.

Say:

> I interpreted the problem as forecasting uncertain business demand and renewable generation at site level, aggregating the portfolio, and converting the resulting distribution into an operational hedge decision.

### 15–30 seconds

Show demand, generation, net position and uncertainty.

Say:

> Each modelled site has a baseline, an interpretable statistical model and quantile ML models. I use rolling-origin validation and record forecast issue time to avoid leakage.

### 30–45 seconds

Open the map and a site.

Say:

> Public generator metadata and output are separated from simulated commercial meter data. Each site has its own model card, forecast history and data-quality report.

### 45–60 seconds

Show renewable matching.

Say:

> The matching engine allocates renewable generation to business demand for every half-hour while preserving generation and demand constraints. The map lines represent commercial allocation, not physical electron flow.

### 60–75 seconds

Show hedge page.

Say:

> The portfolio model produces a distribution, not just a point estimate. The hedge engine selects a quantile based on the relative cost of being short or long and compares that policy historically.

### 75–90 seconds

Show Research.

Say:

> I kept the project research-driven. The notebooks cover the market, data lineage, site forecasting, portfolio reconciliation, matching and hedge validation, while the deployed product uses reusable package modules and saved artifacts.

## Likely questions

### Why per-site models?

- different physical and behavioural drivers;
- site reporting;
- anomaly detection;
- bottom-up explanations.

### Why also a direct portfolio model?

- aggregation changes noise;
- directly targets the commercial decision;
- site-level optimality may not imply portfolio optimality.

### Why quantile forecasts?

- the hedge decision depends on uncertainty and asymmetric costs.

### Why LightGBM?

- structured tabular features;
- nonlinear interactions;
- fast training;
- interpretability;
- operational simplicity.

### How did you prevent leakage?

- rolling validation;
- issue-time weather;
- lag cutoff;
- training cutoff;
- no random split.

### What is simulated?

- commercial meter data;
- contracts;
- matching relationships;
- exact supplier cost model;
- fault events.

### What would change with real Volter data?

- meter ingestion;
- contract constraints;
- true market execution prices;
- customer-specific tariffs;
- portfolio membership;
- live reforecasting;
- production monitoring.

### What would you build next?

- actual smart-meter connectors;
- historical forecast archive;
- calibrated joint portfolio distribution;
- intraday reforecasting;
- battery/flex optimisation;
- production model monitoring.
