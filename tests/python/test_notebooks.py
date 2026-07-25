from __future__ import annotations

import json
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_NAMES = [
    "00_gb_market_and_settlement",
    "01_site_map_and_public_assets",
    "02_data_quality_and_site_profiles",
    "03_weather_features",
]

EXPECTED_ARTIFACTS = [
    "artifacts/figures/00_gb_settlement_period_counts.png",
    "artifacts/figures/01_repd_capacity_by_technology.png",
    "artifacts/figures/01_repd_operational_geography.png",
    "artifacts/figures/02_profile_dem_office_london.png",
    "artifacts/figures/02_profile_dem_manufacturing_sheffield.png",
    "artifacts/figures/02_profile_gen_solar_cambridge.png",
    "artifacts/figures/02_profile_gen_wind_cumbria.png",
    "artifacts/figures/03_weather_driver_overview.png",
    "artifacts/tables/00_settlement_day_examples.csv",
    "artifacts/tables/00_imbalance_worked_example.csv",
    "artifacts/tables/00_point_vs_probabilistic.csv",
    "artifacts/tables/01_repd_technology_summary.csv",
    "artifacts/tables/01_repd_capacity_summary.csv",
    "artifacts/tables/01_repd_region_summary.csv",
    "artifacts/tables/01_repd_map_ready_summary.csv",
    "artifacts/tables/02_archetypes.csv",
    "artifacts/tables/02_half_hour_profiles.csv",
    "artifacts/tables/02_capacity_factors.csv",
    "artifacts/tables/02_missingness.csv",
    "artifacts/tables/02_quality_flags.csv",
    "artifacts/tables/02_quality_score_distribution.csv",
    "artifacts/tables/02_readiness.csv",
    "artifacts/tables/03_weather_availability.csv",
    "artifacts/tables/03_demand_weather_example.csv",
    "artifacts/tables/03_solar_weather_example.csv",
    "artifacts/tables/03_wind_weather_example.csv",
    "artifacts/tables/03_weather_missingness.csv",
]


def _read_notebook(name: str, *, executed: bool = False):
    suffix = ".executed.ipynb" if executed else ".ipynb"
    directory = ROOT / ("artifacts/notebooks" if executed else "notebooks")
    return nbformat.read(directory / f"{name}{suffix}", as_version=4)


def test_p0_notebooks_exist_and_follow_research_contract() -> None:
    for name in NOTEBOOK_NAMES:
        document = _read_notebook(name)
        markdown = "\n".join(
            cell.source for cell in document.cells if cell.cell_type == "markdown"
        ).lower()
        code = "\n".join(
            cell.source for cell in document.cells if cell.cell_type == "code"
        )

        assert "business purpose" in document.cells[0].source.lower()
        assert "findings" in markdown
        assert "limitations" in markdown
        assert "production implications" in markdown
        assert "public" in markdown
        assert "simulated" in markdown
        assert "gridmatch." in code
        assert "np.random.seed(20260725)" in code
        if name != "00_gb_market_and_settlement":
            assert "project_path(" in code


def test_notebooks_use_cached_artifacts_not_ingestion_clients() -> None:
    forbidden = (
        "requests.get",
        "http://",
        "https://",
        "CachedHttpClient",
        "fetch_public_data",
    )
    for name in NOTEBOOK_NAMES:
        document = _read_notebook(name)
        code = "\n".join(
            cell.source for cell in document.cells if cell.cell_type == "code"
        )
        assert "read_parquet" in code or name == "00_gb_market_and_settlement"
        assert not any(value in code for value in forbidden)


def test_notebook_index_records_successful_execution() -> None:
    index_path = ROOT / "artifacts/notebooks/notebook_index.json"
    entries = json.loads(index_path.read_text(encoding="utf-8"))

    assert [entry["name"] for entry in entries] == NOTEBOOK_NAMES
    for entry in entries:
        assert entry["status"] == "executed"
        assert entry["summary"]
        assert entry["key_result"]
        assert entry["execution_timestamp"].endswith("+00:00")
        assert entry["duration_seconds"] >= 0
        assert entry["artifact_links"]
        assert (ROOT / entry["output_path"]).is_file()


def test_executed_notebooks_have_no_error_outputs() -> None:
    for name in NOTEBOOK_NAMES:
        document = _read_notebook(name, executed=True)
        outputs = [
            output
            for cell in document.cells
            if cell.cell_type == "code"
            for output in cell.get("outputs", [])
        ]
        assert not [output for output in outputs if output.output_type == "error"]


def test_expected_research_artifacts_are_nonempty() -> None:
    for relative_path in EXPECTED_ARTIFACTS:
        path = ROOT / relative_path
        assert path.is_file(), relative_path
        assert path.stat().st_size > 0, relative_path


def test_research_summaries_separate_evidence_and_assumptions() -> None:
    summaries = [
        ROOT / "research/01_gb_market_primer.md",
        ROOT / "research/02_data_source_audit.md",
        ROOT / "research/03_data_quality_findings.md",
        ROOT / "research/04_weather_and_leakage.md",
    ]
    required_sections = [
        "## Verified public facts",
        "## Observed data findings",
        "## Modelling assumptions",
        "## Prototype limitations",
        "## Production recommendations",
    ]
    for path in summaries:
        content = path.read_text(encoding="utf-8")
        assert all(section in content for section in required_sections)
        assert "public" in content.lower()
        assert "simulated" in content.lower()
