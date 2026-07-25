# Phase 11 — Volter-Inspired Product Frontend

## Goal

Present the research and models as an operational clean-energy product.

Do not copy Volter’s logo, proprietary assets or exact pages. Use a related clean-energy visual language.

## Design system

```css
--paper: #F1F2EF;
--surface: #FFFFFF;
--ink: #0E121A;
--muted: #737B83;
--line: rgba(14, 18, 26, 0.12);
--green: #4CA855;
--green-soft: #E1F1DE;
--blue: #2F73D9;
--blue-soft: #E5EEFB;
--amber: #D99A2B;
--red: #C95A50;
--navy: #0E121A;
```

Use:

- large typography;
- generous whitespace;
- rounded cards;
- green generation charts;
- blue demand charts;
- dark analytical panels;
- restrained borders and shadows.

## Landing page

Headline:

> Forecast, match and optimise clean power across Great Britain.

Show:

- demand forecasting;
- renewable generation;
- matching;
- hedge intelligence;
- asset monitoring;
- research credibility.

## Dashboard

KPIs:

- tomorrow demand;
- renewable generation;
- net position;
- recommended hedge;
- renewable match rate;
- forecast uncertainty;
- expected imbalance cost;
- alerts.

Main chart:

- demand;
- generation;
- net position;
- q10–q90;
- hedge.

## GB map

Show:

- operational REPD sites;
- selected modelled public generators;
- simulated business sites;
- active matching arcs.

Filters:

- technology;
- role;
- region;
- capacity;
- data origin;
- alert state.

## Sites page

Table:

- name;
- role;
- technology;
- location;
- capacity;
- latest forecast;
- MAE;
- quality score;
- status.

## Site detail

Tabs:

- overview;
- forecast;
- actuals;
- weather;
- anomalies;
- model;
- quality;
- financial/ESG.

## Forecast Lab

Show:

- baseline;
- statistical;
- ML;
- quantile calibration;
- error by settlement period;
- feature importance;
- rolling backtests.

## Matching page

Show:

- matched MWh;
- renewable coverage;
- spill;
- residual grid import;
- allocation matrix;
- map arcs;
- period slider.

## Market page

Show:

- price references;
- forecast distribution;
- recommended quantile;
- hedge volume;
- cost comparisons;
- interactive assumptions.

## Research page

Show:

- notebook status;
- research summaries;
- model cards;
- data lineage;
- public versus simulated data;
- limitations.

## Reports page

Show:

- procurement;
- renewable match;
- generator revenue;
- emissions;
- forecast performance;
- alerts.

## Acceptance criteria

- no placeholder pages;
- all P0 pages use real artifacts;
- mobile layout is usable;
- charts include units;
- loading, error and empty states exist;
- production build succeeds;
- data origin is visible;
- design is coherent.

## Codex execution prompt

```text
Implement Phase 11 from 11_FRONTEND_PRODUCT.md. Build all P0 Next.js routes and reusable components, connect them to API or exported artifacts, apply the clean-energy design system, and run the production build. Remove placeholders and fix all runtime and type errors.
```
