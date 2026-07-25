"""Build the four deterministic Phase 5 source notebooks."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_ROOT = ROOT / "notebooks"


def notebook(cells: list, name: str) -> Path:
    document = nbf.v4.new_notebook(cells=cells)
    document.metadata.update({"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}})
    path = NOTEBOOK_ROOT / f"{name}.ipynb"
    path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(document, path)
    return path


def build() -> list[Path]:
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    notebooks = []
    notebooks.append(notebook([
        md("""# Business purpose — GB market and settlement primer

This notebook gives an energy portfolio operator a concise, worked view of Great Britain half-hourly settlement, contracted-versus-metered imbalance and the information advantage of probabilistic forecasts. It uses reusable GridMatch settlement utilities and deterministic examples; it does **not** reproduce a licensed supplier's complete settlement system."""),
        md("""## Participants and commercial context

- **Generators** produce physical electricity; **consumers** use it.
- **Suppliers** contract for and settle customer energy, while **NESO** operates the electricity system and **Elexon** administers Balancing and Settlement Code arrangements.
- Physical electricity flows through the grid; a commercial renewable match is an accounting/contractual allocation and does not create a dedicated physical wire.

An operator therefore needs coherent site and portfolio forecasts: metered demand or generation that differs from contracted volume creates an imbalance position."""),
        code("""import numpy as np
from IPython.display import display
from gridmatch.research.market import settlement_day_examples, imbalance_worked_example, forecast_information_example, save_market_artifacts

np.random.seed(20260725)
artifact_paths = save_market_artifacts()
display(settlement_day_examples())
print({name: str(path) for name, path in artifact_paths.items()})"""),
        md("""## Settlement-day mechanics

A normal local delivery day has 48 half-hours. The spring clock change removes one local hour (46 periods); the autumn change repeats one local hour (50 periods). UTC timestamps remain unambiguous, while Europe/London labels provide the operational display. Forecast records must keep **issue time** (what was knowable) separate from **valid/delivery time** (what is being predicted)."""),
        code("""imbalance = imbalance_worked_example()
display(imbalance)
print(f\"Net example imbalance: {imbalance['imbalance_mwh'].sum():.3f} MWh\")"""),
        md("""## Point versus probabilistic forecasts

A point forecast supports a central contracted volume. Calibrated q10/q50/q90 estimates additionally expose plausible tails, enabling an operator to compare short and long risk when costs are asymmetric. Quantiles are information, not an instruction to trade; calibration and governance remain necessary."""),
        code("display(forecast_information_example())"),
        md("""## Findings, limitations and production implications

**Findings:** the reusable functions produce 48/46/50 periods and unambiguous UTC boundaries; the worked imbalance convention is metered minus contracted volume, where positive is long and negative is short. **Limitations:** worked volumes are deterministic illustrations, not public or simulated customer observations, and omit the full BSC settlement calculation. **Production implications:** preserve issue time, delivery time, contract volume and meter volume; test DST days explicitly; only use probabilistic forecasts after calibration and human-approved risk policy."""),
    ], "00_gb_market_and_settlement"))

    notebooks.append(notebook([
        md("""# Business purpose — public renewable assets and site geography

This notebook helps an energy portfolio operator understand the scale, technology mix and geographic concentration of operational public REPD projects before selecting assets for renewable forecasting research. REPD records are **public metadata**, not simulated customer sites."""),
        code("""import numpy as np
import pandas as pd
from IPython.display import display
from gridmatch.research.assets import asset_summaries, save_asset_artifacts
from gridmatch.research.common import project_path

np.random.seed(20260725)
repd = pd.read_parquet(project_path('data', 'processed', 'repd_operational_sites.parquet'))
assert set(repd['data_origin']) == {'public'}
summaries = asset_summaries(repd)
artifact_paths = save_asset_artifacts(repd)
display(summaries['technology'].head(15))
display(summaries['map_ready'])
print({name: str(path) for name, path in artifact_paths.items()})"""),
        md("""## Capacity, project size and regional concentration

Counts alone overstate technologies with many small projects, so the next tables separate project count, total MW and size quantiles. Region is retained from the official source; coordinates are converted from British National Grid by the Phase 3 pipeline rather than inside this notebook."""),
        code("""display(summaries['capacity'].head(15))
display(summaries['region'].head(12))
solar_wind = summaries['technology'][summaries['technology']['technology'].astype(str).str.contains('solar|wind', case=False, regex=True)]
display(solar_wind)"""),
        md("""## Public-data boundary

REPD shows planning/development metadata and operational status. It does **not** imply that every project exposes public half-hourly generation, a usable BM Unit mapping, availability, curtailment or commercial terms. The separate 12-site portfolio used elsewhere is explicitly **simulated**."""),
        md("""## Findings, limitations and production implications

**Findings:** technology, capacity, size, region and coordinate-validity summaries are reproducible from the cached public artifact; solar and wind form clear forecast-relevant subsets. **Limitations:** operational status and coordinates can be stale or incomplete, and REPD does not guarantee meter history. **Production implications:** version each extract, retain invalid-coordinate flags, validate prospective assets independently and do not infer output history from planning metadata."""),
    ], "01_site_map_and_public_assets"))

    notebooks.append(notebook([
        md("""# Business purpose — data quality and site profiles

This notebook lets an energy portfolio operator see whether each **simulated** demand or renewable site is sufficiently complete, physically plausible and interpretable for later research. It reuses Phase 4 readiness and audit artifacts; flagged observations remain present."""),
        code("""import numpy as np
import pandas as pd
from IPython.display import display
from gridmatch.research.common import project_path
from gridmatch.research.profiles import profile_summaries, save_profile_artifacts

np.random.seed(20260725)
sites = pd.read_parquet(project_path('data', 'demo', 'sites.parquet'))
observations = pd.read_parquet(project_path('data', 'demo', 'observations.parquet'))
readiness = pd.read_parquet(project_path('data', 'quality', 'site_readiness.parquet'))
annotated = pd.read_parquet(project_path('data', 'quality', 'annotated_observations.parquet'))
assert set(sites['data_origin']) == {'simulated'}
assert set(observations['data_origin']) == {'simulated'}
assert len(annotated) == len(observations)
summaries = profile_summaries(sites, observations, readiness, annotated)
artifact_paths = save_profile_artifacts(sites, observations, readiness, annotated)
display(summaries['archetypes'])
display(summaries['quality_score_distribution'])
display(summaries['readiness'][['site_id', 'quality_score', 'site_readiness']])
print({name: str(path) for name, path in artifact_paths.items()})"""),
        md("""## Profiles, capacity factors and weekday effects

Average half-hour shapes expose archetype schedules and weekday/weekend differences. Generator capacity factors are descriptive ratios over the simulated period, not performance claims about public assets."""),
        code("""display(summaries['capacity_factors'])
display(summaries['half_hour_profiles'].head(12))
display(summaries['missingness'])"""),
        md("""## Quality flags and readiness

The Phase 4 score combines completeness, consistency, physical validity, recency and anomaly rate. All 12 sites are currently `ready` because their scores exceed the documented threshold and no critical physical/timestamp failures occur. The 5,086 flagged rows in the current artifact are retained rule-based candidates—mostly robust spikes plus long zero runs—not automatically confirmed faults."""),
        code("""display(summaries['quality_flags'])
flagged_count = int((annotated['quality_flag'] != 'valid').sum())
print({'source_rows': len(observations), 'annotated_rows': len(annotated), 'flagged_rows': flagged_count, 'all_rows_retained': len(observations) == len(annotated)})"""),
        md("""## Findings, limitations and production implications

**Findings:** office, manufacturing, solar and wind profiles are visibly distinct; all sites pass current readiness criteria; all flags remain auditable. **Limitations:** data is simulated and the rules deliberately favour sensitivity, so a flag is not proof of bad data. **Production implications:** decide per use case whether to exclude, down-weight, repair or explicitly model flagged rows; record that decision and never overwrite the source observation."""),
    ], "02_data_quality_and_site_profiles"))

    notebooks.append(notebook([
        md("""# Business purpose — weather availability and leakage

This notebook establishes how an energy portfolio operator should align weather information with business demand, solar and wind sites without leaking realised future conditions into a forecast. It uses the cached **public** Open-Meteo artifact and **simulated** site coordinates; it does not create production model features."""),
        code("""import numpy as np
import pandas as pd
from IPython.display import display
from gridmatch.research.common import project_path
from gridmatch.research.weather import weather_availability, example_weather_tables, save_weather_artifacts

np.random.seed(20260725)
weather = pd.read_parquet(project_path('data', 'processed', 'weather.parquet'))
sites = pd.read_parquet(project_path('data', 'demo', 'sites.parquet'))
assert set(weather['data_origin']) == {'public'}
assert set(sites['data_origin']) == {'simulated'}
assert (pd.to_datetime(weather['issue_time'], utc=True) != pd.to_datetime(weather['valid_time'], utc=True)).all()
availability = weather_availability(weather)
examples = example_weather_tables(weather, sites)
artifact_paths = save_weather_artifacts(weather, sites)
display(availability)
print({name: str(path) for name, path in artifact_paths.items()})"""),
        md("""## Issue time, valid time and leakage

`issue_time` is when information became available; `valid_time` is when weather applies. A historical observation describes realised weather. A historical forecast vintage preserves what an operator could actually know at the issue time. Training with realised future weather while evaluating a day-ahead decision leaks information and overstates performance."""),
        code("""for use_case, table in examples.items():
    print(f'--- {use_case} example ---')
    display(table)
print('Weather missing values:', int(weather.isna().sum().sum()))"""),
        md("""## Methodology by site type

- **Demand:** temperature and calendar-aware sensitivity; cloud may proxy lighting/conditions.
- **Solar:** shortwave radiation, cloud and temperature, aligned to the site coordinate.
- **Wind:** wind speed/direction and pressure; hub-height wind is preferable to the current 10 m field.

Coordinate distance is recorded rather than silently treating one grid point as co-located. Missing weather should create availability flags and an explicit fallback hierarchy; it must not be backfilled from future observations."""),
        md("""## Findings, limitations and production implications

**Findings:** the compact artifact supplies 48 public hourly records and the variables needed to demonstrate demand/solar/wind availability tables; issue and valid times remain distinct. **Limitations:** the current Open-Meteo data is ERA5 historical weather, not a complete operational forecast-vintage archive, and one London grid point is used for examples. **Production implications:** archive forecast vintages at issue time, enrich each coordinate, record model/run identifiers and make missing-weather fallback visible before any forecasting model is trained."""),
    ], "03_weather_features"))
    return notebooks


if __name__ == "__main__":
    for path in build():
        print(path.relative_to(ROOT))
