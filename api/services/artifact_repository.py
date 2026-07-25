"""Bounded, modification-aware readers for approved artifacts."""

from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime
import json
from pathlib import Path
from typing import Any
import warnings

import joblib
import numpy as np
import pandas as pd

from api.dependencies import Settings
from api.errors import APIError, ArtifactMissingError


def _load_joblib(path: Path) -> Any:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=(
                "Setting the shape on a NumPy array has been deprecated.*"
            ),
            category=DeprecationWarning,
            module="joblib.numpy_pickle",
        )
        return joblib.load(path)


class ArtifactRepository:
    """Lazy cache that never accepts user-provided filesystem paths."""

    REQUIRED_ARTIFACTS = (
        "sites",
        "observations",
        "readiness",
        "site_forecasts",
        "site_metrics",
        "portfolio_forecasts",
        "matching_summary",
        "matching_periods",
        "hedge_recommendations",
        "hedge_backtest",
        "notebooks",
        "model_registry",
    )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cache: OrderedDict[
            str,
            tuple[int, Any],
        ] = OrderedDict()
        data = settings.data_dir
        artifacts = settings.artifact_dir
        self._paths: dict[str, Path] = {
            "sites": data / "demo/sites.parquet",
            "observations": data / "quality/annotated_observations.parquet",
            "readiness": data / "quality/site_readiness.parquet",
            "site_forecasts": artifacts
            / "forecasts/site_forecasts.parquet",
            "site_metrics": artifacts / "metrics/site_metrics.parquet",
            "portfolio_forecasts": artifacts
            / "forecasts/portfolio_forecasts.parquet",
            "portfolio_metrics": artifacts
            / "metrics/portfolio_metrics.parquet",
            "portfolio_attribution_site": artifacts
            / "metrics/site_error_contributions.parquet",
            "portfolio_attribution_technology": artifacts
            / "metrics/technology_error_contributions.parquet",
            "portfolio_attribution_region": artifacts
            / "metrics/region_error_contributions.parquet",
            "portfolio_correlation": artifacts
            / "metrics/site_error_correlation.parquet",
            "matching_summary": artifacts / "matching/summary.json",
            "matching_periods": artifacts
            / "matching/period_summary.parquet",
            "matching_forecast": artifacts
            / "matching/forecast_allocations.parquet",
            "matching_realised": artifacts
            / "matching/realised_allocations.parquet",
            "matching_consumers": artifacts
            / "matching/consumer_summary.parquet",
            "matching_generators": artifacts
            / "matching/generator_summary.parquet",
            "matching_comparison": artifacts
            / "matching/allocation_comparison.parquet",
            "map_arcs": artifacts / "matching/map_arcs.parquet",
            "prices": data / "processed/prices.parquet",
            "hedge_recommendations": artifacts
            / "forecasts/hedge_recommendations.parquet",
            "hedge_policy_metrics": artifacts
            / "metrics/hedge_policy_metrics.parquet",
            "hedge_sensitivity": artifacts
            / "metrics/hedge_sensitivity.parquet",
            "hedge_backtest": artifacts / "metrics/hedge_backtest.json",
            "notebooks": artifacts / "notebooks/notebook_index.json",
            "model_registry": artifacts / "models/model_registry.parquet",
        }

    def path(self, logical_id: str) -> Path:
        try:
            return self._paths[logical_id]
        except KeyError as error:
            raise ArtifactMissingError(logical_id) from error

    def _read_cached(
        self,
        cache_key: str,
        path: Path,
        loader: Any,
    ) -> Any:
        if not path.is_file():
            raise ArtifactMissingError(cache_key.split(":", 1)[0])
        modified = path.stat().st_mtime_ns
        cached = self._cache.get(cache_key)
        if cached and cached[0] == modified:
            self._cache.move_to_end(cache_key)
            return cached[1]
        value = loader(path)
        self._cache[cache_key] = (modified, value)
        self._cache.move_to_end(cache_key)
        while len(self._cache) > self.settings.model_cache_size:
            self._cache.popitem(last=False)
        return value

    def parquet(
        self,
        logical_id: str,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        path = self.path(logical_id)
        projection = ",".join(columns or ())
        key = f"{logical_id}:parquet:{projection}"
        return self._read_cached(
            key,
            path,
            lambda value: pd.read_parquet(value, columns=columns),
        ).copy(deep=False)

    def json(self, logical_id: str) -> Any:
        path = self.path(logical_id)
        return self._read_cached(
            f"{logical_id}:json",
            path,
            lambda value: json.loads(value.read_text(encoding="utf-8")),
        )

    def model(self, site_id: str, artifact_name: str) -> Any:
        allowed = {
            "statistical",
            "point",
            "q10",
            "q50",
            "q90",
        }
        if artifact_name not in allowed:
            raise ArtifactMissingError("model")
        path = (
            self.settings.artifact_dir
            / "models"
            / site_id
            / f"{artifact_name}.joblib"
        )
        return self._read_cached(
            f"model:{site_id}:{artifact_name}",
            path,
            _load_joblib,
        )

    def model_metadata(self, site_id: str) -> dict[str, Any]:
        path = (
            self.settings.artifact_dir
            / "models"
            / site_id
            / "metadata.json"
        )
        return self._read_cached(
            f"metadata:{site_id}",
            path,
            lambda value: json.loads(value.read_text(encoding="utf-8")),
        )

    def model_card(self, site_id: str) -> str:
        path = (
            self.settings.artifact_dir
            / "models"
            / site_id
            / "model_card.md"
        )
        return self._read_cached(
            f"card:{site_id}",
            path,
            lambda value: value.read_text(encoding="utf-8"),
        )

    def availability(self) -> dict[str, bool]:
        return {
            logical_id: self.path(logical_id).is_file()
            for logical_id in self.REQUIRED_ARTIFACTS
        }

    def last_artifact_update(self) -> str | None:
        timestamps = [
            path.stat().st_mtime
            for path in self._paths.values()
            if path.is_file()
        ]
        if not timestamps:
            return None
        return datetime.fromtimestamp(
            max(timestamps),
        ).astimezone().isoformat()


def json_safe(value: Any) -> Any:
    """Convert pandas/numpy values without emitting NaN or Infinity."""
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if pd.isna(value):
        return None
    return value


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        json_safe(record)
        for record in frame.to_dict(orient="records")
    ]


def utc_timestamp(value: Any, field_name: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise APIError(
            422,
            "TIMEZONE_REQUIRED",
            f"{field_name} must include a UTC offset.",
        )
    return timestamp.tz_convert("UTC")
