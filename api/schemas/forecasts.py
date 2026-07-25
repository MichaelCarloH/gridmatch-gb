"""Site forecast and compact prediction schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from api.schemas.common import APIModel, ListEnvelope


class PredictionFeatureRow(APIModel):
    valid_time_utc: datetime
    settlement_period: int = Field(ge=1, le=50)
    temperature_c: float = Field(ge=-50, le=60)
    irradiance_wm2: float = Field(ge=0, le=1500)
    cloud_cover_pct: float = Field(ge=0, le=100)
    wind_speed_mps: float = Field(ge=0, le=60)
    wind_direction_deg: float = Field(ge=0, le=360)
    wind_gust_mps: float = Field(ge=0, le=90)
    surface_pressure_hpa: float = Field(ge=850, le=1100)
    is_daylight: bool
    lag_1: float
    lag_2: float
    lag_48: float
    lag_96: float
    lag_336: float
    rolling_mean_48: float
    rolling_std_48: float = Field(ge=0)
    rolling_same_period_mean: float
    recent_residual: float

    @field_validator(
        "lag_1",
        "lag_2",
        "lag_48",
        "lag_96",
        "lag_336",
        "rolling_mean_48",
        "rolling_same_period_mean",
        "recent_residual",
    )
    @classmethod
    def finite_feature(cls, value: float) -> float:
        if not float("-inf") < value < float("inf"):
            raise ValueError("Feature values must be finite")
        return value


class PredictionRequest(APIModel):
    site_id: str
    forecast_issue_time_utc: datetime
    rows: list[PredictionFeatureRow] = Field(min_length=1, max_length=48)


class PredictionResponse(ListEnvelope):
    pass
