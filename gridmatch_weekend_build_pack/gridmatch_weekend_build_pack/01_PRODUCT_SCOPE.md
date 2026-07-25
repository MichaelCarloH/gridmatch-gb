# Phase 1 — Product Scope and Acceptance Criteria

## Product thesis

GridMatch GB is a clean-energy operating prototype for commercial electricity portfolios.

It should answer five questions:

1. What will each business site consume tomorrow?
2. What will each renewable site generate tomorrow?
3. What is the portfolio’s net electricity position?
4. How much renewable output can be matched to business demand?
5. How much should be hedged given forecast uncertainty and imbalance costs?

## User personas

### Portfolio operator

Needs:

- tomorrow’s demand and generation;
- uncertainty;
- net position;
- recommended hedge;
- active data and asset alerts.

### Energy analyst

Needs:

- model comparisons;
- backtests;
- forecast errors;
- site-level drivers;
- model versions;
- research notebooks.

### Renewable asset owner

Needs:

- actual versus expected generation;
- underperformance;
- lost generation;
- revenue benchmark;
- matched offtake.

### Business customer

Needs:

- consumption history;
- forecast;
- renewable coverage;
- residual grid usage;
- cost and carbon summary.

## Mandatory pages

- Landing page
- Portfolio dashboard
- GB site map
- Site list
- Site detail
- Forecast lab
- Renewable matching
- Market and hedge
- Asset intelligence
- Research
- Reports

## Mandatory backend capabilities

- list sites;
- read site observations;
- read site forecasts;
- read site metrics;
- read portfolio forecasts;
- calculate matching;
- simulate hedge decisions;
- validate uploaded meter data;
- expose model registry.

## P0 acceptance criteria

The project is not complete until:

- at least 10 sites exist;
- at least 3 site types exist;
- at least 180 days of half-hourly data exist;
- every modelled site has a baseline and ML forecast;
- q10, q50 and q90 forecasts exist;
- portfolio forecasts exist;
- renewable matching conserves demand and generation;
- the hedge simulator produces an actionable volume;
- the API returns real artifact-backed data;
- the frontend consumes the API or exported artifacts;
- the production build succeeds;
- notebooks execute;
- tests pass;
- the deployment is accessible.

## Cut list

Do not spend weekend time on:

- authentication;
- billing;
- user permissions;
- live trading;
- contract execution;
- chatbots;
- mobile apps;
- LSTMs or transformers;
- complex battery optimisation;
- live retraining;
- a complete BSC settlement engine.
