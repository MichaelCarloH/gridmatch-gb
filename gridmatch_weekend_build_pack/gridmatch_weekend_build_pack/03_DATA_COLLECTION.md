# Phase 3 — Public and Synthetic Data Collection

## Goal

Build reproducible, cached data pipelines before modelling.

## Data categories

### Public renewable-site metadata

Use the DESNZ Renewable Energy Planning Database for:

- project name;
- technology;
- installed capacity;
- development status;
- operator;
- postcode;
- easting/northing;
- planning metadata.

Tasks:

1. download the current public CSV;
2. store the raw file unchanged;
3. record retrieval timestamp and URL;
4. clean field names;
5. filter operational projects;
6. convert British National Grid coordinates to WGS84;
7. export `repd_operational_sites.parquet`;
8. export GeoJSON for the map.

### Public GB electricity data

Build a reusable Elexon client for:

- BM Unit reference data;
- actual generation output;
- generation by fuel type;
- market index data;
- system prices;
- optional physical notifications.

Requirements:

- date-window parameters;
- retries;
- pagination;
- schema validation;
- local caching;
- source metadata;
- rate-limit awareness.

### NESO data

Build a reusable CKAN client for:

- historic demand;
- day-ahead demand forecasts;
- historic wind forecasts;
- embedded wind and solar estimates;
- generation mix.

Do not hardcode resource IDs without documenting them.

### Weather

Build an Open-Meteo client for:

- historical forecasts;
- previous forecast runs;
- temperature;
- cloud cover;
- irradiance;
- wind speed;
- wind direction;
- pressure;
- weather issue time and valid time.

Cache by:

```text
latitude
longitude
issue_time
valid_time
weather_model
```

### Carbon intensity

Collect national and regional carbon-intensity data for:

- residual grid emissions;
- avoided emissions;
- regional context.

### Calendar

Collect:

- UK bank holidays;
- weekday/weekend;
- daylight-saving transitions.

## Synthetic commercial portfolio

Generate at least:

- 2 offices;
- 2 warehouses;
- 2 retail sites;
- 1 hospitality site;
- 1 manufacturing site;
- 2 solar sites;
- 2 wind sites.

A site may be public or simulated, but every record must include:

```text
data_origin = public | simulated | uploaded
```

## Synthetic demand equation

Create transparent site demand:

```math
load_{i,t}
=
base_i
+ calendar_{i,t}
+ temperature_{i,t}
+ portfolio_factor_t
+ autoregressive_{i,t}
+ noise_{i,t}
+ anomaly_{i,t}
```

## Synthetic solar equation

```math
solar_{i,t}
=
capacity_i
× daylight_t
× irradiance_t
× cloud_adjustment_t
× temperature_adjustment_t
+ noise_t
```

Clip to physical capacity and zero at night.

## Synthetic wind equation

Use a stylised power curve:

- zero below cut-in;
- cubic growth before rated speed;
- capacity at rated speed;
- zero above cut-out;
- add noise and outages.

## Required outputs

```text
data/raw/
data/processed/repd_operational_sites.parquet
data/processed/public_generation.parquet
data/processed/weather.parquet
data/processed/prices.parquet
data/demo/sites.parquet
data/demo/observations.parquet
data/demo/site_metadata.json
```

## Data source manifest

Create a machine-readable manifest:

```json
{
  "dataset": "repd",
  "source_url": "...",
  "retrieved_at": "...",
  "license_or_terms": "...",
  "raw_path": "...",
  "processed_path": "...",
  "schema_version": "1"
}
```

## Acceptance criteria

- data collection is reproducible;
- external failures use cached fixtures;
- synthetic generation is deterministic;
- at least 180 days of half-hourly observations exist;
- all units are explicit;
- all timestamps are UTC;
- no synthetic customer data is described as public or real.

## Codex execution prompt

```text
Implement Phase 3 from 03_DATA_COLLECTION.md. Build reusable clients, raw-data caching, schema validation, source manifests and deterministic synthetic sites. Generate the required Parquet and GeoJSON artifacts. Do not begin model training. Run the pipeline twice and verify that the second run is deterministic and cache-aware.
```
