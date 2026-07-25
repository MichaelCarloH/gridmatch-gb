"""Site metadata, observation, quality, forecast and map services."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from api.errors import APIError
from api.services.artifact_repository import (
    ArtifactRepository,
    json_safe,
    records,
    utc_timestamp,
)


class SiteService:
    def __init__(self, repository: ArtifactRepository) -> None:
        self.repository = repository

    def _sites(self) -> pd.DataFrame:
        sites = self.repository.parquet("sites")
        readiness = self.repository.parquet("readiness")
        frame = sites.merge(
            readiness[
                ["site_id", "quality_score", "site_readiness"]
            ],
            on="site_id",
            how="left",
            validate="one_to_one",
        )
        frame["modelled"] = frame["site_id"].map(
            lambda site_id: (
                self.repository.settings.artifact_dir
                / "models"
                / str(site_id)
                / "point.joblib"
            ).is_file()
        )
        return frame

    def ensure_site(self, site_id: str) -> pd.Series:
        selected = self._sites()
        selected = selected[selected["site_id"] == site_id]
        if selected.empty:
            raise APIError(
                404,
                "SITE_NOT_FOUND",
                "Unknown site_id.",
                {"site_id": site_id},
            )
        return selected.iloc[0]

    def list_sites(
        self,
        *,
        role: str | None,
        technology: str | None,
        archetype: str | None,
        region: str | None,
        data_origin: str | None,
        status: str | None,
        ready: bool | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        frame = self._sites()
        filters = {
            "site_role": role,
            "technology": technology,
            "business_archetype": archetype,
            "region": region,
            "data_origin": data_origin,
        }
        for column, value in filters.items():
            if value is not None:
                frame = frame[frame[column] == value]
        if status is not None:
            if status not in {"modelled", "unmodelled"}:
                raise APIError(
                    400,
                    "INVALID_STATUS",
                    "status must be modelled or unmodelled.",
                )
            frame = frame[
                frame["modelled"] == (status == "modelled")
            ]
        if ready is not None:
            frame = frame[
                (frame["site_readiness"] == "ready") == ready
            ]
        if search:
            term = search.casefold()
            frame = frame[
                frame[["site_id", "name", "region"]]
                .astype(str)
                .apply(
                    lambda column: column.str.casefold().str.contains(
                        term,
                        regex=False,
                    )
                )
                .any(axis=1)
            ]
        total = len(frame)
        return records(frame.iloc[offset : offset + limit]), total

    def get_site(self, site_id: str) -> dict[str, Any]:
        return json_safe(self.ensure_site(site_id).to_dict())

    def observations(
        self,
        site_id: str,
        *,
        start: datetime | None,
        end: datetime | None,
        quality_flag: str | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self.ensure_site(site_id)
        if start and end and start > end:
            raise APIError(
                400,
                "INVALID_DATE_RANGE",
                "start must not be after end.",
            )
        frame = self.repository.parquet("observations")
        frame = frame[frame["site_id"] == site_id]
        timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True)
        if start:
            frame = frame[
                timestamps >= utc_timestamp(start, "start")
            ]
            timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True)
        if end:
            frame = frame[
                timestamps <= utc_timestamp(end, "end")
            ]
        if quality_flag:
            frame = frame[
                frame["quality_flag"].astype(str).str.contains(
                    quality_flag,
                    regex=False,
                )
            ]
        frame = frame.sort_values("timestamp_utc")
        total = len(frame)
        return records(frame.head(limit)), total

    def quality(self, site_id: str) -> dict[str, Any]:
        self.ensure_site(site_id)
        frame = self.repository.parquet("readiness")
        return json_safe(
            frame[frame["site_id"] == site_id].iloc[0].to_dict()
        )

    def forecast(
        self,
        site_id: str,
        *,
        start: datetime | None,
        end: datetime | None,
        fold: int | None,
        model: str,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self.ensure_site(site_id)
        if model not in {"ml", "baseline", "statistical"}:
            raise APIError(
                400,
                "UNSUPPORTED_FORECAST_MODEL",
                "model must be ml, baseline or statistical.",
            )
        if start and end and start > end:
            raise APIError(
                400,
                "INVALID_DATE_RANGE",
                "start must not be after end.",
            )
        frame = self.repository.parquet("site_forecasts")
        frame = frame[frame["site_id"] == site_id].copy()
        timestamps = pd.to_datetime(frame["valid_time_utc"], utc=True)
        if start:
            frame = frame[
                timestamps >= utc_timestamp(start, "start")
            ]
            timestamps = pd.to_datetime(frame["valid_time_utc"], utc=True)
        if end:
            frame = frame[
                timestamps <= utc_timestamp(end, "end")
            ]
        if fold is not None:
            frame = frame[frame["validation_fold"] == fold]
        point_column = {
            "ml": "point_mwh",
            "baseline": "baseline_mwh",
            "statistical": "statistical_mwh",
        }[model]
        output = pd.DataFrame(
            {
                "site_id": frame["site_id"],
                "actual_mwh": frame["actual_mwh"],
                "point_mwh": frame[point_column],
                "q10_mwh": frame["q10_mwh"],
                "q50_mwh": frame["q50_mwh"],
                "q90_mwh": frame["q90_mwh"],
                "issue_time_utc": frame["issue_time_utc"],
                "valid_time_utc": frame["valid_time_utc"],
                "settlement_date": frame["settlement_date"],
                "settlement_period": frame["settlement_period"],
                "model_id": frame["model_id"],
                "model_version": frame["model_version"],
                "validation_fold": frame["validation_fold"],
                "forecast_method": model,
                "units": "MWh",
            }
        ).sort_values("valid_time_utc")
        total = len(output)
        return records(output.head(limit)), total

    def metrics(self, site_id: str) -> list[dict[str, Any]]:
        self.ensure_site(site_id)
        frame = self.repository.parquet("site_metrics")
        return records(frame[frame["site_id"] == site_id])

    def model_card(self, site_id: str) -> dict[str, Any]:
        self.ensure_site(site_id)
        return {
            "site_id": site_id,
            "format": "markdown",
            "content": self.repository.model_card(site_id),
        }

    def alerts(self, site_id: str) -> list[dict[str, Any]]:
        quality = self.quality(site_id)
        alerts = []
        for field, label in (
            ("missing_periods", "Missing settlement periods"),
            ("duplicate_observations", "Duplicate observations"),
            ("wrong_interval_count", "Invalid interval frequency"),
            ("above_capacity_count", "Generation above capacity"),
            ("night_solar_count", "Night-time solar generation"),
            ("long_zero_run_count", "Long zero runs"),
            ("extreme_spike_count", "Extreme spikes"),
        ):
            count = int(quality.get(field) or 0)
            if count:
                alerts.append(
                    {
                        "site_id": site_id,
                        "code": field.upper(),
                        "message": label,
                        "count": count,
                        "severity": (
                            "warning"
                            if field
                            in {
                                "above_capacity_count",
                                "night_solar_count",
                                "wrong_interval_count",
                            }
                            else "information"
                        ),
                        "source": "data_quality_artifact",
                    }
                )
        if quality.get("stale_data"):
            alerts.append(
                {
                    "site_id": site_id,
                    "code": "STALE_DATA",
                    "message": "Latest observations are stale.",
                    "count": 1,
                    "severity": "warning",
                    "source": "data_quality_artifact",
                }
            )
        return alerts

    def geojson(
        self,
        *,
        technology: str | None,
        role: str | None,
        data_origin: str | None,
        modelled: bool | None,
    ) -> dict[str, Any]:
        frame = self._sites()
        for column, value in {
            "technology": technology,
            "site_role": role,
            "data_origin": data_origin,
            "modelled": modelled,
        }.items():
            if value is not None:
                frame = frame[frame[column] == value]
        features = []
        for row in frame.to_dict(orient="records"):
            longitude = float(row.pop("longitude"))
            latitude = float(row.pop("latitude"))
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "properties": json_safe(row),
                }
            )
        bbox = None
        if features:
            coordinates = [
                feature["geometry"]["coordinates"] for feature in features
            ]
            bbox = [
                min(item[0] for item in coordinates),
                min(item[1] for item in coordinates),
                max(item[0] for item in coordinates),
                max(item[1] for item in coordinates),
            ]
        return {
            "type": "FeatureCollection",
            "features": features,
            "bbox": bbox,
        }
