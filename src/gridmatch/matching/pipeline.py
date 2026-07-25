"""Phase 8 forecast and realised renewable-matching artifact pipeline."""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gridmatch.matching.metrics import safe_ratio, weighted_average
from gridmatch.matching.optimizer import (
    SOLVER_TOLERANCE,
    AllocationResult,
    MatchParticipant,
    MatchingMode,
    solve_allocation,
)
from gridmatch.research.common import FIGURE_ROOT, research_style

MATCHING_VERSION = "renewable-matching-v1"
MATCHING_MODES: tuple[MatchingMode, ...] = (
    "maximum_match",
    "local_preference",
)
ALLOCATION_TYPES = ("forecast", "realised")
PROJECT_ROOT = Path(__file__).resolve().parents[3]

ALLOCATION_COLUMNS = [
    "timestamp_utc",
    "settlement_date",
    "settlement_period",
    "forecast_issue_time_utc",
    "allocation_type",
    "matching_mode",
    "generator_site_id",
    "consumer_site_id",
    "generator_name",
    "consumer_name",
    "generator_technology",
    "consumer_archetype",
    "generator_region",
    "consumer_region",
    "generator_latitude",
    "generator_longitude",
    "consumer_latitude",
    "consumer_longitude",
    "distance_km",
    "matched_mwh",
    "generator_available_mwh",
    "consumer_demand_mwh",
    "allocation_share_of_generator",
    "allocation_share_of_consumer",
    "allocation_score",
    "matching_version",
]


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_clean_json(value), indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _portable_path(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(
            PROJECT_ROOT.resolve()
        ).as_posix()
    except ValueError:
        return candidate.as_posix()


def _validate_inputs(
    site_forecasts: pd.DataFrame,
    portfolio_forecasts: pd.DataFrame,
    sites: pd.DataFrame,
) -> pd.DataFrame:
    required_site_columns = {
        "site_id",
        "site_role",
        "technology",
        "issue_time_utc",
        "valid_time_utc",
        "settlement_date",
        "settlement_period",
        "actual_mwh",
        "point_mwh",
        "validation_fold",
    }
    required_metadata_columns = {
        "site_id",
        "name",
        "business_archetype",
        "latitude",
        "longitude",
        "installed_capacity_mw",
        "region",
    }
    missing_forecast = required_site_columns - set(site_forecasts.columns)
    missing_metadata = required_metadata_columns - set(sites.columns)
    if missing_forecast:
        raise ValueError(
            f"Site forecasts missing columns: {sorted(missing_forecast)}"
        )
    if missing_metadata:
        raise ValueError(
            f"Site metadata missing columns: {sorted(missing_metadata)}"
        )
    period_keys = portfolio_forecasts[
        ["validation_fold", "valid_time_utc"]
    ].drop_duplicates()
    selected = site_forecasts.merge(
        period_keys,
        on=["validation_fold", "valid_time_utc"],
        how="inner",
        validate="many_to_one",
    )
    if selected.empty:
        raise ValueError("No Phase 6 forecasts overlap Phase 7 periods")
    selected_periods = selected[
        ["validation_fold", "valid_time_utc"]
    ].drop_duplicates()
    if len(selected_periods) != len(period_keys):
        raise ValueError(
            "Every Phase 7 portfolio period must exist in Phase 6 forecasts"
        )
    expected_sites = set(sites["site_id"])
    site_sets = selected.groupby(
        ["validation_fold", "valid_time_utc"]
    )["site_id"].agg(set)
    if not site_sets.map(lambda value: value == expected_sites).all():
        raise ValueError(
            "Every portfolio period must contain every configured site"
        )
    if selected[["actual_mwh", "point_mwh"]].isna().any().any():
        raise ValueError("Matching inputs cannot contain missing energy")
    if (selected[["actual_mwh", "point_mwh"]] < 0).any().any():
        raise ValueError("Matching inputs cannot contain negative energy")
    return selected.merge(
        sites[
            [
                "site_id",
                "name",
                "business_archetype",
                "latitude",
                "longitude",
                "installed_capacity_mw",
                "region",
            ]
        ],
        on="site_id",
        how="left",
        validate="many_to_one",
    )


def _participants(
    period: pd.DataFrame,
    allocation_type: str,
) -> tuple[list[MatchParticipant], list[MatchParticipant], str]:
    value_column = (
        "point_mwh" if allocation_type == "forecast" else "actual_mwh"
    )
    generators = []
    consumers = []
    for row in period.sort_values("site_id").itertuples(index=False):
        participant = MatchParticipant(
            site_id=str(row.site_id),
            available_mwh=float(getattr(row, value_column)),
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            region=str(row.region),
            technology=str(row.technology),
        )
        if row.site_role == "generation":
            generators.append(participant)
        elif row.site_role == "demand":
            consumers.append(participant)
        else:
            raise ValueError(f"Unknown site role: {row.site_role}")
    return generators, consumers, value_column


def _allocation_records(
    period: pd.DataFrame,
    result: AllocationResult,
    allocation_type: str,
    value_column: str,
) -> list[dict[str, Any]]:
    metadata = period.set_index("site_id").to_dict(orient="index")
    first = period.iloc[0]
    records = []
    for allocation in result.allocations:
        generator = metadata[allocation.generator_site_id]
        consumer = metadata[allocation.consumer_site_id]
        generator_available = float(generator[value_column])
        consumer_demand = float(consumer[value_column])
        records.append(
            {
                "timestamp_utc": first["valid_time_utc"],
                "settlement_date": str(first["settlement_date"]),
                "settlement_period": int(first["settlement_period"]),
                "forecast_issue_time_utc": first["issue_time_utc"],
                "allocation_type": allocation_type,
                "matching_mode": result.matching_mode,
                "generator_site_id": allocation.generator_site_id,
                "consumer_site_id": allocation.consumer_site_id,
                "generator_name": generator["name"],
                "consumer_name": consumer["name"],
                "generator_technology": generator["technology"],
                "consumer_archetype": consumer["business_archetype"],
                "generator_region": generator["region"],
                "consumer_region": consumer["region"],
                "generator_latitude": float(generator["latitude"]),
                "generator_longitude": float(generator["longitude"]),
                "consumer_latitude": float(consumer["latitude"]),
                "consumer_longitude": float(consumer["longitude"]),
                "distance_km": allocation.distance_km,
                "matched_mwh": allocation.matched_mwh,
                "generator_available_mwh": generator_available,
                "consumer_demand_mwh": consumer_demand,
                "allocation_share_of_generator": safe_ratio(
                    allocation.matched_mwh,
                    generator_available,
                ),
                "allocation_share_of_consumer": safe_ratio(
                    allocation.matched_mwh,
                    consumer_demand,
                ),
                "allocation_score": allocation.allocation_score,
                "matching_version": MATCHING_VERSION,
            }
        )
    return records


def _period_record(
    period: pd.DataFrame,
    result: AllocationResult,
    allocation_type: str,
) -> dict[str, Any]:
    first = period.iloc[0]
    matched = result.matched_mwh
    distances = np.array(
        [allocation.distance_km for allocation in result.allocations],
        dtype=float,
    )
    weights = np.array(
        [allocation.matched_mwh for allocation in result.allocations],
        dtype=float,
    )
    return {
        "timestamp_utc": first["valid_time_utc"],
        "settlement_date": str(first["settlement_date"]),
        "settlement_period": int(first["settlement_period"]),
        "forecast_issue_time_utc": first["issue_time_utc"],
        "validation_fold": int(first["validation_fold"]),
        "allocation_type": allocation_type,
        "matching_mode": result.matching_mode,
        "total_demand_mwh": result.total_demand_mwh,
        "total_generation_mwh": result.total_generation_mwh,
        "matched_mwh": matched,
        "residual_grid_demand_mwh": max(
            result.total_demand_mwh - matched,
            0.0,
        ),
        "unused_generation_mwh": max(
            result.total_generation_mwh - matched,
            0.0,
        ),
        "renewable_match_rate": safe_ratio(
            matched,
            result.total_demand_mwh,
        ),
        "average_match_distance_km": weighted_average(
            distances,
            weights,
        ),
        "forecast_or_actual": (
            "forecast" if allocation_type == "forecast" else "actual"
        ),
        "demand_constrained": bool(
            result.total_generation_mwh
            > result.total_demand_mwh + SOLVER_TOLERANCE
        ),
        "generation_constrained": bool(
            result.total_demand_mwh
            > result.total_generation_mwh + SOLVER_TOLERANCE
        ),
        "solver": result.solver,
        "matching_version": MATCHING_VERSION,
    }


def run_matching(
    site_forecasts: pd.DataFrame,
    portfolio_forecasts: pd.DataFrame,
    sites: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Solve forecast and realised allocations for every portfolio period."""
    inputs = _validate_inputs(site_forecasts, portfolio_forecasts, sites)
    allocations: list[dict[str, Any]] = []
    periods: list[dict[str, Any]] = []
    group_columns = ["validation_fold", "valid_time_utc"]
    for _, period in inputs.groupby(group_columns, sort=True):
        for allocation_type in ALLOCATION_TYPES:
            generators, consumers, value_column = _participants(
                period,
                allocation_type,
            )
            for mode in MATCHING_MODES:
                result = solve_allocation(
                    generators,
                    consumers,
                    mode=mode,
                )
                allocations.extend(
                    _allocation_records(
                        period,
                        result,
                        allocation_type,
                        value_column,
                    )
                )
                periods.append(
                    _period_record(period, result, allocation_type)
                )
    allocation_frame = pd.DataFrame(
        allocations,
        columns=ALLOCATION_COLUMNS,
    ).sort_values(
        [
            "allocation_type",
            "matching_mode",
            "timestamp_utc",
            "generator_site_id",
            "consumer_site_id",
        ]
    ).reset_index(drop=True)
    period_frame = pd.DataFrame(periods).sort_values(
        ["allocation_type", "matching_mode", "timestamp_utc"]
    ).reset_index(drop=True)
    return allocation_frame, period_frame


def _site_summaries(
    allocations: pd.DataFrame,
    periods: pd.DataFrame,
    inputs: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source_rows = []
    for allocation_type in ALLOCATION_TYPES:
        value_column = (
            "point_mwh" if allocation_type == "forecast" else "actual_mwh"
        )
        totals = (
            inputs.groupby(["site_id", "site_role"], as_index=False)[
                value_column
            ]
            .sum()
            .rename(columns={value_column: "available_mwh"})
        )
        totals["allocation_type"] = allocation_type
        source_rows.append(totals)
    source_totals = pd.concat(source_rows, ignore_index=True)

    consumer_rows = []
    generator_rows = []
    for allocation_type in ALLOCATION_TYPES:
        for mode in MATCHING_MODES:
            selected = allocations[
                (allocations["allocation_type"] == allocation_type)
                & (allocations["matching_mode"] == mode)
            ]
            consumer_allocations = selected.groupby(
                "consumer_site_id",
                as_index=False,
            ).agg(
                matched_renewable_mwh=("matched_mwh", "sum"),
                number_of_generators=("generator_site_id", "nunique"),
            )
            generator_allocations = selected.groupby(
                "generator_site_id",
                as_index=False,
            ).agg(
                matched_generation_mwh=("matched_mwh", "sum"),
                number_of_consumers=("consumer_site_id", "nunique"),
            )
            consumer_distance = (
                selected.groupby("consumer_site_id")
                .apply(
                    lambda group: weighted_average(
                        group["distance_km"].to_numpy(),
                        group["matched_mwh"].to_numpy(),
                    ),
                    include_groups=False,
                )
                .rename("weighted_average_distance_km")
                .reset_index()
            )
            generator_distance = (
                selected.groupby("generator_site_id")
                .apply(
                    lambda group: weighted_average(
                        group["distance_km"].to_numpy(),
                        group["matched_mwh"].to_numpy(),
                    ),
                    include_groups=False,
                )
                .rename("weighted_average_distance_km")
                .reset_index()
            )
            consumer_base = source_totals[
                (source_totals["allocation_type"] == allocation_type)
                & (source_totals["site_role"] == "demand")
            ][["site_id", "available_mwh"]].rename(
                columns={
                    "site_id": "consumer_site_id",
                    "available_mwh": "consumer_demand_mwh",
                }
            )
            consumer = (
                consumer_base.merge(
                    consumer_allocations,
                    on="consumer_site_id",
                    how="left",
                )
                .merge(
                    consumer_distance,
                    on="consumer_site_id",
                    how="left",
                )
                .fillna(0)
            )
            consumer["residual_grid_demand_mwh"] = (
                consumer["consumer_demand_mwh"]
                - consumer["matched_renewable_mwh"]
            ).clip(lower=0)
            consumer["renewable_coverage"] = consumer.apply(
                lambda row: safe_ratio(
                    row["matched_renewable_mwh"],
                    row["consumer_demand_mwh"],
                ),
                axis=1,
            )
            consumer["allocation_type"] = allocation_type
            consumer["matching_mode"] = mode
            consumer_rows.append(consumer)

            generator_base = source_totals[
                (source_totals["allocation_type"] == allocation_type)
                & (source_totals["site_role"] == "generation")
            ][["site_id", "available_mwh"]].rename(
                columns={
                    "site_id": "generator_site_id",
                    "available_mwh": "available_generation_mwh",
                }
            )
            generator = (
                generator_base.merge(
                    generator_allocations,
                    on="generator_site_id",
                    how="left",
                )
                .merge(
                    generator_distance,
                    on="generator_site_id",
                    how="left",
                )
                .fillna(0)
            )
            generator["unused_generation_mwh"] = (
                generator["available_generation_mwh"]
                - generator["matched_generation_mwh"]
            ).clip(lower=0)
            generator["offtake_coverage"] = generator.apply(
                lambda row: safe_ratio(
                    row["matched_generation_mwh"],
                    row["available_generation_mwh"],
                ),
                axis=1,
            )
            generator["allocation_type"] = allocation_type
            generator["matching_mode"] = mode
            generator_rows.append(generator)
    consumers = pd.concat(consumer_rows, ignore_index=True)
    generators = pd.concat(generator_rows, ignore_index=True)
    return consumers, generators


def _comparison(periods: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "timestamp_utc",
        "settlement_date",
        "settlement_period",
        "matching_mode",
    ]
    measures = [
        "total_demand_mwh",
        "total_generation_mwh",
        "matched_mwh",
        "residual_grid_demand_mwh",
        "unused_generation_mwh",
        "renewable_match_rate",
        "average_match_distance_km",
    ]
    forecast = periods[periods["allocation_type"] == "forecast"][
        keys + measures
    ].rename(columns={column: f"forecast_{column}" for column in measures})
    realised = periods[periods["allocation_type"] == "realised"][
        keys + measures
    ].rename(columns={column: f"realised_{column}" for column in measures})
    comparison = forecast.merge(
        realised,
        on=keys,
        how="outer",
        validate="one_to_one",
    )
    comparison["allocation_error_mwh"] = (
        comparison["realised_matched_mwh"]
        - comparison["forecast_matched_mwh"]
    )
    comparison["absolute_allocation_error_mwh"] = comparison[
        "allocation_error_mwh"
    ].abs()
    return comparison.sort_values(
        ["matching_mode", "timestamp_utc"]
    ).reset_index(drop=True)


def _map_arcs(allocations: pd.DataFrame) -> pd.DataFrame:
    return allocations[
        [
            "timestamp_utc",
            "settlement_period",
            "matching_mode",
            "generator_site_id",
            "consumer_site_id",
            "generator_latitude",
            "generator_longitude",
            "consumer_latitude",
            "consumer_longitude",
            "matched_mwh",
            "distance_km",
            "generator_technology",
            "allocation_type",
            "allocation_score",
        ]
    ].rename(
        columns={
            "generator_latitude": "start_latitude",
            "generator_longitude": "start_longitude",
            "consumer_latitude": "end_latitude",
            "consumer_longitude": "end_longitude",
            "generator_technology": "technology",
        }
    )


def _assert_conservation(
    allocations: pd.DataFrame,
    periods: pd.DataFrame,
) -> None:
    tolerance = 1e-7
    if (allocations["matched_mwh"] < -tolerance).any():
        raise AssertionError("Negative allocation detected")
    if (periods["matched_mwh"] > periods["total_demand_mwh"] + tolerance).any():
        raise AssertionError("Portfolio demand over-allocation detected")
    if (
        periods["matched_mwh"]
        > periods["total_generation_mwh"] + tolerance
    ).any():
        raise AssertionError("Portfolio generation over-allocation detected")
    expected = periods[
        ["total_demand_mwh", "total_generation_mwh"]
    ].min(axis=1)
    if not np.allclose(periods["matched_mwh"], expected, atol=tolerance):
        raise AssertionError("Maximum feasible matching was not achieved")
    group_keys = [
        "timestamp_utc",
        "allocation_type",
        "matching_mode",
    ]
    generator = allocations.groupby(
        group_keys + ["generator_site_id"]
    ).agg(
        allocated=("matched_mwh", "sum"),
        available=("generator_available_mwh", "first"),
    )
    consumer = allocations.groupby(
        group_keys + ["consumer_site_id"]
    ).agg(
        allocated=("matched_mwh", "sum"),
        demand=("consumer_demand_mwh", "first"),
    )
    if (generator["allocated"] > generator["available"] + tolerance).any():
        raise AssertionError("Generator over-allocation detected")
    if (consumer["allocated"] > consumer["demand"] + tolerance).any():
        raise AssertionError("Consumer over-allocation detected")


def _assert_portfolio_reconciliation(
    periods: pd.DataFrame,
    portfolio: pd.DataFrame,
) -> None:
    columns = [
        "valid_time_utc",
        "actual_demand_mwh",
        "actual_generation_mwh",
        "bottom_up_demand_point_mwh",
        "bottom_up_generation_point_mwh",
    ]
    reference = portfolio[columns].rename(
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


def _create_figures(
    periods: pd.DataFrame,
    consumers: pd.DataFrame,
    generators: pd.DataFrame,
    allocations: pd.DataFrame,
    figure_root: Path,
) -> dict[str, str]:
    research_style()
    figure_root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    selected = periods[periods["matching_mode"] == "local_preference"].copy()
    selected["date"] = pd.to_datetime(selected["timestamp_utc"]).dt.floor("D")
    daily = selected.groupby(["date", "allocation_type"], as_index=False)[
        "renewable_match_rate"
    ].mean()
    fig, axis = plt.subplots(figsize=(11, 5))
    for allocation_type, group in daily.groupby("allocation_type"):
        axis.plot(
            group["date"],
            group["renewable_match_rate"] * 100,
            label=allocation_type.title(),
            linewidth=1.7,
        )
    axis.set(
        title="Commercial renewable matching over time",
        ylabel="Mean renewable coverage (%)",
        xlabel="Delivery date (UTC)",
    )
    axis.legend()
    fig.tight_layout()
    path = figure_root / "renewable_matching_over_time.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["renewable_matching_over_time"] = path.as_posix()

    consumer = consumers[
        (consumers["matching_mode"] == "local_preference")
        & (consumers["allocation_type"] == "realised")
    ].sort_values("renewable_coverage")
    fig, axis = plt.subplots(figsize=(10, 5.5))
    axis.barh(
        consumer["consumer_site_id"].str.replace("dem_", "", regex=False),
        consumer["renewable_coverage"] * 100,
        color="#277da1",
    )
    axis.set(
        title="Realised renewable coverage by consumer",
        xlabel="Renewable coverage (%)",
    )
    fig.tight_layout()
    path = figure_root / "consumer_renewable_coverage.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["consumer_renewable_coverage"] = path.as_posix()

    generator = generators[
        (generators["matching_mode"] == "local_preference")
        & (generators["allocation_type"] == "realised")
    ].sort_values("offtake_coverage")
    fig, axis = plt.subplots(figsize=(10, 4.5))
    axis.barh(
        generator["generator_site_id"].str.replace("gen_", "", regex=False),
        generator["offtake_coverage"] * 100,
        color="#43aa8b",
    )
    axis.set(
        title="Realised offtake coverage by generator",
        xlabel="Offtake coverage (%)",
    )
    fig.tight_layout()
    path = figure_root / "generator_offtake_coverage.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["generator_offtake_coverage"] = path.as_posix()

    distance = allocations[
        (allocations["matching_mode"] == "local_preference")
        & (allocations["allocation_type"] == "realised")
    ]
    fig, axis = plt.subplots(figsize=(10, 5))
    axis.hist(
        distance["distance_km"],
        weights=distance["matched_mwh"],
        bins=18,
        color="#f8961e",
        edgecolor="white",
    )
    axis.set(
        title="Matched-energy distance preference distribution",
        xlabel="Great-circle distance (km)",
        ylabel="Matched MWh",
    )
    fig.tight_layout()
    path = figure_root / "matching_distance_distribution.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["matching_distance_distribution"] = path.as_posix()
    return paths


def _analysis_summary(
    periods: pd.DataFrame,
    consumers: pd.DataFrame,
    generators: pd.DataFrame,
    comparison: pd.DataFrame,
) -> dict[str, Any]:
    local_periods = periods[
        periods["matching_mode"] == "local_preference"
    ]
    forecast = local_periods[
        local_periods["allocation_type"] == "forecast"
    ]
    realised = local_periods[
        local_periods["allocation_type"] == "realised"
    ]
    local_consumers = consumers[
        (consumers["matching_mode"] == "local_preference")
        & (consumers["allocation_type"] == "realised")
    ]
    local_generators = generators[
        (generators["matching_mode"] == "local_preference")
        & (generators["allocation_type"] == "realised")
    ]
    consumer_high = local_consumers.loc[
        local_consumers["renewable_coverage"].idxmax()
    ]
    consumer_low = local_consumers.loc[
        local_consumers["renewable_coverage"].idxmin()
    ]
    generator_high = local_generators.loc[
        local_generators["offtake_coverage"].idxmax()
    ]
    generator_low = local_generators.loc[
        local_generators["offtake_coverage"].idxmin()
    ]
    local_comparison = comparison[
        comparison["matching_mode"] == "local_preference"
    ]
    return {
        "average_forecast_renewable_match_rate": float(
            forecast["renewable_match_rate"].mean()
        ),
        "average_realised_renewable_match_rate": float(
            realised["renewable_match_rate"].mean()
        ),
        "total_realised_residual_grid_requirement_mwh": float(
            realised["residual_grid_demand_mwh"].sum()
        ),
        "total_realised_unused_generation_mwh": float(
            realised["unused_generation_mwh"].sum()
        ),
        "highest_consumer_renewable_coverage": {
            "site_id": consumer_high["consumer_site_id"],
            "coverage": consumer_high["renewable_coverage"],
        },
        "lowest_consumer_renewable_coverage": {
            "site_id": consumer_low["consumer_site_id"],
            "coverage": consumer_low["renewable_coverage"],
        },
        "highest_generator_offtake_coverage": {
            "site_id": generator_high["generator_site_id"],
            "coverage": generator_high["offtake_coverage"],
        },
        "lowest_generator_offtake_coverage": {
            "site_id": generator_low["generator_site_id"],
            "coverage": generator_low["offtake_coverage"],
        },
        "average_realised_matching_distance_km": weighted_average(
            realised["average_match_distance_km"].to_numpy(),
            realised["matched_mwh"].to_numpy(),
        ),
        "forecast_demand_constrained_periods": int(
            forecast["demand_constrained"].sum()
        ),
        "forecast_generation_constrained_periods": int(
            forecast["generation_constrained"].sum()
        ),
        "realised_demand_constrained_periods": int(
            realised["demand_constrained"].sum()
        ),
        "realised_generation_constrained_periods": int(
            realised["generation_constrained"].sum()
        ),
        "zero_forecast_generation_periods": int(
            (forecast["total_generation_mwh"] <= SOLVER_TOLERANCE).sum()
        ),
        "zero_realised_generation_periods": int(
            (realised["total_generation_mwh"] <= SOLVER_TOLERANCE).sum()
        ),
        "mean_planned_vs_realised_matching_difference_mwh": float(
            local_comparison["allocation_error_mwh"].mean()
        ),
        "total_planned_vs_realised_matching_difference_mwh": float(
            local_comparison["allocation_error_mwh"].sum()
        ),
    }


def build_matching_allocations(
    *,
    site_forecasts_path: Path | str = (
        PROJECT_ROOT / "artifacts/forecasts/site_forecasts.parquet"
    ),
    portfolio_forecasts_path: Path | str = (
        PROJECT_ROOT / "artifacts/forecasts/portfolio_forecasts.parquet"
    ),
    sites_path: Path | str = PROJECT_ROOT / "data/demo/sites.parquet",
    output_root: Path | str = PROJECT_ROOT / "artifacts/matching",
    figure_root: Path | str = FIGURE_ROOT,
) -> dict[str, Any]:
    """Build all Phase 8 allocations, summaries, comparisons and figures."""
    site_forecasts = pd.read_parquet(site_forecasts_path)
    portfolio_forecasts = pd.read_parquet(portfolio_forecasts_path)
    sites = pd.read_parquet(sites_path)
    inputs = _validate_inputs(site_forecasts, portfolio_forecasts, sites)
    allocations, periods = run_matching(
        site_forecasts,
        portfolio_forecasts,
        sites,
    )
    _assert_conservation(allocations, periods)
    _assert_portfolio_reconciliation(periods, portfolio_forecasts)
    consumers, generators = _site_summaries(
        allocations,
        periods,
        inputs,
    )
    comparison = _comparison(periods)
    arcs = _map_arcs(allocations)
    destination = Path(output_root)
    destination.mkdir(parents=True, exist_ok=True)
    paths = {
        "forecast_allocations": (
            destination / "forecast_allocations.parquet"
        ),
        "realised_allocations": (
            destination / "realised_allocations.parquet"
        ),
        "period_summary": destination / "period_summary.parquet",
        "consumer_summary": destination / "consumer_summary.parquet",
        "generator_summary": destination / "generator_summary.parquet",
        "allocation_comparison": (
            destination / "allocation_comparison.parquet"
        ),
        "map_arcs": destination / "map_arcs.parquet",
        "summary": destination / "summary.json",
    }
    allocations[
        allocations["allocation_type"] == "forecast"
    ].to_parquet(paths["forecast_allocations"], index=False)
    allocations[
        allocations["allocation_type"] == "realised"
    ].to_parquet(paths["realised_allocations"], index=False)
    periods.to_parquet(paths["period_summary"], index=False)
    consumers.to_parquet(paths["consumer_summary"], index=False)
    generators.to_parquet(paths["generator_summary"], index=False)
    comparison.to_parquet(paths["allocation_comparison"], index=False)
    arcs.to_parquet(paths["map_arcs"], index=False)
    figure_paths = _create_figures(
        periods,
        consumers,
        generators,
        allocations,
        Path(figure_root),
    )
    analysis = _analysis_summary(
        periods,
        consumers,
        generators,
        comparison,
    )
    summary = {
        "matching_version": MATCHING_VERSION,
        "interpretation": (
            "Commercial/accounting renewable allocation; not physical "
            "electricity routing through the grid."
        ),
        "solver": sorted(periods["solver"].unique().tolist()),
        "matching_modes": list(MATCHING_MODES),
        "settlement_periods": int(
            periods["timestamp_utc"].nunique()
        ),
        "forecast_allocation_rows": int(
            (allocations["allocation_type"] == "forecast").sum()
        ),
        "realised_allocation_rows": int(
            (allocations["allocation_type"] == "realised").sum()
        ),
        "period_summary_rows": len(periods),
        "map_arc_rows": len(arcs),
        "conservation_passed": True,
        "phase_7_reconciliation_passed": True,
        "analysis_basis": "local_preference",
        "analysis": analysis,
        "artifacts": {
            key: _portable_path(path) for key, path in paths.items()
        },
        "figures": {
            key: _portable_path(path)
            for key, path in figure_paths.items()
        },
        "limitations": [
            "Inputs are simulated out-of-sample prototype observations and forecasts.",
            "Distance is only a commercial preference, not evidence of local physical flow.",
            "The model omits contracts, prices, REGOs, supplier rules and network constraints.",
            "No financial savings or hedge decisions are calculated.",
        ],
    }
    _write_json(paths["summary"], summary)
    return summary
