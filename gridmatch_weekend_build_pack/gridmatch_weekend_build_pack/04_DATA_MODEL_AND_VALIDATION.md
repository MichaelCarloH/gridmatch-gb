# Phase 4 — Data Model, Settlement Logic and Quality Validation

## Goal

Standardise all site, observation, forecast and market records before modelling.

## Core schemas

### Site

```text
site_id
name
site_role
technology
business_archetype
operator
latitude
longitude
postcode
region
installed_capacity_mw
bmu_id
repd_id
data_origin
status
```

### Observation

```text
site_id
timestamp_utc
settlement_date
settlement_period
consumption_mwh
generation_mwh
actual_mwh
quality_flag
source
retrieved_at
```

### Forecast

```text
site_id
issue_time_utc
valid_time_utc
settlement_date
settlement_period
horizon_periods
model_id
model_version
q10_mwh
q50_mwh
q90_mwh
point_mwh
actual_mwh
```

### Weather

```text
site_id
issue_time_utc
valid_time_utc
temperature_2m
cloud_cover
shortwave_radiation
wind_speed_10m
wind_speed_100m
wind_direction_100m
pressure
weather_model
```

### Price

```text
timestamp_utc
settlement_date
settlement_period
market_index_price_gbp_mwh
system_price_gbp_mwh
source
```

## Settlement functions

Implement:

```python
expected_period_count(date)
timestamp_to_settlement_period(timestamp_utc)
settlement_period_to_timestamp(date, period)
validate_settlement_day(df, date)
```

Requirements:

- UTC internally;
- Europe/London display;
- 46 periods on spring transition;
- 48 normal;
- 50 autumn transition.

## Data-quality checks

Per site:

- missing timestamps;
- duplicate timestamps;
- wrong interval;
- negative demand;
- negative generation;
- output above installed capacity;
- long zero runs;
- extreme spikes;
- stale data;
- impossible night-time solar;
- DST-period errors.

## Quality score

Create a score from 0–100 based on:

- completeness;
- consistency;
- physical validity;
- recency;
- anomaly rate.

## Upload validation

Accepted format:

```csv
timestamp,consumption_kwh,generation_kwh
```

Output:

- date range;
- inferred frequency;
- expected rows;
- completeness;
- duplicates;
- anomalies;
- site readiness;
- recommended next action.

## Acceptance criteria

- DST tests pass;
- all schemas validate;
- invalid observations are flagged, not silently dropped;
- data-quality reports are generated for every site;
- uploaded CSV validation works on fixtures;
- units are converted consistently.

## Codex execution prompt

```text
Implement Phase 4 from 04_DATA_MODEL_AND_VALIDATION.md. Create typed schemas, GB settlement utilities, DST tests, data-quality scoring and CSV validation. Do not move to modelling until all settlement and validation tests pass.
```
