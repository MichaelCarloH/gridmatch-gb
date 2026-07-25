# Progress

## Current phase

Phase 3 — Public and synthetic data collection: complete.

## Completed implementation

- Retained the Phase 2 scaffold and archived `legacy-prototype/` without modification.
- Added the reusable retrying/cached HTTP layer, response-schema checks and source-manifest model under `src/gridmatch/clients/` and `src/gridmatch/data/`.
- Added DESNZ REPD collection, Windows-1252-aware parsing, operational filtering, `pyproj` EPSG:27700 → EPSG:4326 conversion, invalid-coordinate flags and GeoJSON export.
- Added Elexon clients for BM Unit reference data, B1610 actual generation, Market Index Data and system prices, including date parameters, pagination support, cache reuse and fixture fallback.
- Added NESO CKAN package search, package/resource discovery, CSV download and datastore-query support with recorded package/resource IDs.
- Added Open-Meteo weather collection with separate issue/valid times, requested variables, model name and cache key inputs.
- Added national carbon-intensity, UK bank-holiday and Europe/London DST-transition collection.
- Added a deterministic 12-site simulated portfolio with 180 days of half-hourly demand, solar and wind observations (103,680 rows), fixed seed, explicit units and `data_origin=simulated`.
- Added `scripts/fetch_public_data.py`, `scripts/build_demo_dataset.py`, a portable Makefile Python selector and Windows `make.cmd` wrapper.
- Added 11 Python tests covering deterministic generation, site mix, coverage, physical constraints, night solar, coordinate conversion, valid GeoJSON, cache reuse, manifests, origins and fixture fallback.

## Generated artifacts

- `data/processed/repd_operational_sites.parquet` — 3,100 operational sites; 3,096 valid coordinates.
- `public/demo-data/repd_operational_sites.geojson` — 3,096 map-ready point features.
- `data/processed/bm_units.parquet` — 3,041 records.
- `data/processed/public_generation.parquet` — 9,168 B1610 records.
- `data/processed/prices.parquet` — 58 market/system-price records.
- `data/processed/neso_demand_demo.parquet` — 96 records.
- `data/processed/weather.parquet` — 48 records with distinct issue and valid times.
- `data/processed/carbon_intensity.parquet` — 48 records.
- `data/processed/calendar.parquet` — 20 bank-holiday/DST records.
- `data/demo/sites.parquet` — 12 simulated sites.
- `data/demo/observations.parquet` — 103,680 UTC half-hourly records.
- `data/demo/site_metadata.json` — deterministic seed, units, schema and site metadata.
- `data/manifests/*.json` — 10 public/simulated provenance manifests.

## Verification evidence

- `python scripts/fetch_public_data.py`: passed; a second run reported cache hits for every public response.
- `python scripts/build_demo_dataset.py`: passed twice.
- SHA-256 equality across consecutive synthetic runs: sites, observations and metadata all `True`.
- `make demo-data`: passed through the Windows GNU Make wrapper.
- `pytest`: 11 passed with no warnings.
- `npm run build`: production compilation remains successful.
- Artifact audit: timestamps are `datetime64[ns, UTC]`; manifest origins are exactly `public` and `simulated`.

## External API limitations

- All configured official endpoints were reachable during this run; the checked-in compact fixtures were derived from those successful responses.
- Source schemas and availability remain external dependencies. Retries handle transient failures; schema changes fail explicitly; unavailable sources select labelled fixtures and log warnings.
- Demonstration windows are deliberately compact and are not complete market histories.
- Open-Meteo ERA5 archive data is historical weather, not an operational forecast-vintage archive.

## Remaining Phase 3 gaps

No P0 acceptance gaps remain. Optional broader histories, regional carbon queries and additional NESO/Elexon datasets are intentionally deferred; they are not required for Phase 3 acceptance.

## Next

Proceed to Phase 4 (`04_DATA_MODEL_AND_VALIDATION.md`) only when explicitly requested.
