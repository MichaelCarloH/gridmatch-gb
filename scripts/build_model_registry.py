"""Consolidate saved Phase 6/7 estimators into a logical model registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "artifacts/models"
VARIANTS = {
    "statistical": ("ridge", None),
    "point": ("hist_gradient_boosting", None),
    "q10": ("hist_gradient_boosting", 0.1),
    "q50": ("hist_gradient_boosting", 0.5),
    "q90": ("hist_gradient_boosting", 0.9),
}


def _value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_value(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _metric(
    frame: pd.DataFrame,
    **filters: str,
) -> dict[str, Any]:
    selected = frame
    for column, value in filters.items():
        selected = selected[selected[column] == value]
    if selected.empty:
        return {}
    return selected.iloc[0].to_dict()


def build_model_registry(
    output_root: Path | str = MODEL_ROOT,
) -> dict[str, Any]:
    sites = pd.read_parquet(ROOT / "data/demo/sites.parquet")
    observations = pd.read_parquet(
        ROOT / "data/demo/observations.parquet",
        columns=["timestamp_utc"],
    )
    site_metrics = pd.read_parquet(
        ROOT / "artifacts/metrics/site_metrics.parquet"
    )
    portfolio_metrics = pd.read_parquet(
        ROOT / "artifacts/metrics/portfolio_metrics.parquet"
    )
    training_start = pd.to_datetime(
        observations["timestamp_utc"],
        utc=True,
    ).min().isoformat()
    rows: list[dict[str, Any]] = []

    for site in sites.itertuples(index=False):
        metadata_path = MODEL_ROOT / str(site.site_id) / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for artifact_type, (algorithm, quantile) in VARIANTS.items():
            metric_name = (
                "ridge"
                if artifact_type == "statistical"
                else "hist_gradient_boosting"
            )
            metrics = _metric(
                site_metrics,
                site_id=str(site.site_id),
                model_name=metric_name,
            )
            rows.append(
                {
                    "model_id": f"{site.site_id}:{artifact_type}",
                    "site_id": str(site.site_id),
                    "scope": "site",
                    "target": str(site.site_role),
                    "algorithm": algorithm,
                    "quantile": quantile,
                    "training_start": training_start,
                    "training_end": metadata["training_cutoff_utc"],
                    "feature_version": metadata["feature_version"],
                    "artifact_path": (
                        f"model://site/{site.site_id}/{artifact_type}"
                    ),
                    "artifact_type": artifact_type,
                    "created_at": metadata["generated_at_utc"],
                    "status": "active",
                    "mae": metrics.get("mae"),
                    "rmse": metrics.get("rmse"),
                    "bias": metrics.get("bias"),
                    "pinball_loss": metrics.get("pinball_loss"),
                    "coverage": metrics.get("interval_coverage"),
                    "intended_use": (
                        "Day-ahead half-hourly simulated site forecasting."
                    ),
                    "limitations": (
                        "Simulated site data and realised-weather proxy; "
                        "prototype use only."
                    ),
                }
            )

    for scope_name, target in (
        ("global_demand", "demand"),
        ("global_solar", "generation"),
        ("global_wind", "generation"),
    ):
        metadata = json.loads(
            (MODEL_ROOT / scope_name / "metadata.json").read_text(
                encoding="utf-8"
            )
        )
        for artifact_type, (algorithm, quantile) in VARIANTS.items():
            rows.append(
                {
                    "model_id": f"{scope_name}:{artifact_type}",
                    "site_id": None,
                    "scope": "global_fallback",
                    "target": target,
                    "algorithm": algorithm,
                    "quantile": quantile,
                    "training_start": training_start,
                    "training_end": metadata["training_cutoff_utc"],
                    "feature_version": metadata["feature_version"],
                    "artifact_path": (
                        f"model://global/{scope_name}/{artifact_type}"
                    ),
                    "artifact_type": artifact_type,
                    "created_at": metadata["generated_at_utc"],
                    "status": "active",
                    "mae": None,
                    "rmse": None,
                    "bias": None,
                    "pinball_loss": None,
                    "coverage": None,
                    "intended_use": (
                        "Fallback demonstration when a site-specific stack "
                        "is unavailable."
                    ),
                    "limitations": (
                        "Pooled simulated data; no site-specific performance "
                        "claim."
                    ),
                }
            )

    for target in ("demand", "generation", "net"):
        metadata = json.loads(
            (
                MODEL_ROOT / "portfolio" / target / "metadata.json"
            ).read_text(encoding="utf-8")
        )
        metrics = _metric(
            portfolio_metrics,
            target=target,
            method="direct",
        )
        for artifact_type, (algorithm, quantile) in VARIANTS.items():
            rows.append(
                {
                    "model_id": f"portfolio:{target}:{artifact_type}",
                    "site_id": None,
                    "scope": "portfolio",
                    "target": target,
                    "algorithm": algorithm,
                    "quantile": quantile,
                    "training_start": training_start,
                    "training_end": metadata["training_cutoff_utc"],
                    "feature_version": metadata["feature_version"],
                    "artifact_path": (
                        f"model://portfolio/{target}/{artifact_type}"
                    ),
                    "artifact_type": artifact_type,
                    "created_at": metadata["generated_at_utc"],
                    "status": "active",
                    "mae": metrics.get("mae"),
                    "rmse": metrics.get("rmse"),
                    "bias": metrics.get("bias"),
                    "pinball_loss": metrics.get("pinball_loss"),
                    "coverage": metrics.get("interval_coverage"),
                    "intended_use": (
                        f"Direct aggregate {target} forecast demonstration."
                    ),
                    "limitations": (
                        "Simulated portfolio and realised-weather proxy; "
                        "compare with bottom-up evidence."
                    ),
                }
            )

    frame = pd.DataFrame(rows).sort_values("model_id").reset_index(drop=True)
    destination = Path(output_root)
    destination.mkdir(parents=True, exist_ok=True)
    parquet_path = destination / "model_registry.parquet"
    json_path = destination / "model_registry.json"
    frame.to_parquet(parquet_path, index=False)
    json_path.write_text(
        json.dumps(
            [_value(record) for record in frame.to_dict(orient="records")],
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    return {
        "model_count": len(frame),
        "site_models": int((frame["scope"] == "site").sum()),
        "global_fallback_models": int(
            (frame["scope"] == "global_fallback").sum()
        ),
        "portfolio_models": int((frame["scope"] == "portfolio").sum()),
        "parquet": parquet_path.as_posix(),
        "json": json_path.as_posix(),
    }


if __name__ == "__main__":
    print(json.dumps(build_model_registry(), indent=2))
