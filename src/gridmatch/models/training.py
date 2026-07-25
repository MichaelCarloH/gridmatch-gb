"""End-to-end Phase 6 site model training and artifact generation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from gridmatch.features.site import (
    FEATURE_COLUMNS,
    FEATURE_VERSION,
    build_site_features,
    rolling_origin_splits,
)
from gridmatch.models.baselines import (
    BASELINE_DESCRIPTIONS,
    baseline_predictions,
    canonical_baseline_name,
)
from gridmatch.models.metrics import point_metrics, probabilistic_metrics
from gridmatch.models.site_forecasting import (
    MODEL_VERSION,
    ModelStack,
    predict_model_stack,
    train_model_stack,
)


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _clean_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_for_json(item) for item in value]
    if isinstance(value, tuple):
        return [_clean_for_json(item) for item in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            _clean_for_json(value),
            indent=2,
            default=_json_value,
            allow_nan=False,
        ),
        encoding="utf-8",
    )


def _save_stack(stack: ModelStack, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    joblib.dump(stack.statistical, destination / "statistical.joblib")
    joblib.dump(stack.point, destination / "point.joblib")
    joblib.dump(stack.q10, destination / "q10.joblib")
    joblib.dump(stack.q50, destination / "q50.joblib")
    joblib.dump(stack.q90, destination / "q90.joblib")


def _metric_row(
    *,
    site_id: str,
    model_name: str,
    model_type: str,
    fold: int,
    actual: np.ndarray,
    forecast: np.ndarray,
    normalization: float,
    q10: np.ndarray | None = None,
    q50: np.ndarray | None = None,
    q90: np.ndarray | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "site_id": site_id,
        "model_name": model_name,
        "model_type": model_type,
        "validation_fold": fold,
        "evaluation_rows": len(actual),
        **point_metrics(actual, forecast, normalization),
        "pinball_loss": np.nan,
        "interval_coverage": np.nan,
        "interval_width": np.nan,
    }
    if q10 is not None and q50 is not None and q90 is not None:
        row.update(probabilistic_metrics(actual, q10, q50, q90))
    return row


def _aggregate_metrics(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "mae",
        "rmse",
        "nmae",
        "bias",
        "pinball_loss",
        "interval_coverage",
        "interval_width",
    ]
    grouped = (
        fold_metrics.groupby(["site_id", "model_name", "model_type"], as_index=False)
        .agg(
            fold_count=("validation_fold", "nunique"),
            evaluation_rows=("evaluation_rows", "sum"),
            **{column: (column, "mean") for column in metric_columns},
        )
        .sort_values(["site_id", "model_type", "mae"])
        .reset_index(drop=True)
    )
    return grouped


def _model_card(
    site: dict[str, Any],
    metrics: pd.DataFrame,
    canonical_baseline: str,
    training_cutoff: pd.Timestamp,
) -> str:
    site_id = str(site["site_id"])
    site_metrics = metrics[metrics["site_id"] == site_id]
    baseline_mae = float(
        site_metrics.loc[
            site_metrics["model_name"] == canonical_baseline,
            "mae",
        ].iloc[0]
    )
    model_mae = float(
        site_metrics.loc[
            site_metrics["model_name"] == "hist_gradient_boosting",
            "mae",
        ].iloc[0]
    )
    improvement = 100 * (baseline_mae - model_mae) / max(baseline_mae, 1e-9)
    metric_lines = [
        "| Model | MAE (MWh) | RMSE (MWh) | nMAE | Bias (MWh) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in site_metrics.itertuples():
        metric_lines.append(
            f"| {row.model_name} | {row.mae:.5f} | {row.rmse:.5f} | "
            f"{row.nmae:.4f} | {row.bias:.5f} |"
        )
    return f"""# Model card — {site_id}

## Purpose

Day-ahead half-hourly {site["site_role"]} forecasting for the simulated
`{site["name"]}` demo site. The stored stack includes a Ridge statistical model,
HistGradientBoosting point model and q10/q50/q90 quantile models.

## Training and validation

- Data origin: **simulated**
- Feature version: `{FEATURE_VERSION}`
- Model version: `{MODEL_VERSION}`
- Final rolling-origin training cutoff: `{training_cutoff.isoformat()}`
- Validation: two expanding-window seven-day folds; no random split
- Forecast issue convention: exactly 48 half-hour periods before valid time
- Canonical baseline: `{canonical_baseline}`

## Performance

{chr(10).join(metric_lines)}

The ML point model changes MAE by {improvement:.2f}% versus the canonical
baseline. Negative forecasts are clipped; generation is capped at installed
capacity, and solar output is forced to zero at night.

## Limitations

The meter and site data are simulated. Weather inputs are simulated realised
weather used as a forecast-weather proxy, not archived operational forecast
vintages. Metrics therefore demonstrate pipeline behaviour, not expected
production or commercial performance. Outage and curtailment availability are
not separately forecast.

## Production recommendations

Replace the weather proxy with issue-time forecast vintages, calibrate intervals
on a longer history, review flagged observations per use case, monitor drift and
coverage, and obtain human approval before forecasts influence trading.
"""


def _train_global_fallbacks(
    feature_frames: dict[str, pd.DataFrame],
    sites: pd.DataFrame,
    models_root: Path,
    generated_at: str,
) -> list[dict[str, Any]]:
    definitions = {
        "global_demand": sites["site_role"].eq("demand"),
        "global_solar": sites["technology"].eq("solar"),
        "global_wind": sites["technology"].eq("wind"),
    }
    outputs = []
    for name, site_mask in definitions.items():
        site_ids = sites.loc[site_mask, "site_id"].tolist()
        combined = pd.concat(
            [feature_frames[site_id] for site_id in site_ids],
            ignore_index=True,
        )
        final_split = rolling_origin_splits(combined, folds=2, test_days=7)[-1]
        training = combined.loc[final_split.train_mask].copy()
        stack = train_model_stack(training)
        destination = models_root / name
        _save_stack(stack, destination)
        metadata = {
            "model_id": name,
            "model_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "fallback_for_site_ids": site_ids,
            "training_rows": len(training),
            "training_cutoff_utc": final_split.training_cutoff,
            "generated_at_utc": generated_at,
            "data_origin": "simulated",
            "feature_columns": FEATURE_COLUMNS,
        }
        _write_json(destination / "metadata.json", metadata)
        outputs.append(metadata)
    return outputs


def train_all_sites(
    sites_path: Path | str = "data/demo/sites.parquet",
    observations_path: Path | str = "data/demo/observations.parquet",
    artifacts_root: Path | str = "artifacts",
) -> dict[str, Any]:
    """Train and persist every Phase 6 site stack and validation artifact."""
    sites = pd.read_parquet(sites_path)
    observations = pd.read_parquet(observations_path)
    if set(sites["data_origin"]) != {"simulated"}:
        raise ValueError("Phase 6 demo training requires explicitly simulated sites")
    if set(observations["data_origin"]) != {"simulated"}:
        raise ValueError("Phase 6 demo training requires simulated observations")

    root = Path(artifacts_root)
    models_root = root / "models"
    forecasts_root = root / "forecasts"
    metrics_root = root / "metrics"
    for directory in (models_root, forecasts_root, metrics_root):
        directory.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    feature_frames: dict[str, pd.DataFrame] = {}
    forecast_frames: list[pd.DataFrame] = []
    fold_metric_rows: list[dict[str, Any]] = []
    final_stacks: dict[str, tuple[ModelStack, pd.Timestamp, int]] = {}

    for site_record in sites.to_dict(orient="records"):
        site_id = str(site_record["site_id"])
        site_observations = observations[observations["site_id"] == site_id]
        features = build_site_features(site_observations, site_record)
        feature_frames[site_id] = features
        splits = rolling_origin_splits(features, folds=2, test_days=7)
        canonical_baseline = canonical_baseline_name(site_record)

        for split in splits:
            training = features.loc[split.train_mask].copy()
            testing = features.loc[split.test_mask].copy()
            stack = train_model_stack(training)
            model_predictions = predict_model_stack(stack, testing, site_record)
            baselines = baseline_predictions(testing, site_record)
            actual = testing["actual_mwh"].to_numpy(dtype=float)
            normalization = float(site_record["installed_capacity_mw"]) * 0.5

            for baseline_name, values in baselines.items():
                fold_metric_rows.append(
                    _metric_row(
                        site_id=site_id,
                        model_name=baseline_name,
                        model_type="baseline",
                        fold=split.fold,
                        actual=actual,
                        forecast=values,
                        normalization=normalization,
                    )
                )
            fold_metric_rows.append(
                _metric_row(
                    site_id=site_id,
                    model_name="ridge",
                    model_type="statistical",
                    fold=split.fold,
                    actual=actual,
                    forecast=model_predictions["statistical_mwh"],
                    normalization=normalization,
                )
            )
            fold_metric_rows.append(
                _metric_row(
                    site_id=site_id,
                    model_name="hist_gradient_boosting",
                    model_type="ml_probabilistic",
                    fold=split.fold,
                    actual=actual,
                    forecast=model_predictions["point_mwh"],
                    normalization=normalization,
                    q10=model_predictions["q10_mwh"],
                    q50=model_predictions["q50_mwh"],
                    q90=model_predictions["q90_mwh"],
                )
            )

            forecast = testing[
                [
                    "site_id",
                    "site_role",
                    "technology",
                    "issue_time_utc",
                    "valid_time_utc",
                    "settlement_date",
                    "settlement_period",
                    "horizon_periods",
                    "actual_mwh",
                    "data_origin",
                    "is_daylight",
                ]
            ].copy()
            forecast["baseline_method"] = canonical_baseline
            forecast["baseline_mwh"] = baselines[canonical_baseline]
            for column, values in model_predictions.items():
                forecast[column] = values
            forecast["model_id"] = f"{site_id}:hist_gradient_boosting"
            forecast["model_version"] = MODEL_VERSION
            forecast["feature_version"] = FEATURE_VERSION
            forecast["training_cutoff_utc"] = split.training_cutoff
            forecast["validation_fold"] = split.fold
            forecast_frames.append(forecast)
            if split is splits[-1]:
                final_stacks[site_id] = (
                    stack,
                    split.training_cutoff,
                    len(training),
                )
        print(f"{site_id}: trained and validated")

    fold_metrics = pd.DataFrame(fold_metric_rows)
    metrics = _aggregate_metrics(fold_metrics)
    forecasts = pd.concat(forecast_frames, ignore_index=True).sort_values(
        ["site_id", "valid_time_utc"]
    )

    for site_record in sites.to_dict(orient="records"):
        site_id = str(site_record["site_id"])
        stack, training_cutoff, training_rows = final_stacks[site_id]
        destination = models_root / site_id
        _save_stack(stack, destination)
        canonical_baseline = canonical_baseline_name(site_record)
        site_metrics = metrics[metrics["site_id"] == site_id]
        baseline_payload = {
            "site_id": site_id,
            "canonical_baseline": canonical_baseline,
            "definitions": {
                name: BASELINE_DESCRIPTIONS[name]
                for name in site_metrics.loc[
                    site_metrics["model_type"] == "baseline",
                    "model_name",
                ]
            },
            "metrics": site_metrics.loc[
                site_metrics["model_type"] == "baseline"
            ].to_dict(orient="records"),
        }
        _write_json(destination / "baseline.json", baseline_payload)
        metadata = {
            "model_id": f"{site_id}:hist_gradient_boosting",
            "site_id": site_id,
            "site_role": site_record["site_role"],
            "technology": site_record["technology"],
            "business_archetype": site_record["business_archetype"],
            "model_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "feature_columns": FEATURE_COLUMNS,
            "training_rows": training_rows,
            "training_cutoff_utc": training_cutoff,
            "generated_at_utc": generated_at,
            "data_origin": "simulated",
            "weather_input_limitation": (
                "Simulated realised weather is a methodology proxy, not a "
                "forecast-vintage archive."
            ),
        }
        _write_json(destination / "metadata.json", metadata)
        (destination / "model_card.md").write_text(
            _model_card(
                site_record,
                metrics,
                canonical_baseline,
                training_cutoff,
            ),
            encoding="utf-8",
        )

    global_metadata = _train_global_fallbacks(
        feature_frames,
        sites,
        models_root,
        generated_at,
    )
    forecasts_root.mkdir(parents=True, exist_ok=True)
    metrics_root.mkdir(parents=True, exist_ok=True)
    forecasts.to_parquet(
        forecasts_root / "site_forecasts.parquet",
        index=False,
    )
    fold_metrics.to_parquet(
        metrics_root / "site_metrics_by_fold.parquet",
        index=False,
    )
    metrics.to_parquet(metrics_root / "site_metrics.parquet", index=False)

    comparison = metrics.pivot_table(
        index="site_id",
        columns="model_name",
        values="mae",
    )
    canonical_names = {
        str(site.site_id): canonical_baseline_name(site._asdict())
        for site in sites.itertuples(index=False)
    }
    improvement_rows = []
    for site_id, baseline_name in canonical_names.items():
        baseline_mae = float(comparison.loc[site_id, baseline_name])
        ml_mae = float(comparison.loc[site_id, "hist_gradient_boosting"])
        improvement_rows.append(
            {
                "site_id": site_id,
                "baseline_name": baseline_name,
                "baseline_mae": baseline_mae,
                "ml_mae": ml_mae,
                "ml_improves_baseline": ml_mae < baseline_mae,
            }
        )
    improvement = pd.DataFrame(improvement_rows)
    summary = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "generated_at_utc": generated_at,
        "site_count": len(sites),
        "forecast_rows": len(forecasts),
        "rolling_origin_folds": 2,
        "models_improving_canonical_baseline": int(
            improvement["ml_improves_baseline"].sum()
        ),
        "all_quantiles_ordered": bool(
            (
                (forecasts["q10_mwh"] <= forecasts["q50_mwh"])
                & (forecasts["q50_mwh"] <= forecasts["q90_mwh"])
            ).all()
        ),
        "global_fallbacks": [item["model_id"] for item in global_metadata],
        "site_comparison": improvement.to_dict(orient="records"),
        "metrics": metrics.to_dict(orient="records"),
    }
    if not summary["models_improving_canonical_baseline"]:
        raise RuntimeError("no site model improves on its canonical baseline")
    _write_json(metrics_root / "site_metrics.json", summary)
    return summary
