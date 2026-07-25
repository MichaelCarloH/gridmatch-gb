"""Phase 7 portfolio aggregation, direct modelling and reconciliation."""

from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gridmatch.features.portfolio import (
    PORTFOLIO_FEATURE_COLUMNS,
    PORTFOLIO_FEATURE_VERSION,
    build_portfolio_features,
)
from gridmatch.features.site import rolling_origin_splits
from gridmatch.models.site_forecasting import (
    ModelStack,
    repair_quantiles,
    train_model_stack,
)
from gridmatch.portfolio.metrics import (
    HEDGE_COST_GBP_PER_MWH,
    portfolio_metrics,
)
from gridmatch.portfolio.simulation import (
    PORTFOLIO_CORRELATION,
    PORTFOLIO_SIMULATIONS,
    simulate_portfolio_quantiles,
)
from gridmatch.research.common import FIGURE_ROOT, research_style

PORTFOLIO_MODEL_VERSION = "portfolio-forecast-v1"
TARGETS = ("demand", "generation", "net")
METHODS = ("baseline", "bottom_up", "direct", "reconciled")


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_json(item) for item in value]
    if isinstance(value, tuple):
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


def _save_direct_stack(stack: ModelStack, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    joblib.dump(stack.statistical, destination / "statistical.joblib")
    joblib.dump(stack.point, destination / "point.joblib")
    joblib.dump(stack.q10, destination / "q10.joblib")
    joblib.dump(stack.q50, destination / "q50.joblib")
    joblib.dump(stack.q90, destination / "q90.joblib")


def aggregate_bottom_up(
    site_forecasts: pd.DataFrame,
    sites: pd.DataFrame,
    *,
    seed: int = 20260725,
) -> pd.DataFrame:
    """Aggregate point forecasts exactly and intervals through simulation."""
    forecasts = site_forecasts.merge(
        sites[
            [
                "site_id",
                "installed_capacity_mw",
                "region",
            ]
        ],
        on="site_id",
        how="left",
        validate="many_to_one",
    )
    rng = np.random.default_rng(seed)
    rows = []
    group_columns = ["validation_fold", "valid_time_utc"]
    for (fold, valid_time), group in forecasts.groupby(
        group_columns,
        sort=True,
    ):
        demand = group["site_role"] == "demand"
        generation = ~demand
        record: dict[str, Any] = {
            "validation_fold": int(fold),
            "issue_time_utc": group["issue_time_utc"].max(),
            "valid_time_utc": valid_time,
            "settlement_date": group["settlement_date"].iloc[0],
            "settlement_period": int(group["settlement_period"].iloc[0]),
            "horizon_periods": int(group["horizon_periods"].max()),
            "training_cutoff_utc": group["training_cutoff_utc"].max(),
            "data_origin": "simulated",
            "bottom_up_correlation": PORTFOLIO_CORRELATION,
            "bottom_up_simulations": PORTFOLIO_SIMULATIONS,
        }
        for target, mask in (("demand", demand), ("generation", generation)):
            record[f"actual_{target}_mwh"] = float(
                group.loc[mask, "actual_mwh"].sum()
            )
            record[f"baseline_{target}_mwh"] = float(
                group.loc[mask, "baseline_mwh"].sum()
            )
            record[f"bottom_up_{target}_point_mwh"] = float(
                group.loc[mask, "point_mwh"].sum()
            )
        record["actual_net_mwh"] = (
            record["actual_demand_mwh"] - record["actual_generation_mwh"]
        )
        record["baseline_net_mwh"] = (
            record["baseline_demand_mwh"] - record["baseline_generation_mwh"]
        )
        record["bottom_up_net_point_mwh"] = (
            record["bottom_up_demand_point_mwh"]
            - record["bottom_up_generation_point_mwh"]
        )
        record.update(
            simulate_portfolio_quantiles(
                group,
                rng=rng,
            )
        )
        rows.append(record)
    return pd.DataFrame(rows).sort_values(
        ["validation_fold", "valid_time_utc"]
    ).reset_index(drop=True)


def _constrain_direct(
    values: np.ndarray,
    target: str,
    generation_capacity_mw: float,
) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if target in {"demand", "generation"}:
        result = np.maximum(result, 0)
    if target == "generation":
        result = np.minimum(result, generation_capacity_mw * 0.5)
    return result


def _predict_direct_stack(
    stack: ModelStack,
    frame: pd.DataFrame,
    target: str,
) -> dict[str, np.ndarray]:
    features = frame[PORTFOLIO_FEATURE_COLUMNS]
    generation_capacity = float(frame["generation_capacity_mw"].iloc[0])
    output = {
        "point": _constrain_direct(
            stack.point.predict(features),
            target,
            generation_capacity,
        ),
        "q10": _constrain_direct(
            stack.q10.predict(features),
            target,
            generation_capacity,
        ),
        "q50": _constrain_direct(
            stack.q50.predict(features),
            target,
            generation_capacity,
        ),
        "q90": _constrain_direct(
            stack.q90.predict(features),
            target,
            generation_capacity,
        ),
    }
    output["q10"], output["q50"], output["q90"] = repair_quantiles(
        output["q10"],
        output["q50"],
        output["q90"],
    )
    return output


def _optimal_weight(
    actual: np.ndarray,
    direct: np.ndarray,
    bottom_up: np.ndarray,
) -> float:
    grid = np.linspace(0, 1, 101)
    losses = [
        np.mean(np.abs(weight * direct + (1 - weight) * bottom_up - actual))
        for weight in grid
    ]
    return float(grid[int(np.argmin(losses))])


def direct_and_reconciled_forecasts(
    portfolio_features: pd.DataFrame,
    bottom_up: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, ModelStack], list[dict[str, Any]]]:
    """Train direct rolling models and reconcile using prior-fold evidence."""
    fold_outputs = []
    final_stacks: dict[str, ModelStack] = {}
    splits = rolling_origin_splits(
        portfolio_features,
        folds=2,
        test_days=7,
    )
    for split in splits:
        training = portfolio_features.loc[split.train_mask].copy()
        testing = portfolio_features.loc[split.test_mask].copy()
        fold = bottom_up[bottom_up["validation_fold"] == split.fold].copy()
        fold = fold.merge(
            testing[
                [
                    "valid_time_utc",
                    "generation_capacity_mw",
                ]
            ],
            on="valid_time_utc",
            how="inner",
            validate="one_to_one",
        )
        testing = testing.set_index("valid_time_utc").loc[
            fold["valid_time_utc"]
        ].reset_index()
        if len(fold) != len(testing):
            raise ValueError("direct and bottom-up validation rows do not align")
        fold["training_cutoff_utc"] = max(
            pd.Timestamp(split.training_cutoff),
            pd.Timestamp(fold["training_cutoff_utc"].max()),
        )
        for target in TARGETS:
            training_target = training.copy()
            training_target["actual_mwh"] = training_target[
                f"actual_{target}_mwh"
            ]
            stack = train_model_stack(
                training_target,
                feature_columns=PORTFOLIO_FEATURE_COLUMNS,
            )
            predictions = _predict_direct_stack(stack, testing, target)
            for quantile, values in predictions.items():
                fold[f"direct_{target}_{quantile}_mwh"] = values
            if split is splits[-1]:
                final_stacks[target] = stack
        fold_outputs.append(fold)

    output = pd.concat(fold_outputs, ignore_index=True).sort_values(
        ["validation_fold", "valid_time_utc"]
    )
    weight_records = []
    previous = pd.DataFrame()
    for fold_number in sorted(output["validation_fold"].unique()):
        mask = output["validation_fold"] == fold_number
        for target in TARGETS:
            if previous.empty:
                weight = 0.5
                source = "documented default; no earlier validation fold"
            else:
                weight = _optimal_weight(
                    previous[f"actual_{target}_mwh"].to_numpy(),
                    previous[f"direct_{target}_point_mwh"].to_numpy(),
                    previous[f"bottom_up_{target}_point_mwh"].to_numpy(),
                )
                source = "MAE grid search on prior rolling-origin folds only"
            output.loc[mask, f"reconciliation_weight_{target}"] = weight
            output.loc[mask, f"reconciled_{target}_point_mwh"] = (
                weight * output.loc[mask, f"direct_{target}_point_mwh"]
                + (1 - weight)
                * output.loc[mask, f"bottom_up_{target}_point_mwh"]
            )
            quantiles = []
            for quantile in ("q10", "q50", "q90"):
                values = (
                    weight * output.loc[mask, f"direct_{target}_{quantile}_mwh"]
                    + (1 - weight)
                    * output.loc[mask, f"bottom_up_{target}_{quantile}_mwh"]
                ).to_numpy()
                quantiles.append(values)
            q10, q50, q90 = repair_quantiles(*quantiles)
            for quantile, values in zip(("q10", "q50", "q90"), (q10, q50, q90)):
                output.loc[mask, f"reconciled_{target}_{quantile}_mwh"] = values
            weight_records.append(
                {
                    "validation_fold": int(fold_number),
                    "target": target,
                    "direct_weight": weight,
                    "bottom_up_weight": 1 - weight,
                    "selection_source": source,
                }
            )
        previous = output[output["validation_fold"] <= fold_number].copy()

    output["portfolio_model_version"] = PORTFOLIO_MODEL_VERSION
    output["portfolio_feature_version"] = PORTFOLIO_FEATURE_VERSION
    if not (
        output["training_cutoff_utc"] <= output["issue_time_utc"]
    ).all():
        raise ValueError("portfolio training cutoff exceeds an issue time")
    return output, final_stacks, weight_records


def _comparison_metrics(
    forecasts: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    aggregate_rows = []
    fold_rows = []
    for target in TARGETS:
        actual_column = f"actual_{target}_mwh"
        for method in METHODS:
            point_column = (
                f"baseline_{target}_mwh"
                if method == "baseline"
                else f"{method}_{target}_point_mwh"
            )
            quantile_columns = (
                None
                if method == "baseline"
                else [
                    f"{method}_{target}_q10_mwh",
                    f"{method}_{target}_q50_mwh",
                    f"{method}_{target}_q90_mwh",
                ]
            )
            for fold, group in forecasts.groupby("validation_fold"):
                kwargs = {}
                if quantile_columns:
                    kwargs = {
                        "q10": group[quantile_columns[0]].to_numpy(),
                        "q50": group[quantile_columns[1]].to_numpy(),
                        "q90": group[quantile_columns[2]].to_numpy(),
                    }
                fold_rows.append(
                    {
                        "target": target,
                        "method": method,
                        "validation_fold": int(fold),
                        "evaluation_rows": len(group),
                        **portfolio_metrics(
                            group[actual_column].to_numpy(),
                            group[point_column].to_numpy(),
                            **kwargs,
                        ),
                    }
                )
            kwargs = {}
            if quantile_columns:
                kwargs = {
                    "q10": forecasts[quantile_columns[0]].to_numpy(),
                    "q50": forecasts[quantile_columns[1]].to_numpy(),
                    "q90": forecasts[quantile_columns[2]].to_numpy(),
                }
            aggregate_rows.append(
                {
                    "target": target,
                    "method": method,
                    "evaluation_rows": len(forecasts),
                    **portfolio_metrics(
                        forecasts[actual_column].to_numpy(),
                        forecasts[point_column].to_numpy(),
                        **kwargs,
                    ),
                }
            )
    return pd.DataFrame(aggregate_rows), pd.DataFrame(fold_rows)


def _bottom_up_totals_match(
    forecasts: pd.DataFrame,
    site_forecasts: pd.DataFrame,
) -> bool:
    keys = ["validation_fold", "valid_time_utc"]
    expected = []
    for target, role in (("demand", "demand"), ("generation", "generation")):
        totals = (
            site_forecasts[site_forecasts["site_role"] == role]
            .groupby(keys, as_index=False)
            .agg(
                **{
                    f"expected_actual_{target}": ("actual_mwh", "sum"),
                    f"expected_point_{target}": ("point_mwh", "sum"),
                }
            )
        )
        expected.append(totals)
    comparison = expected[0].merge(expected[1], on=keys, validate="one_to_one")
    comparison = forecasts.merge(comparison, on=keys, validate="one_to_one")
    checks = []
    for target in ("demand", "generation"):
        checks.extend(
            [
                np.allclose(
                    comparison[f"actual_{target}_mwh"],
                    comparison[f"expected_actual_{target}"],
                ),
                np.allclose(
                    comparison[f"bottom_up_{target}_point_mwh"],
                    comparison[f"expected_point_{target}"],
                ),
            ]
        )
    return bool(all(checks))


def _group_error_attribution(
    signed_errors: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    grouped = (
        signed_errors.groupby(
            [
                "validation_fold",
                "valid_time_utc",
                group_column,
            ],
            as_index=False,
        )["signed_error_mwh"]
        .sum()
    )
    summary = (
        grouped.groupby(group_column)["signed_error_mwh"]
        .agg(
            mean_absolute_error_mwh=lambda values: float(
                np.mean(np.abs(values))
            ),
            rmse_mwh=lambda values: float(np.sqrt(np.mean(values**2))),
            bias_mwh="mean",
        )
        .reset_index()
    )
    denominator = max(float(summary["mean_absolute_error_mwh"].sum()), 1e-9)
    summary["absolute_error_share"] = (
        summary["mean_absolute_error_mwh"] / denominator
    )
    return summary.sort_values(
        "mean_absolute_error_mwh",
        ascending=False,
    ).reset_index(drop=True)


def error_attribution(
    site_forecasts: pd.DataFrame,
    sites: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Produce signed site, technology and region error evidence."""
    rows = site_forecasts.merge(
        sites[["site_id", "technology", "region"]],
        on=["site_id", "technology"],
        how="left",
        validate="many_to_one",
    )
    sign = np.where(rows["site_role"] == "demand", 1.0, -1.0)
    rows["signed_error_mwh"] = sign * (
        rows["point_mwh"] - rows["actual_mwh"]
    )
    site = _group_error_attribution(rows, "site_id")
    site = site.merge(
        sites[["site_id", "technology", "region"]],
        on="site_id",
        how="left",
    )
    technology = _group_error_attribution(rows, "technology")
    region = _group_error_attribution(rows, "region")
    correlation = rows.pivot_table(
        index=["validation_fold", "valid_time_utc"],
        columns="site_id",
        values="signed_error_mwh",
    ).corr()
    correlation.index.name = "site_id"
    return site, technology, region, correlation


def _save_figures(
    forecasts: pd.DataFrame,
    correlation: pd.DataFrame,
) -> dict[str, Path]:
    research_style()
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    recent = forecasts[
        forecasts["validation_fold"] == forecasts["validation_fold"].max()
    ].tail(144)
    figure, axis = plt.subplots(figsize=(12, 5.5))
    axis.plot(
        recent["valid_time_utc"],
        recent["actual_net_mwh"],
        color="#1c2833",
        linewidth=2.2,
        label="Actual",
    )
    axis.plot(
        recent["valid_time_utc"],
        recent["bottom_up_net_point_mwh"],
        color="#2f73d9",
        alpha=0.8,
        label="Bottom-up",
    )
    axis.plot(
        recent["valid_time_utc"],
        recent["direct_net_point_mwh"],
        color="#d99a2b",
        alpha=0.8,
        label="Direct",
    )
    axis.plot(
        recent["valid_time_utc"],
        recent["reconciled_net_point_mwh"],
        color="#4ca855",
        linewidth=1.8,
        label="Reconciled",
    )
    axis.fill_between(
        recent["valid_time_utc"],
        recent["reconciled_net_q10_mwh"],
        recent["reconciled_net_q90_mwh"],
        color="#4ca855",
        alpha=0.16,
        label="Reconciled q10–q90",
    )
    axis.axhline(0, color="#737b83", linewidth=0.8)
    axis.set_ylabel("Net position (MWh)")
    axis.set_title("Portfolio net-position forecast comparison")
    axis.legend(frameon=False, ncol=3)
    figure.autofmt_xdate()
    figure.tight_layout()
    comparison_path = FIGURE_ROOT / "portfolio_comparison.png"
    figure.savefig(comparison_path, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 8))
    image = axis.imshow(
        correlation.to_numpy(),
        vmin=-1,
        vmax=1,
        cmap="RdBu_r",
    )
    axis.set_xticks(range(len(correlation.columns)))
    axis.set_xticklabels(correlation.columns, rotation=90, fontsize=8)
    axis.set_yticks(range(len(correlation.index)))
    axis.set_yticklabels(correlation.index, fontsize=8)
    axis.set_title("Correlated site forecast errors")
    figure.colorbar(image, ax=axis, label="Pearson correlation")
    figure.tight_layout()
    correlation_path = FIGURE_ROOT / "portfolio_error_correlation_heatmap.png"
    figure.savefig(correlation_path, bbox_inches="tight")
    plt.close(figure)
    return {
        "comparison": comparison_path,
        "error_correlation": correlation_path,
    }


def _portfolio_model_card(
    metrics: pd.DataFrame,
    weights: list[dict[str, Any]],
) -> str:
    table = [
        "| Target | Method | MAE (MWh) | RMSE (MWh) | Bias (MWh) | Coverage |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in metrics.itertuples():
        coverage = (
            "n/a"
            if row.interval_coverage is None or pd.isna(row.interval_coverage)
            else f"{row.interval_coverage:.3f}"
        )
        table.append(
            f"| {row.target} | {row.method} | {row.mae:.4f} | "
            f"{row.rmse:.4f} | {row.bias:.4f} | {coverage} |"
        )
    final_weights = [
        row for row in weights if row["validation_fold"] == 2
    ]
    weight_lines = "\n".join(
        f"- {row['target']}: direct `{row['direct_weight']:.2f}`, "
        f"bottom-up `{row['bottom_up_weight']:.2f}`"
        for row in final_weights
    )
    return f"""# Portfolio forecast model card

## Purpose

Translate the 12 simulated site forecasts into aggregate demand, aggregate
generation and the operator's net position (`demand - generation`).

## Methods

- **Baseline:** aggregate the canonical site baselines.
- **Bottom-up:** exactly sum site point forecasts.
- **Bottom-up intervals:** 600 split-normal site simulations coupled by a
  one-factor Gaussian approximation with correlation `{PORTFOLIO_CORRELATION}`.
- **Direct:** HistGradientBoosting point/q10/q50/q90 models trained on aggregate
  weather, calendar, lag and site-composition features.
- **Reconciled:** direct and bottom-up forecasts blended using weights selected
  only from earlier rolling-origin validation evidence.

Final-fold reconciliation weights:

{weight_lines}

## Rolling-origin evidence

{chr(10).join(table)}

The simulated hedge-cost column is a transparent diagnostic proxy:
absolute forecast error multiplied by £{HEDGE_COST_GBP_PER_MWH:.0f}/MWh. It is
not a Phase 9 hedge strategy or a claim about realised imbalance prices.

## Limitations

Site data and weather are simulated, weather is not a forecast-vintage archive,
and only two seven-day rolling folds are available. The Gaussian correlation
factor is a documented approximation, not a calibrated production copula.
Quantile blending is an approximation and should be recalibrated with longer
permissioned histories.

## Production recommendations

Archive issue-time weather vintages, estimate changing cross-site error
dependence, expand rolling seasons, monitor interval calibration and determine
reconciliation weights under an approved commercial loss function.
"""


def build_portfolio_forecasts(
    sites_path: Path | str = "data/demo/sites.parquet",
    observations_path: Path | str = "data/demo/observations.parquet",
    site_forecasts_path: Path | str = (
        "artifacts/forecasts/site_forecasts.parquet"
    ),
    artifacts_root: Path | str = "artifacts",
) -> dict[str, Any]:
    """Build every Phase 7 output from Phase 6 out-of-sample forecasts."""
    sites = pd.read_parquet(sites_path)
    observations = pd.read_parquet(observations_path)
    site_forecasts = pd.read_parquet(site_forecasts_path)
    if set(site_forecasts["data_origin"]) != {"simulated"}:
        raise ValueError("portfolio forecasts require labelled simulated inputs")
    root = Path(artifacts_root)
    forecast_root = root / "forecasts"
    metric_root = root / "metrics"
    model_root = root / "models" / "portfolio"
    for directory in (forecast_root, metric_root, model_root):
        directory.mkdir(parents=True, exist_ok=True)

    bottom_up = aggregate_bottom_up(site_forecasts, sites)
    features = build_portfolio_features(observations, sites)
    forecasts, final_stacks, weights = direct_and_reconciled_forecasts(
        features,
        bottom_up,
    )
    metrics, metrics_by_fold = _comparison_metrics(forecasts)
    site_error, technology_error, region_error, correlation = error_attribution(
        site_forecasts,
        sites,
    )
    figures = _save_figures(forecasts, correlation)

    for target, stack in final_stacks.items():
        destination = model_root / target
        _save_direct_stack(stack, destination)
        _write_json(
            destination / "metadata.json",
            {
                "model_id": f"portfolio_direct_{target}",
                "model_version": PORTFOLIO_MODEL_VERSION,
                "feature_version": PORTFOLIO_FEATURE_VERSION,
                "target": target,
                "feature_columns": PORTFOLIO_FEATURE_COLUMNS,
                "data_origin": "simulated",
                "training_cutoff_utc": forecasts.loc[
                    forecasts["validation_fold"] == 2,
                    "training_cutoff_utc",
                ].max(),
                "generated_at_utc": datetime.now(timezone.utc),
            },
        )

    forecasts.to_parquet(
        forecast_root / "portfolio_forecasts.parquet",
        index=False,
    )
    metrics.to_parquet(
        metric_root / "portfolio_metrics.parquet",
        index=False,
    )
    metrics_by_fold.to_parquet(
        metric_root / "portfolio_metrics_by_fold.parquet",
        index=False,
    )
    site_error.to_parquet(
        metric_root / "site_error_contributions.parquet",
        index=False,
    )
    technology_error.to_parquet(
        metric_root / "technology_error_contributions.parquet",
        index=False,
    )
    region_error.to_parquet(
        metric_root / "region_error_contributions.parquet",
        index=False,
    )
    correlation.to_parquet(
        metric_root / "site_error_correlation.parquet",
    )
    (model_root / "model_card.md").write_text(
        _portfolio_model_card(metrics, weights),
        encoding="utf-8",
    )

    best_methods = {
        target: str(
            metrics[metrics["target"] == target]
            .sort_values("mae")
            .iloc[0]["method"]
        )
        for target in TARGETS
    }
    totals_match = _bottom_up_totals_match(forecasts, site_forecasts)
    if not totals_match:
        raise ValueError("bottom-up totals do not equal site aggregation")
    summary = {
        "model_version": PORTFOLIO_MODEL_VERSION,
        "feature_version": PORTFOLIO_FEATURE_VERSION,
        "data_origin": "simulated",
        "forecast_rows": len(forecasts),
        "validation_folds": int(forecasts["validation_fold"].nunique()),
        "site_count": int(site_forecasts["site_id"].nunique()),
        "simulation": {
            "method": "split-normal marginals with one-factor Gaussian dependence",
            "simulations": PORTFOLIO_SIMULATIONS,
            "correlation": PORTFOLIO_CORRELATION,
            "seed": 20260725,
        },
        "reconciliation_weights": weights,
        "best_method_by_target_mae": best_methods,
        "bottom_up_totals_equal_site_aggregation": totals_match,
        "all_intervals_ordered": bool(
            all(
                (
                    forecasts[f"{method}_{target}_q10_mwh"]
                    <= forecasts[f"{method}_{target}_q50_mwh"]
                ).all()
                and (
                    forecasts[f"{method}_{target}_q50_mwh"]
                    <= forecasts[f"{method}_{target}_q90_mwh"]
                ).all()
                for method in ("bottom_up", "direct", "reconciled")
                for target in TARGETS
            )
        ),
        "metrics": metrics.to_dict(orient="records"),
        "artifacts": {
            "forecasts": "artifacts/forecasts/portfolio_forecasts.parquet",
            "comparison_figure": figures["comparison"].as_posix(),
            "error_correlation_figure": figures[
                "error_correlation"
            ].as_posix(),
        },
    }
    _write_json(metric_root / "portfolio_metrics.json", summary)
    return summary
