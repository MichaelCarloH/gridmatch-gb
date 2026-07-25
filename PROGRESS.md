# Progress

## Current phase

Phase 5 — Research notebook framework and notebooks 00–03: complete.

## Preserved work and scope

- All completed Phase 3 public/simulated pipelines and Phase 4 schemas, settlement utilities, validation logic, tests and generated data artifacts remain intact.
- `legacy-prototype/` remains archived and unchanged.
- No feature engineering, model training, portfolio forecasting, renewable matching, hedge modelling, API routes or frontend product pages were started.

## Completed Phase 5 implementation

- `src/gridmatch/research/common.py`: shared deterministic chart style and CSV artifact writer.
- `src/gridmatch/research/market.py`: worked 46/48/50 settlement-day, imbalance and point-versus-probabilistic examples.
- `src/gridmatch/research/assets.py`: reusable REPD technology, capacity, project-size, region, coordinate-quality and map summaries.
- `src/gridmatch/research/profiles.py`: reusable archetype, weekday/weekend half-hour profile, capacity-factor, missingness, quality-flag and score-distribution summaries.
- `src/gridmatch/research/weather.py`: weather-variable availability, coordinate-distance and demand/solar/wind methodology tables.
- `scripts/build_research_notebooks.py`: deterministic source-notebook builder.
- `scripts/execute_notebooks.py`: ordered, fail-fast execution using a repository-local kernelspec pinned to the active interpreter; writes executed copies, timings, status and the JSON index.
- `pyproject.toml`: adds Matplotlib, nbformat, nbclient and ipykernel execution dependencies.
- `tests/python/test_notebooks.py`: six tests for notebook contracts, cached-data use, index schema, error-free execution, artifacts and public/simulated disclosure.

## Notebook and research outputs

Source notebooks:

- `notebooks/00_gb_market_and_settlement.ipynb`
- `notebooks/01_site_map_and_public_assets.ipynb`
- `notebooks/02_data_quality_and_site_profiles.ipynb`
- `notebooks/03_weather_features.ipynb`

Executed copies and index:

- `artifacts/notebooks/00_gb_market_and_settlement.executed.ipynb`
- `artifacts/notebooks/01_site_map_and_public_assets.executed.ipynb`
- `artifacts/notebooks/02_data_quality_and_site_profiles.executed.ipynb`
- `artifacts/notebooks/03_weather_features.executed.ipynb`
- `artifacts/notebooks/notebook_index.json`

Research summaries:

- `research/01_gb_market_primer.md`
- `research/02_data_source_audit.md`
- `research/03_data_quality_findings.md`
- `research/04_weather_and_leakage.md`

Generated evidence:

- Eight figures under `artifacts/figures/`: one settlement-day figure, two public-asset figures, four site-profile figures and one weather-driver figure.
- Nineteen CSV tables under `artifacts/tables/`: settlement/imbalance, REPD, site profile/quality and weather-methodology outputs.
- Public REPD evidence covers 3,100 operational projects, including 3,096 valid and four invalid coordinates.
- Simulated portfolio evidence preserves all 103,680 observations and all 5,086 quality flags; 12 sites are currently `ready`, with scores from 95.55 to 99.84.

## Phase 5 P0 acceptance audit

- All four required notebooks begin with business purpose and operator relevance: passed.
- Notebooks import reusable `gridmatch` modules, use cached Phase 3/4 artifacts and contain no ingestion clients or external API calls: passed.
- Public and simulated data are explicitly distinguished in notebooks and summaries: passed.
- GB participants, physical-versus-commercial matching, 46/48/50 settlement days, issue/delivery time, imbalance and probabilistic forecasts are covered without claiming full supplier settlement: passed.
- REPD technology, capacity, size, region, geography and coordinate validity are analysed; two professional figures are saved: passed.
- Archetypes, half-hour/weekday/weekend shapes, capacity factors, missingness, quality flags, score distribution and readiness are analysed; four required site-profile figures are saved: passed.
- The 5,086 flags remain auditable and are described as review candidates, not confirmed faults: passed.
- Weather issue/valid time, leakage, coordinate alignment, missingness and demand/solar/wind availability tables are covered without production feature generation: passed.
- The ERA5 historical-weather versus forecast-vintage limitation is explicit: passed.
- Execution is deterministic, ordered and fail-fast; all four executed notebooks contain no error outputs: passed.
- Index fields, expected artifacts, summary structure and cached-ingestion boundary are test-covered: passed.
- No Phase 5 P0 gaps remain.

## Verification evidence

- `py -3 scripts/build_research_notebooks.py`: passed; generated four source notebooks.
- `py -3 scripts/execute_notebooks.py`: passed; four notebooks executed in order and per-notebook UTC timestamps and durations were written to the index.
- `py -3 -m pytest`: 36 passed.
- `cmd /c npm run build`: passed; Next.js compiled, type-checked and generated four static pages.
- Visual audit: settlement, REPD capacity/geography, site-profile and weather figures render legibly and support the accompanying conclusions.

## Known prototype limitations

- REPD metadata does not imply public half-hourly generation or commercial availability.
- The 12-site business portfolio is simulated.
- Current Open-Meteo/ERA5 evidence is historical realised weather at one grid point, not an operational forecast-vintage archive.
- Notebook 00 is an explanatory market primer, not a complete BSC or licensed-supplier settlement implementation.

## Next

Proceed to Phase 6 only when explicitly requested.
