"""Model registry and compact saved-estimator inference."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import holidays
import numpy as np
import pandas as pd

from api.errors import APIError
from api.services.artifact_repository import ArtifactRepository, records
from api.services.site_service import SiteService
from gridmatch.features.site import (
    ARCHETYPE_CODES,
    FEATURE_COLUMNS,
    TECHNOLOGY_CODES,
)
from gridmatch.data.settlements import timestamp_to_settlement_period
from gridmatch.models.site_forecasting import (
    ModelStack,
    predict_model_stack,
)


class ModelService:
    def __init__(self, repository: ArtifactRepository) -> None:
        self.repository = repository
        self.sites = SiteService(repository)

    def list_models(
        self,
        *,
        site_id: str | None,
        algorithm: str | None,
        target: str | None,
        quantile: float | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        frame = self.repository.parquet("model_registry")
        filters = {
            "site_id": site_id,
            "algorithm": algorithm,
            "target": target,
            "status": status,
        }
        for column, value in filters.items():
            if value is not None:
                frame = frame[frame[column] == value]
        if quantile is not None:
            frame = frame[np.isclose(frame["quantile"], quantile)]
        total = len(frame)
        return records(frame.iloc[offset : offset + limit]), total

    def get_model(self, model_id: str) -> dict[str, Any]:
        frame = self.repository.parquet("model_registry")
        selected = frame[frame["model_id"] == model_id]
        if selected.empty:
            raise APIError(
                404,
                "MODEL_NOT_FOUND",
                "Unknown model_id.",
                {"model_id": model_id},
            )
        return records(selected)[0]

    @staticmethod
    def _sun_elevation(
        timestamp: pd.Timestamp,
        latitude: float,
    ) -> float:
        local = timestamp.tz_convert("Europe/London")
        day = local.dayofyear
        hour = local.hour + local.minute / 60
        declination = np.deg2rad(
            23.44 * np.sin(2 * np.pi * (284 + day) / 365)
        )
        latitude_rad = np.deg2rad(latitude)
        hour_angle = np.deg2rad(15 * (hour - 12))
        sine = (
            np.sin(latitude_rad) * np.sin(declination)
            + np.cos(latitude_rad)
            * np.cos(declination)
            * np.cos(hour_angle)
        )
        return float(np.rad2deg(np.arcsin(np.clip(sine, -1, 1))))

    @staticmethod
    def _is_open(archetype: str, hour: float) -> float:
        windows = {
            "office": (8.0, 18.5),
            "warehouse": (6.0, 22.0),
            "retail": (9.0, 21.0),
            "hospitality": (6.0, 23.5),
            "manufacturing": (6.0, 19.0),
        }
        if archetype not in windows:
            return 1.0
        start, end = windows[archetype]
        return float(start <= hour < end)

    def _feature_frame(
        self,
        site: pd.Series,
        issue_time: datetime,
        rows: list[dict[str, Any]],
    ) -> pd.DataFrame:
        issue = pd.Timestamp(issue_time)
        if issue.tzinfo is None:
            raise APIError(
                422,
                "TIMEZONE_REQUIRED",
                "forecast_issue_time_utc must include a UTC offset.",
            )
        issue = issue.tz_convert("UTC")
        gb_holidays = holidays.UnitedKingdom()
        output = []
        for values in rows:
            valid = pd.Timestamp(values["valid_time_utc"])
            if valid.tzinfo is None:
                raise APIError(
                    422,
                    "TIMEZONE_REQUIRED",
                    "valid_time_utc must include a UTC offset.",
                )
            valid = valid.tz_convert("UTC")
            if valid <= issue:
                raise APIError(
                    422,
                    "INVALID_PREDICTION_TIME",
                    "Every valid time must be after forecast issue time.",
                )
            horizon = (
                valid - issue
            ) / pd.Timedelta(minutes=30)
            if not float(horizon).is_integer():
                raise APIError(
                    422,
                    "INVALID_PREDICTION_INTERVAL",
                    "Prediction times must align to half-hour boundaries.",
                )
            if horizon > 336:
                raise APIError(
                    422,
                    "PREDICTION_HORIZON_TOO_LONG",
                    "Compact prediction supports at most seven days.",
                )
            _, derived_period = timestamp_to_settlement_period(valid)
            if int(values["settlement_period"]) != derived_period:
                raise APIError(
                    422,
                    "SETTLEMENT_PERIOD_MISMATCH",
                    (
                        "settlement_period does not match valid_time_utc "
                        "under Europe/London settlement rules."
                    ),
                    {
                        "expected_settlement_period": derived_period,
                    },
                )
            local = valid.tz_convert("Europe/London")
            hour = local.hour + local.minute / 60
            period_angle = (
                2 * np.pi * (hour * 2) / 48
            )
            direction = np.deg2rad(values["wind_direction_deg"])
            record = {
                "settlement_period": values["settlement_period"],
                "horizon_periods": int(round(horizon)),
                "period_sin": np.sin(period_angle),
                "period_cos": np.cos(period_angle),
                "weekday": local.dayofweek,
                "weekend": int(local.dayofweek >= 5),
                "bank_holiday": int(local.date() in gb_holidays),
                "day_of_year_sin": np.sin(
                    2 * np.pi * local.dayofyear / 365.25
                ),
                "day_of_year_cos": np.cos(
                    2 * np.pi * local.dayofyear / 365.25
                ),
                "temperature_c": values["temperature_c"],
                "heating_degree_c": max(
                    15 - values["temperature_c"],
                    0,
                ),
                "cooling_degree_c": max(
                    values["temperature_c"] - 20,
                    0,
                ),
                "irradiance_wm2": values["irradiance_wm2"],
                "cloud_cover_pct": values["cloud_cover_pct"],
                "wind_speed_mps": values["wind_speed_mps"],
                "wind_speed_squared": values["wind_speed_mps"] ** 2,
                "wind_speed_cubed": values["wind_speed_mps"] ** 3,
                "wind_direction_sin": np.sin(direction),
                "wind_direction_cos": np.cos(direction),
                "wind_gust_mps": values["wind_gust_mps"],
                "surface_pressure_hpa": values[
                    "surface_pressure_hpa"
                ],
                "sun_elevation_deg": self._sun_elevation(
                    valid,
                    float(site["latitude"]),
                ),
                "is_daylight": int(values["is_daylight"]),
                "lag_1": values["lag_1"],
                "lag_2": values["lag_2"],
                "lag_48": values["lag_48"],
                "lag_96": values["lag_96"],
                "lag_336": values["lag_336"],
                "rolling_mean_48": values["rolling_mean_48"],
                "rolling_std_48": values["rolling_std_48"],
                "rolling_same_period_mean": values[
                    "rolling_same_period_mean"
                ],
                "recent_residual": values["recent_residual"],
                "installed_capacity_mw": site[
                    "installed_capacity_mw"
                ],
                "latitude": site["latitude"],
                "longitude": site["longitude"],
                "archetype_code": ARCHETYPE_CODES[
                    str(site["business_archetype"])
                ],
                "technology_code": TECHNOLOGY_CODES[
                    str(site["technology"])
                ],
                "is_open": self._is_open(
                    str(site["business_archetype"]),
                    hour,
                ),
                "is_generation": int(site["site_role"] == "generation"),
                "is_solar": int(site["technology"] == "solar"),
                "is_wind": int(site["technology"] == "wind"),
                "valid_time_utc": valid,
            }
            output.append(record)
        return pd.DataFrame(output)

    def predict(
        self,
        *,
        site_id: str,
        issue_time: datetime,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        site = self.sites.ensure_site(site_id)
        try:
            metadata = self.repository.model_metadata(site_id)
            stack = ModelStack(
                statistical=self.repository.model(
                    site_id,
                    "statistical",
                ),
                point=self.repository.model(site_id, "point"),
                q10=self.repository.model(site_id, "q10"),
                q50=self.repository.model(site_id, "q50"),
                q90=self.repository.model(site_id, "q90"),
            )
        except Exception as error:
            if isinstance(error, APIError):
                raise
            raise APIError(
                503,
                "MODEL_UNAVAILABLE",
                "Saved model artifacts are unavailable.",
            ) from error
        frame = self._feature_frame(site, issue_time, rows)
        missing = set(FEATURE_COLUMNS) - set(frame.columns)
        if missing:
            raise APIError(
                422,
                "PREDICTION_FEATURES_UNAVAILABLE",
                "Complete prediction feature reconstruction is unavailable.",
                {"missing_features": sorted(missing)},
            )
        predictions = predict_model_stack(stack, frame, site)
        output = []
        for position, valid_time in enumerate(frame["valid_time_utc"]):
            output.append(
                {
                    "site_id": site_id,
                    "forecast_issue_time_utc": pd.Timestamp(
                        issue_time
                    ).isoformat(),
                    "valid_time_utc": valid_time.isoformat(),
                    "point_mwh": predictions["point_mwh"][position],
                    "q10_mwh": predictions["q10_mwh"][position],
                    "q50_mwh": predictions["q50_mwh"][position],
                    "q90_mwh": predictions["q90_mwh"][position],
                    "model_id": metadata["model_id"],
                    "model_version": metadata["model_version"],
                    "feature_version": metadata["feature_version"],
                    "units": "MWh",
                    "inference_only": True,
                }
            )
        return records(pd.DataFrame(output))
