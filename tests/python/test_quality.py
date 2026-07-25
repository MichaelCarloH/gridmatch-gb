from __future__ import annotations

import pandas as pd

from gridmatch.data.quality import validate_site_observations
from gridmatch.data.uploads import validate_csv_upload


def _site(role: str = "demand", technology: str = "grid_supply", capacity: float = 1.0) -> dict:
    return {"site_id": "test-site", "site_role": role, "technology": technology, "installed_capacity_mw": capacity}


def _normal_day(value: float = 0.2) -> pd.DataFrame:
    return pd.DataFrame({"site_id": "test-site", "timestamp_utc": pd.date_range("2025-01-15", periods=48, freq="30min", tz="UTC"), "energy_mwh": value, "is_daylight": False})


def test_duplicate_observations_are_flagged_and_preserved() -> None:
    frame = _normal_day()
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    annotated, report = validate_site_observations(frame, _site(), reference_time=pd.Timestamp("2025-01-16T00:00:00Z"))
    assert len(annotated) == len(frame)
    assert report.duplicate_observations == 2
    assert annotated.quality_flag.str.contains("duplicate_timestamp").sum() == 2


def test_missing_period_and_invalid_interval_are_detected() -> None:
    frame = _normal_day().drop(index=10).reset_index(drop=True)
    _, report = validate_site_observations(frame, _site(), reference_time=pd.Timestamp("2025-01-16T00:00:00Z"))
    assert report.missing_periods == 1
    assert report.wrong_interval_count >= 1
    assert report.completeness < 1


def test_non_half_hour_frequency_is_detected() -> None:
    frame = pd.DataFrame({"site_id": "test-site", "timestamp_utc": pd.to_datetime(["2025-01-15T00:00Z", "2025-01-15T00:45Z", "2025-01-15T01:15Z"]), "energy_mwh": [0.2, 0.2, 0.2]})
    _, report = validate_site_observations(frame, _site(), reference_time=pd.Timestamp("2025-01-15T02:00:00Z"))
    assert report.wrong_interval_count >= 1


def test_negative_demand_is_flagged() -> None:
    frame = _normal_day()
    frame.loc[4, "energy_mwh"] = -0.1
    annotated, report = validate_site_observations(frame, _site(), reference_time=pd.Timestamp("2025-01-16T00:00:00Z"))
    assert report.negative_demand_count == 1
    assert "negative_demand" in annotated.loc[4, "quality_flag"]


def test_generation_above_capacity_is_flagged() -> None:
    frame = _normal_day()
    frame.loc[5, "energy_mwh"] = 0.75
    annotated, report = validate_site_observations(frame, _site("generation", "wind", 1.0), reference_time=pd.Timestamp("2025-01-16T00:00:00Z"))
    assert report.above_capacity_count == 1
    assert "generation_above_capacity" in annotated.loc[5, "quality_flag"]


def test_night_time_solar_is_flagged() -> None:
    frame = _normal_day(0.0)
    frame.loc[0, "energy_mwh"] = 0.1
    annotated, report = validate_site_observations(frame, _site("generation", "solar", 1.0), reference_time=pd.Timestamp("2025-01-16T00:00:00Z"))
    assert report.night_solar_count == 1
    assert "night_time_solar" in annotated.loc[0, "quality_flag"]


def test_long_zero_runs_extreme_spikes_and_stale_data_are_detected() -> None:
    frame = _normal_day(0.2)
    frame.loc[0:13, "energy_mwh"] = 0
    frame.loc[30, "energy_mwh"] = 5
    _, report = validate_site_observations(frame, _site(), reference_time=pd.Timestamp("2025-01-17T00:00:00Z"))
    assert report.long_zero_run_count >= 12
    assert report.extreme_spike_count >= 1
    assert report.stale_data


def test_csv_upload_validation_converts_units_and_preserves_rows() -> None:
    result = validate_csv_upload("tests/fixtures/upload_valid.csv")
    assert result.report["inferred_frequency_minutes"] == 30
    assert result.report["site_readiness"] == "ready"
    assert result.report["preserved_rows"] == 3
    assert result.annotated_data.loc[0, "consumption_mwh"] == 0.1
    assert set(result.annotated_data.data_origin) == {"uploaded"}


def test_csv_upload_flags_duplicates_and_invalid_values() -> None:
    result = validate_csv_upload("tests/fixtures/upload_invalid.csv")
    assert result.report["duplicates"] == 2
    assert result.report["anomalies"] == 2
    assert result.report["received_rows"] == result.report["preserved_rows"]
    assert result.report["site_readiness"] == "review"


def test_data_quality_score_is_bounded() -> None:
    _, good = validate_site_observations(_normal_day(), _site(), reference_time=pd.Timestamp("2025-01-16T00:00:00Z"))
    bad_frame = _normal_day(-1)
    _, bad = validate_site_observations(bad_frame, _site(), reference_time=pd.Timestamp("2026-01-01T00:00:00Z"))
    assert 0 <= good.quality_score <= 100
    assert 0 <= bad.quality_score <= 100
