# Phase 10 — FastAPI and Model Serving

## Goal

Expose artifacts and lightweight inference through a typed API.

## Endpoints

```text
GET  /health
GET  /api/sites
GET  /api/sites/{site_id}
GET  /api/sites/{site_id}/observations
GET  /api/sites/{site_id}/forecast
GET  /api/sites/{site_id}/metrics
GET  /api/sites/{site_id}/alerts
GET  /api/portfolio/forecast
GET  /api/portfolio/metrics
GET  /api/map/sites.geojson
GET  /api/matching/allocations
GET  /api/market/prices
POST /api/hedge/simulate
POST /api/upload/validate
POST /api/forecast/predict
GET  /api/research/notebooks
GET  /api/models
```

## Serving rules

The API may:

- read compact Parquet and JSON artifacts;
- load small model files;
- run lightweight inference;
- validate uploads;
- recalculate hedge scenarios.

The API must not:

- train all models;
- download large external datasets during a request;
- run a full historical backtest;
- depend on private credentials for the demo.

## Requirements

- Pydantic schemas;
- OpenAPI docs;
- proper 404 and validation errors;
- JSON-safe timestamps;
- caching;
- deterministic demo mode;
- health checks;
- model version returned with forecasts.

## API tests

Test:

- health;
- sites;
- unknown site;
- forecast response;
- quantile ordering;
- portfolio response;
- matching response;
- hedge simulation;
- upload validation.

## Acceptance criteria

- FastAPI starts;
- OpenAPI loads;
- tests pass;
- frontend can consume every P0 endpoint;
- no static placeholder response replaces artifacts;
- deployment bundle remains small.

## Codex execution prompt

```text
Implement Phase 10 from 10_API_AND_MODEL_SERVING.md. Create typed FastAPI routes backed by generated artifacts and small saved models. Add tests and OpenAPI documentation. Do not train or download heavy data inside requests.
```
