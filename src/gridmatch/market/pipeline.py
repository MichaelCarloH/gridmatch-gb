"""Phase 9 leakage-aware hedge-policy backtest and artifacts."""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gridmatch.market.hedging import (
    evaluate_hedge_cost,
    expected_exposures,
    implied_optimal_quantile,
    interpolate_forecast_quantile,
)
from gridmatch.market.prices import (
    PRICE_ALIGNMENT,
    PriceAssumptions,
    public_price_curve,
)
from gridmatch.research.common import FIGURE_ROOT, research_style

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HEDGE_MODEL_VERSION = "hedge-decision-v1"
DEFAULT_FORECAST_MODEL = "bottom_up"
QUANTILE_GRID = tuple(round(value, 1) for value in np.arange(0.1, 1.0, 0.1))
POLICY_QUANTILES = {
    "q50": 0.5,
    "q60": 0.6,
    "q70": 0.7,
    "q80": 0.8,
}
POLICIES = (
    "no_hedge",
    "q50",
    "q60",
    "q70",
    "q80",
    "validation_optimised",
    "perfect_foresight",
)


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


def _quantile_columns(forecast_model: str) -> tuple[str, str, str]:
    return (
        f"{forecast_model}_net_q10_mwh",
        f"{forecast_model}_net_q50_mwh",
        f"{forecast_model}_net_q90_mwh",
    )


def _prepare_inputs(
    portfolio_forecasts: pd.DataFrame,
    prices: pd.DataFrame,
    assumptions: PriceAssumptions,
    forecast_model: str,
) -> pd.DataFrame:
    q10_column, q50_column, q90_column = _quantile_columns(forecast_model)
    required = {
        "validation_fold",
        "issue_time_utc",
        "valid_time_utc",
        "settlement_date",
        "settlement_period",
        "training_cutoff_utc",
        "actual_net_mwh",
        q10_column,
        q50_column,
        q90_column,
    }
    missing = required - set(portfolio_forecasts.columns)
    if missing:
        raise ValueError(
            f"Portfolio forecasts missing columns: {sorted(missing)}"
        )
    frame = portfolio_forecasts.copy()
    if frame[list(_quantile_columns(forecast_model))].isna().any().any():
        raise ValueError("Hedge forecast quantiles cannot be missing")
    if not (
        (frame[q10_column] <= frame[q50_column])
        & (frame[q50_column] <= frame[q90_column])
    ).all():
        raise ValueError("Hedge forecast quantiles must be ordered")
    if not (
        frame["training_cutoff_utc"] <= frame["issue_time_utc"]
    ).all():
        raise ValueError("Forecast training cutoff exceeds issue time")
    if not (frame["issue_time_utc"] < frame["valid_time_utc"]).all():
        raise ValueError("Forecast issue time must precede delivery")
    curve = public_price_curve(
        prices,
        frame["settlement_period"],
        assumptions=assumptions,
    )
    frame = frame.merge(
        curve,
        on="settlement_period",
        how="left",
        validate="many_to_one",
    )
    if frame[
        [
            "market_reference_price_gbp_mwh",
            "public_system_price_gbp_mwh",
            "short_price_gbp_mwh",
            "long_price_gbp_mwh",
        ]
    ].isna().any().any():
        raise ValueError("Every forecast period requires a price reference")
    frame["forecast_model"] = forecast_model
    return frame.sort_values(
        ["validation_fold", "valid_time_utc"]
    ).reset_index(drop=True)


def _candidate_cost(
    frame: pd.DataFrame,
    quantile: float,
    forecast_model: str,
) -> float:
    q10_column, q50_column, q90_column = _quantile_columns(forecast_model)
    hedge = interpolate_forecast_quantile(
        frame[q10_column].to_numpy(),
        frame[q50_column].to_numpy(),
        frame[q90_column].to_numpy(),
        quantile,
    )
    realised = frame["actual_net_mwh"].to_numpy()
    short = np.maximum(realised - hedge, 0)
    long = np.maximum(hedge - realised, 0)
    cost = (
        hedge * frame["market_reference_price_gbp_mwh"].to_numpy()
        + short * frame["short_price_gbp_mwh"].to_numpy()
        - long * frame["long_price_gbp_mwh"].to_numpy()
    )
    return float(cost.sum())


def select_validation_quantiles(
    frame: pd.DataFrame,
    forecast_model: str = DEFAULT_FORECAST_MODEL,
) -> tuple[dict[int, float], list[dict[str, Any]]]:
    """Select each fold's quantile using only outcomes known by issue time."""
    selected: dict[int, float] = {}
    history: list[dict[str, Any]] = []
    folds = sorted(int(value) for value in frame["validation_fold"].unique())
    for fold in folds:
        current = frame[frame["validation_fold"] == fold]
        earliest_issue = current["issue_time_utc"].min()
        evidence = frame[
            (frame["validation_fold"] < fold)
            & (frame["valid_time_utc"] < earliest_issue)
        ]
        candidate_costs: dict[str, float] = {}
        if evidence.empty:
            implied = np.median(
                [
                    implied_optimal_quantile(
                        row.market_reference_price_gbp_mwh,
                        row.short_price_gbp_mwh,
                        row.long_price_gbp_mwh,
                    )
                    for row in current.itertuples(index=False)
                ]
            )
            quantile = min(
                QUANTILE_GRID,
                key=lambda candidate: (abs(candidate - implied), candidate),
            )
            source = "asymmetric_cost_ratio_default"
        else:
            candidate_costs = {
                f"q{int(candidate * 100):02d}": _candidate_cost(
                    evidence,
                    candidate,
                    forecast_model,
                )
                for candidate in QUANTILE_GRID
            }
            quantile = min(
                QUANTILE_GRID,
                key=lambda candidate: (
                    candidate_costs[f"q{int(candidate * 100):02d}"],
                    candidate,
                ),
            )
            source = "prior_fold_realised_cost"
        selected[fold] = float(quantile)
        history.append(
            {
                "validation_fold": fold,
                "selected_quantile": quantile,
                "selection_source": source,
                "current_fold_earliest_issue_time_utc": earliest_issue,
                "evidence_rows": len(evidence),
                "evidence_start_utc": (
                    evidence["valid_time_utc"].min()
                    if not evidence.empty
                    else None
                ),
                "evidence_end_utc": (
                    evidence["valid_time_utc"].max()
                    if not evidence.empty
                    else None
                ),
                "candidate_total_cost_gbp": candidate_costs,
            }
        )
    return selected, history


def _policy_volume(
    row: Any,
    policy: str,
    selected_quantile: float,
    forecast_model: str,
) -> tuple[float, float | None]:
    q10 = float(getattr(row, f"{forecast_model}_net_q10_mwh"))
    q50 = float(getattr(row, f"{forecast_model}_net_q50_mwh"))
    q90 = float(getattr(row, f"{forecast_model}_net_q90_mwh"))
    if policy == "no_hedge":
        return 0.0, None
    if policy == "perfect_foresight":
        return float(row.actual_net_mwh), None
    quantile = (
        selected_quantile
        if policy == "validation_optimised"
        else POLICY_QUANTILES[policy]
    )
    volume = interpolate_forecast_quantile(
        q10,
        q50,
        q90,
        quantile,
    ).item()
    return float(volume), float(quantile)


def evaluate_policies(
    frame: pd.DataFrame,
    selected_quantiles: dict[int, float],
    forecast_model: str = DEFAULT_FORECAST_MODEL,
) -> pd.DataFrame:
    """Evaluate every policy on out-of-sample realised net demand."""
    rows = []
    for row in frame.itertuples(index=False):
        selected_quantile = selected_quantiles[int(row.validation_fold)]
        for policy in POLICIES:
            volume, policy_quantile = _policy_volume(
                row,
                policy,
                selected_quantile,
                forecast_model,
            )
            cost = evaluate_hedge_cost(
                realised_net_demand_mwh=float(row.actual_net_mwh),
                hedged_volume_mwh=volume,
                market_reference_price_gbp_mwh=float(
                    row.market_reference_price_gbp_mwh
                ),
                short_price_gbp_mwh=float(row.short_price_gbp_mwh),
                long_price_gbp_mwh=float(row.long_price_gbp_mwh),
            )
            rows.append(
                {
                    "timestamp_utc": row.valid_time_utc,
                    "settlement_date": str(row.settlement_date),
                    "settlement_period": int(row.settlement_period),
                    "forecast_issue_time_utc": row.issue_time_utc,
                    "training_cutoff_utc": row.training_cutoff_utc,
                    "validation_fold": int(row.validation_fold),
                    "forecast_model": forecast_model,
                    "policy": policy,
                    "policy_quantile": policy_quantile,
                    "hedged_volume_mwh": volume,
                    "realised_net_demand_mwh": float(row.actual_net_mwh),
                    "short_exposure_mwh": cost.short_exposure_mwh,
                    "long_exposure_mwh": cost.long_exposure_mwh,
                    "day_ahead_cost_gbp": cost.day_ahead_cost_gbp,
                    "imbalance_cost_gbp": cost.imbalance_cost_gbp,
                    "total_cost_gbp": cost.total_cost_gbp,
                    "market_reference_price_gbp_mwh": float(
                        row.market_reference_price_gbp_mwh
                    ),
                    "public_system_price_gbp_mwh": float(
                        row.public_system_price_gbp_mwh
                    ),
                    "short_price_gbp_mwh": float(
                        row.short_price_gbp_mwh
                    ),
                    "long_price_gbp_mwh": float(
                        row.long_price_gbp_mwh
                    ),
                    "short_cost_multiplier": float(
                        row.short_cost_multiplier
                    ),
                    "long_value_multiplier": float(
                        row.long_value_multiplier
                    ),
                    "uses_realised_information": (
                        policy == "perfect_foresight"
                    ),
                    "eligible_recommendation": (
                        policy != "perfect_foresight"
                    ),
                    "price_data_origin": row.price_data_origin,
                    "price_alignment_method": row.price_alignment_method,
                    "hedge_model_version": HEDGE_MODEL_VERSION,
                }
            )
    result = pd.DataFrame(rows)
    _assert_perfect_foresight_lower_bound(result)
    return result.sort_values(
        ["policy", "timestamp_utc"]
    ).reset_index(drop=True)


def _assert_perfect_foresight_lower_bound(backtest: pd.DataFrame) -> None:
    perfect = backtest[backtest["policy"] == "perfect_foresight"][
        ["timestamp_utc", "total_cost_gbp"]
    ].rename(columns={"total_cost_gbp": "perfect_cost_gbp"})
    comparison = backtest.merge(
        perfect,
        on="timestamp_utc",
        how="left",
        validate="many_to_one",
    )
    if (
        comparison["perfect_cost_gbp"]
        > comparison["total_cost_gbp"] + 1e-7
    ).any():
        raise AssertionError("Perfect foresight must remain a lower bound")


def recommendation_frame(
    frame: pd.DataFrame,
    backtest: pd.DataFrame,
    selection_history: list[dict[str, Any]],
    forecast_model: str = DEFAULT_FORECAST_MODEL,
) -> pd.DataFrame:
    """Build one auditable, pre-delivery recommendation per forecast period."""
    selected = backtest[
        backtest["policy"] == "validation_optimised"
    ].copy()
    q10_column, q50_column, q90_column = _quantile_columns(forecast_model)
    forecast_columns = [
        "valid_time_utc",
        q10_column,
        q50_column,
        q90_column,
    ]
    selected = selected.merge(
        frame[forecast_columns],
        left_on="timestamp_utc",
        right_on="valid_time_utc",
        how="left",
        validate="one_to_one",
    )
    source_by_fold = {
        int(record["validation_fold"]): record["selection_source"]
        for record in selection_history
    }
    evidence_end_by_fold = {
        int(record["validation_fold"]): record["evidence_end_utc"]
        for record in selection_history
    }
    expected = selected.apply(
        lambda row: expected_exposures(
            float(row[q10_column]),
            float(row[q50_column]),
            float(row[q90_column]),
            float(row["hedged_volume_mwh"]),
        ),
        axis=1,
        result_type="expand",
    )
    selected["expected_short_exposure_mwh"] = expected[0]
    selected["expected_long_exposure_mwh"] = expected[1]
    selected["recommended_quantile"] = selected["policy_quantile"]
    selected["recommended_mwh"] = selected["hedged_volume_mwh"]
    selected["selection_source"] = selected["validation_fold"].map(
        source_by_fold
    )
    selected["selection_evidence_end_utc"] = selected[
        "validation_fold"
    ].map(evidence_end_by_fold)
    selected["risk_preference"] = 0.0
    selected["perfect_foresight_is_benchmark_only"] = True
    return selected[
        [
            "timestamp_utc",
            "settlement_date",
            "settlement_period",
            "forecast_issue_time_utc",
            "training_cutoff_utc",
            "validation_fold",
            "forecast_model",
            q10_column,
            q50_column,
            q90_column,
            "recommended_quantile",
            "recommended_mwh",
            "expected_short_exposure_mwh",
            "expected_long_exposure_mwh",
            "realised_net_demand_mwh",
            "short_exposure_mwh",
            "long_exposure_mwh",
            "day_ahead_cost_gbp",
            "imbalance_cost_gbp",
            "total_cost_gbp",
            "market_reference_price_gbp_mwh",
            "public_system_price_gbp_mwh",
            "short_price_gbp_mwh",
            "long_price_gbp_mwh",
            "short_cost_multiplier",
            "long_value_multiplier",
            "risk_preference",
            "selection_source",
            "selection_evidence_end_utc",
            "price_data_origin",
            "price_alignment_method",
            "perfect_foresight_is_benchmark_only",
            "hedge_model_version",
        ]
    ].sort_values("timestamp_utc").reset_index(drop=True)


def _risk_metrics(costs: pd.Series) -> dict[str, float]:
    threshold = float(costs.quantile(0.95))
    tail = costs[costs >= threshold]
    return {
        "mean_period_cost_gbp": float(costs.mean()),
        "cost_standard_deviation_gbp": float(costs.std(ddof=0)),
        "p95_period_cost_gbp": threshold,
        "cvar95_period_cost_gbp": float(tail.mean()),
        "worst_period_cost_gbp": float(costs.max()),
    }


def policy_metrics(backtest: pd.DataFrame) -> list[dict[str, Any]]:
    """Aggregate policy cost, exposure and risk distribution metrics."""
    no_hedge_total = float(
        backtest[backtest["policy"] == "no_hedge"][
            "total_cost_gbp"
        ].sum()
    )
    rows = []
    for policy, group in backtest.groupby("policy", sort=False):
        total_cost = float(group["total_cost_gbp"].sum())
        rows.append(
            {
                "policy": policy,
                "periods": len(group),
                "total_cost_gbp": total_cost,
                "cost_difference_vs_no_hedge_gbp": (
                    total_cost - no_hedge_total
                ),
                "total_short_exposure_mwh": float(
                    group["short_exposure_mwh"].sum()
                ),
                "total_long_exposure_mwh": float(
                    group["long_exposure_mwh"].sum()
                ),
                "mean_hedged_volume_mwh": float(
                    group["hedged_volume_mwh"].mean()
                ),
                "perfect_foresight_lower_bound": (
                    policy == "perfect_foresight"
                ),
                **_risk_metrics(group["total_cost_gbp"]),
            }
        )
    return sorted(rows, key=lambda row: row["total_cost_gbp"])


def _sensitivity(
    frame: pd.DataFrame,
    prices: pd.DataFrame,
    forecast_model: str,
) -> pd.DataFrame:
    rows = []
    q10_column, q50_column, q90_column = _quantile_columns(forecast_model)
    for short_multiplier in (1.15, 1.35, 1.75):
        for long_multiplier in (0.4, 0.65, 0.85):
            assumptions = PriceAssumptions(
                short_cost_multiplier=short_multiplier,
                long_value_multiplier=long_multiplier,
            )
            curve = public_price_curve(
                prices,
                frame["settlement_period"],
                assumptions=assumptions,
            )
            scenario = frame.drop(
                columns=[
                    column
                    for column in curve.columns
                    if column != "settlement_period"
                    and column in frame.columns
                ]
            ).merge(
                curve,
                on="settlement_period",
                how="left",
                validate="many_to_one",
            )
            quantiles = np.array(
                [
                    implied_optimal_quantile(
                        row.market_reference_price_gbp_mwh,
                        row.short_price_gbp_mwh,
                        row.long_price_gbp_mwh,
                    )
                    for row in scenario.itertuples(index=False)
                ]
            )
            hedges = np.array(
                [
                    interpolate_forecast_quantile(
                        q10,
                        q50,
                        q90,
                        quantile,
                    ).item()
                    for q10, q50, q90, quantile in zip(
                        scenario[q10_column],
                        scenario[q50_column],
                        scenario[q90_column],
                        quantiles,
                        strict=True,
                    )
                ]
            )
            realised = scenario["actual_net_mwh"].to_numpy()
            short = np.maximum(realised - hedges, 0)
            long = np.maximum(hedges - realised, 0)
            costs = (
                hedges
                * scenario["market_reference_price_gbp_mwh"].to_numpy()
                + short * scenario["short_price_gbp_mwh"].to_numpy()
                - long * scenario["long_price_gbp_mwh"].to_numpy()
            )
            rows.append(
                {
                    "short_cost_multiplier": short_multiplier,
                    "long_value_multiplier": long_multiplier,
                    "mean_recommended_quantile": float(quantiles.mean()),
                    "total_scenario_cost_gbp": float(costs.sum()),
                    "total_short_exposure_mwh": float(short.sum()),
                    "total_long_exposure_mwh": float(long.sum()),
                    "forecast_model": forecast_model,
                    "price_alignment_method": PRICE_ALIGNMENT,
                }
            )
    return pd.DataFrame(rows)


def _create_figures(
    recommendations: pd.DataFrame,
    backtest: pd.DataFrame,
    metrics: list[dict[str, Any]],
    sensitivity: pd.DataFrame,
    figure_root: Path,
) -> dict[str, str]:
    research_style()
    figure_root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    metric_frame = pd.DataFrame(metrics).sort_values(
        "total_cost_gbp",
        ascending=False,
    )
    fig, axis = plt.subplots(figsize=(10, 5.5))
    colors = [
        "#90be6d" if policy != "perfect_foresight" else "#577590"
        for policy in metric_frame["policy"]
    ]
    axis.barh(
        metric_frame["policy"].str.replace("_", " "),
        metric_frame["total_cost_gbp"],
        color=colors,
    )
    axis.set(
        title="Prototype hedge-policy scenario cost",
        xlabel="Total scenario cost (£)",
    )
    fig.tight_layout()
    path = figure_root / "hedge_policy_comparison.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["hedge_policy_comparison"] = path.as_posix()

    sample = recommendations.tail(96)
    fig, axis = plt.subplots(figsize=(11, 5))
    axis.plot(
        sample["timestamp_utc"],
        sample["realised_net_demand_mwh"],
        label="Realised net demand",
        linewidth=1.5,
    )
    axis.plot(
        sample["timestamp_utc"],
        sample["recommended_mwh"],
        label="Recommended hedge",
        linewidth=1.5,
    )
    axis.axhline(0, color="#555555", linewidth=0.8)
    axis.set(
        title="Leakage-aware hedge recommendation — final 48 hours",
        ylabel="Signed MWh",
        xlabel="Delivery time (UTC)",
    )
    axis.legend()
    fig.tight_layout()
    path = figure_root / "hedge_recommendations_over_time.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["hedge_recommendations_over_time"] = path.as_posix()

    pivot = sensitivity.pivot(
        index="short_cost_multiplier",
        columns="long_value_multiplier",
        values="total_scenario_cost_gbp",
    )
    fig, axis = plt.subplots(figsize=(8, 5))
    image = axis.imshow(pivot.to_numpy(), cmap="YlOrRd", aspect="auto")
    axis.set_xticks(range(len(pivot.columns)), pivot.columns)
    axis.set_yticks(range(len(pivot.index)), pivot.index)
    axis.set(
        title="Cost-assumption sensitivity",
        xlabel="Long-value multiplier",
        ylabel="Short-cost multiplier",
    )
    fig.colorbar(image, ax=axis, label="Total scenario cost (£)")
    fig.tight_layout()
    path = figure_root / "hedge_cost_sensitivity.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["hedge_cost_sensitivity"] = path.as_posix()

    selected = backtest[
        backtest["policy"] == "validation_optimised"
    ]
    fig, axis = plt.subplots(figsize=(10, 5))
    axis.hist(
        selected["realised_net_demand_mwh"]
        - selected["hedged_volume_mwh"],
        bins=24,
        color="#277da1",
        edgecolor="white",
    )
    axis.axvline(0, color="#333333", linewidth=1)
    axis.set(
        title="Validation-optimised imbalance distribution",
        xlabel="Realised net demand minus hedge (MWh)",
        ylabel="Settlement periods",
    )
    fig.tight_layout()
    path = figure_root / "hedge_imbalance_distribution.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    paths["hedge_imbalance_distribution"] = path.as_posix()
    return paths


def build_hedge_backtest(
    *,
    portfolio_forecasts_path: Path | str = (
        PROJECT_ROOT / "artifacts/forecasts/portfolio_forecasts.parquet"
    ),
    prices_path: Path | str = (
        PROJECT_ROOT / "data/processed/prices.parquet"
    ),
    forecast_output_path: Path | str = (
        PROJECT_ROOT / "artifacts/forecasts/hedge_recommendations.parquet"
    ),
    metrics_root: Path | str = PROJECT_ROOT / "artifacts/metrics",
    figure_root: Path | str = FIGURE_ROOT,
    forecast_model: str = DEFAULT_FORECAST_MODEL,
    assumptions: PriceAssumptions = PriceAssumptions(),
) -> dict[str, Any]:
    """Build Phase 9 recommendations, policy backtest and sensitivity."""
    portfolio = pd.read_parquet(portfolio_forecasts_path)
    prices = pd.read_parquet(prices_path)
    frame = _prepare_inputs(
        portfolio,
        prices,
        assumptions,
        forecast_model,
    )
    selected_quantiles, selection_history = select_validation_quantiles(
        frame,
        forecast_model,
    )
    backtest = evaluate_policies(
        frame,
        selected_quantiles,
        forecast_model,
    )
    recommendations = recommendation_frame(
        frame,
        backtest,
        selection_history,
        forecast_model,
    )
    if len(recommendations) != len(portfolio):
        raise AssertionError("Every portfolio period needs one recommendation")
    metrics = policy_metrics(backtest)
    sensitivity = _sensitivity(frame, prices, forecast_model)

    forecast_path = Path(forecast_output_path)
    metric_destination = Path(metrics_root)
    forecast_path.parent.mkdir(parents=True, exist_ok=True)
    metric_destination.mkdir(parents=True, exist_ok=True)
    backtest_path = metric_destination / "hedge_policy_backtest.parquet"
    metrics_path = metric_destination / "hedge_policy_metrics.parquet"
    sensitivity_path = metric_destination / "hedge_sensitivity.parquet"
    summary_path = metric_destination / "hedge_backtest.json"
    recommendations.to_parquet(forecast_path, index=False)
    backtest.to_parquet(backtest_path, index=False)
    pd.DataFrame(metrics).to_parquet(metrics_path, index=False)
    sensitivity.to_parquet(sensitivity_path, index=False)
    figures = _create_figures(
        recommendations,
        backtest,
        metrics,
        sensitivity,
        Path(figure_root),
    )
    metric_lookup = {row["policy"]: row for row in metrics}
    summary = {
        "hedge_model_version": HEDGE_MODEL_VERSION,
        "forecast_model": forecast_model,
        "settlement_periods": len(recommendations),
        "policies_compared": list(POLICIES),
        "recommended_policy": "validation_optimised",
        "selected_quantiles_by_fold": selected_quantiles,
        "selection_history": selection_history,
        "cost_assumptions": {
            "short_cost_multiplier": assumptions.short_cost_multiplier,
            "long_value_multiplier": assumptions.long_value_multiplier,
            "market_reference_price_gbp_mwh": float(
                frame["market_reference_price_gbp_mwh"].iloc[0]
            ),
            "system_price_range_gbp_mwh": [
                float(frame["public_system_price_gbp_mwh"].min()),
                float(frame["public_system_price_gbp_mwh"].max()),
            ],
            "price_data_origin": "public",
            "price_source": "Elexon Insights snapshot",
            "price_source_settlement_date": str(
                frame["price_source_settlement_date"].iloc[0]
            ),
            "price_alignment_method": PRICE_ALIGNMENT,
        },
        "policy_metrics": metrics,
        "validation_optimised_result": metric_lookup[
            "validation_optimised"
        ],
        "no_hedge_result": metric_lookup["no_hedge"],
        "perfect_foresight_result": metric_lookup["perfect_foresight"],
        "perfect_foresight_is_lower_bound_only": True,
        "leakage_audit_passed": all(
            record["evidence_end_utc"] is None
            or record["evidence_end_utc"]
            < record["current_fold_earliest_issue_time_utc"]
            for record in selection_history
        ),
        "scenario_function": (
            "gridmatch.market.hedging.scenario_recommendation"
        ),
        "artifacts": {
            "hedge_recommendations": _portable_path(forecast_path),
            "hedge_backtest": _portable_path(summary_path),
            "policy_backtest": _portable_path(backtest_path),
            "policy_metrics": _portable_path(metrics_path),
            "sensitivity": _portable_path(sensitivity_path),
        },
        "figures": {
            key: _portable_path(path) for key, path in figures.items()
        },
        "interpretation": (
            "Out-of-sample volume backtest valued under an explicit public "
            "price-reference scenario; not realised supplier savings."
        ),
        "limitations": [
            "The public July 2026 price snapshot does not overlap the June 2025 volume backtest.",
            "The price curve is a scenario reference mapped by settlement period, not contemporaneous historical settlement.",
            "The simplified signed-volume rule is not a licensed-supplier or full BSC settlement engine.",
            "The prototype omits liquidity, gate closure, fees, credit, shape products and execution constraints.",
            "Perfect foresight uses realised demand and is only an unattainable lower-bound benchmark.",
        ],
    }
    _write_json(summary_path, summary)
    return summary
