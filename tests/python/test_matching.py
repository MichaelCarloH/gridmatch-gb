from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from gridmatch.matching.distance import great_circle_distance_km
from gridmatch.matching.metrics import safe_ratio
from gridmatch.matching.optimizer import MatchParticipant, solve_allocation

ROOT = Path(__file__).resolve().parents[2]
MATCHING_ROOT = ROOT / "artifacts/matching"


def _participant(
    site_id: str,
    available_mwh: float,
    latitude: float,
    longitude: float,
    *,
    region: str = "Test",
    technology: str = "wind",
) -> MatchParticipant:
    return MatchParticipant(
        site_id=site_id,
        available_mwh=available_mwh,
        latitude=latitude,
        longitude=longitude,
        region=region,
        technology=technology,
    )


def test_distance_calculation() -> None:
    london_to_edinburgh = great_circle_distance_km(
        51.5074,
        -0.1278,
        55.9533,
        -3.1883,
    )
    assert np.isclose(london_to_edinburgh, 533.65, atol=1.0)
    assert great_circle_distance_km(51.5, -0.1, 51.5, -0.1) == 0


def test_optimizer_is_deterministic_and_maximises_match() -> None:
    generators = [
        _participant("gen_b", 2.0, 54.0, -2.0),
        _participant("gen_a", 3.0, 52.0, 0.0, technology="solar"),
    ]
    consumers = [
        _participant("dem_b", 1.5, 55.0, -3.0),
        _participant("dem_a", 2.0, 51.5, -0.1),
    ]
    for mode in ("maximum_match", "local_preference"):
        first = solve_allocation(generators, consumers, mode=mode)
        second = solve_allocation(
            list(reversed(generators)),
            list(reversed(consumers)),
            mode=mode,
        )
        assert first == second
        assert np.isclose(first.matched_mwh, 3.5)
        assert all(row.matched_mwh >= 0 for row in first.allocations)
        assert first.matched_mwh <= first.total_generation_mwh
        assert first.matched_mwh <= first.total_demand_mwh


def test_optimizer_handles_zero_demand_and_generation() -> None:
    generator = [_participant("gen", 2.0, 54.0, -2.0)]
    zero_generator = [_participant("gen", 0.0, 54.0, -2.0)]
    consumer = [_participant("dem", 3.0, 51.5, -0.1)]
    zero_consumer = [_participant("dem", 0.0, 51.5, -0.1)]

    zero_demand = solve_allocation(generator, zero_consumer)
    zero_generation = solve_allocation(zero_generator, consumer)
    assert zero_demand.matched_mwh == 0
    assert zero_generation.matched_mwh == 0
    assert zero_demand.allocations == ()
    assert zero_generation.allocations == ()
    assert safe_ratio(0, 0) == 0
    assert safe_ratio(1, 0) == 0


def test_allocation_artifacts_conserve_energy_by_period_and_site() -> None:
    forecast = pd.read_parquet(
        MATCHING_ROOT / "forecast_allocations.parquet"
    )
    realised = pd.read_parquet(
        MATCHING_ROOT / "realised_allocations.parquet"
    )
    periods = pd.read_parquet(MATCHING_ROOT / "period_summary.parquet")
    allocations = pd.concat([forecast, realised], ignore_index=True)
    tolerance = 1e-7

    assert (allocations["matched_mwh"] >= 0).all()
    assert (periods["residual_grid_demand_mwh"] >= 0).all()
    assert (periods["unused_generation_mwh"] >= 0).all()
    np.testing.assert_allclose(
        periods["residual_grid_demand_mwh"],
        periods["total_demand_mwh"] - periods["matched_mwh"],
        atol=tolerance,
    )
    np.testing.assert_allclose(
        periods["unused_generation_mwh"],
        periods["total_generation_mwh"] - periods["matched_mwh"],
        atol=tolerance,
    )
    assert (
        periods["matched_mwh"] <= periods["total_demand_mwh"] + tolerance
    ).all()
    assert (
        periods["matched_mwh"]
        <= periods["total_generation_mwh"] + tolerance
    ).all()
    np.testing.assert_allclose(
        periods["matched_mwh"],
        periods[
            ["total_demand_mwh", "total_generation_mwh"]
        ].min(axis=1),
        atol=tolerance,
    )
    keys = ["timestamp_utc", "allocation_type", "matching_mode"]
    by_generator = allocations.groupby(
        keys + ["generator_site_id"]
    ).agg(
        allocated=("matched_mwh", "sum"),
        available=("generator_available_mwh", "first"),
    )
    by_consumer = allocations.groupby(
        keys + ["consumer_site_id"]
    ).agg(
        allocated=("matched_mwh", "sum"),
        demand=("consumer_demand_mwh", "first"),
    )
    assert (
        by_generator["allocated"] <= by_generator["available"] + tolerance
    ).all()
    assert (
        by_consumer["allocated"] <= by_consumer["demand"] + tolerance
    ).all()


def test_forecast_and_realised_outputs_are_separate() -> None:
    forecast = pd.read_parquet(
        MATCHING_ROOT / "forecast_allocations.parquet"
    )
    realised = pd.read_parquet(
        MATCHING_ROOT / "realised_allocations.parquet"
    )
    periods = pd.read_parquet(MATCHING_ROOT / "period_summary.parquet")
    comparison = pd.read_parquet(
        MATCHING_ROOT / "allocation_comparison.parquet"
    )
    assert set(forecast["allocation_type"]) == {"forecast"}
    assert set(realised["allocation_type"]) == {"realised"}
    assert set(periods["forecast_or_actual"]) == {"forecast", "actual"}
    assert set(periods["matching_mode"]) == {
        "maximum_match",
        "local_preference",
    }
    np.testing.assert_allclose(
        comparison["allocation_error_mwh"],
        comparison["realised_matched_mwh"]
        - comparison["forecast_matched_mwh"],
    )


def test_map_arcs_are_valid_and_matching_totals_reconcile_to_phase_7() -> None:
    arcs = pd.read_parquet(MATCHING_ROOT / "map_arcs.parquet")
    periods = pd.read_parquet(MATCHING_ROOT / "period_summary.parquet")
    portfolio = pd.read_parquet(
        ROOT / "artifacts/forecasts/portfolio_forecasts.parquet"
    )
    required = {
        "timestamp_utc",
        "settlement_period",
        "generator_site_id",
        "consumer_site_id",
        "start_latitude",
        "start_longitude",
        "end_latitude",
        "end_longitude",
        "matched_mwh",
        "distance_km",
        "technology",
        "allocation_type",
    }
    assert required.issubset(arcs.columns)
    assert arcs["start_latitude"].between(-90, 90).all()
    assert arcs["end_latitude"].between(-90, 90).all()
    assert arcs["start_longitude"].between(-180, 180).all()
    assert arcs["end_longitude"].between(-180, 180).all()
    assert (arcs["distance_km"] >= 0).all()

    reference = portfolio.rename(
        columns={"valid_time_utc": "timestamp_utc"}
    )
    forecast = periods[
        (periods["allocation_type"] == "forecast")
        & (periods["matching_mode"] == "maximum_match")
    ].merge(reference, on="timestamp_utc", validate="one_to_one")
    realised = periods[
        (periods["allocation_type"] == "realised")
        & (periods["matching_mode"] == "maximum_match")
    ].merge(reference, on="timestamp_utc", validate="one_to_one")
    np.testing.assert_allclose(
        forecast["total_demand_mwh"],
        forecast["bottom_up_demand_point_mwh"],
        atol=1e-8,
    )
    np.testing.assert_allclose(
        forecast["total_generation_mwh"],
        forecast["bottom_up_generation_point_mwh"],
        atol=1e-8,
    )
    np.testing.assert_allclose(
        realised["total_demand_mwh"],
        realised["actual_demand_mwh"],
        atol=1e-8,
    )
    np.testing.assert_allclose(
        realised["total_generation_mwh"],
        realised["actual_generation_mwh"],
        atol=1e-8,
    )


def test_matching_summaries_have_safe_coverage_and_strict_json() -> None:
    consumers = pd.read_parquet(
        MATCHING_ROOT / "consumer_summary.parquet"
    )
    generators = pd.read_parquet(
        MATCHING_ROOT / "generator_summary.parquet"
    )
    assert consumers["renewable_coverage"].between(0, 1).all()
    assert generators["offtake_coverage"].between(0, 1).all()
    assert len(consumers) == 8 * 2 * 2
    assert len(generators) == 4 * 2 * 2
    assert (
        consumers["residual_grid_demand_mwh"] >= 0
    ).all()
    assert (generators["unused_generation_mwh"] >= 0).all()
    summary_text = (MATCHING_ROOT / "summary.json").read_text(
        encoding="utf-8"
    )
    assert "NaN" not in summary_text
    summary = json.loads(summary_text)
    assert summary["conservation_passed"] is True
    assert summary["phase_7_reconciliation_passed"] is True
    assert "not physical electricity routing" in summary["interpretation"]
