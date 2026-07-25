# Phase 5 — Research Notebook Framework

## Goal

Create research evidence without turning notebooks into the production codebase.

## Rules

Every notebook must:

- import project modules;
- use deterministic seeds;
- load cached data;
- display business context;
- save figures and tables;
- end with findings and limitations;
- execute top to bottom;
- avoid hidden manual steps.

## Required notebooks

### `00_gb_market_and_settlement.ipynb`

Cover:

- market participants;
- half-hourly settlement;
- 46/48/50 periods;
- forecasting and imbalance;
- public datasets;
- prototype boundaries.

### `01_site_map_and_public_assets.ipynb`

Cover:

- REPD ingestion;
- operational assets;
- technology and capacity;
- map output;
- public-data limitations.

### `02_data_quality_and_site_profiles.ipynb`

Cover:

- synthetic business archetypes;
- public generator coverage;
- missingness;
- anomalies;
- site-level load shapes.

### `03_weather_features.ipynb`

Cover:

- historical forecasts;
- issue versus valid time;
- solar features;
- wind features;
- demand features;
- leakage risks.

### `04_site_forecasting.ipynb`

Cover:

- seasonal baselines;
- statistical model;
- gradient boosting;
- quantile forecasts;
- rolling validation;
- calibration.

### `05_portfolio_forecasting.ipynb`

Cover:

- bottom-up;
- direct;
- reconciliation;
- diversification;
- portfolio intervals.

### `06_renewable_matching.ipynb`

Cover:

- allocation constraints;
- matching score;
- residual demand;
- renewable spill;
- coverage.

### `07_hedge_backtest.ipynb`

Cover:

- price data;
- cost assumptions;
- hedge policies;
- quantile selection;
- sensitivity.

### `08_asset_anomalies.ipynb`

Cover:

- expected versus actual;
- residuals;
- outage detection;
- lost MWh;
- lost revenue.

## Notebook execution

Create:

```bash
python scripts/execute_notebooks.py
```

The script should:

- execute notebooks;
- fail on errors;
- save executed copies;
- write a JSON notebook index;
- capture run time and status.

## Research page integration

Export:

```json
{
  "name": "04_site_forecasting",
  "status": "executed",
  "summary": "...",
  "key_result": "...",
  "artifact_links": []
}
```

## Acceptance criteria

- at least 4 notebooks are complete before frontend polish;
- all P0 notebooks execute;
- figures are written to `artifacts/figures`;
- notebook logic imports package modules;
- conclusions disclose limitations.

## Codex execution prompt

```text
Build the notebook framework and implement the first four notebooks from 05_RESEARCH_NOTEBOOKS.md. Reuse package modules. Execute them automatically, save outputs and generate a notebook index for the web Research page.
```
