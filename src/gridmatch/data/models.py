"""Typed Phase 4 domain schemas.

Physical anomalies are intentionally not rejected here: boundary schemas establish
types and units, while the quality layer flags invalid values without dropping them.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DataOrigin = Literal["public", "simulated", "uploaded"]
SiteRole = Literal["demand", "generation", "hybrid"]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, protected_namespaces=())


class SiteSchema(StrictSchema):
    site_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    site_role: SiteRole
    technology: str
    business_archetype: str | None = None
    operator: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    postcode: str | None = None
    region: str | None = None
    installed_capacity_mw: float | None = Field(default=None, ge=0)
    bmu_id: str | None = None
    repd_id: str | None = None
    data_origin: DataOrigin
    status: str = "active"


class ObservationSchema(StrictSchema):
    site_id: str
    timestamp_utc: datetime
    settlement_date: date
    settlement_period: int = Field(ge=1, le=50)
    consumption_mwh: float | None = None
    generation_mwh: float | None = None
    actual_mwh: float
    quality_flag: str = "unchecked"
    source: str
    retrieved_at: datetime

    _timestamp_to_utc = field_validator("timestamp_utc", "retrieved_at")(_utc)


class ForecastSchema(StrictSchema):
    site_id: str
    issue_time_utc: datetime
    valid_time_utc: datetime
    settlement_date: date
    settlement_period: int = Field(ge=1, le=50)
    horizon_periods: int = Field(ge=1)
    model_id: str
    model_version: str
    q10_mwh: float
    q50_mwh: float
    q90_mwh: float
    point_mwh: float
    actual_mwh: float | None = None

    _times_to_utc = field_validator("issue_time_utc", "valid_time_utc")(_utc)

    @model_validator(mode="after")
    def quantiles_are_ordered(self) -> "ForecastSchema":
        if not self.q10_mwh <= self.q50_mwh <= self.q90_mwh:
            raise ValueError("forecast quantiles must satisfy q10 <= q50 <= q90")
        if self.valid_time_utc <= self.issue_time_utc:
            raise ValueError("valid_time_utc must be after issue_time_utc")
        return self


class WeatherSchema(StrictSchema):
    site_id: str
    issue_time_utc: datetime
    valid_time_utc: datetime
    temperature_2m: float
    cloud_cover: float = Field(ge=0, le=100)
    shortwave_radiation: float = Field(ge=0)
    wind_speed_10m: float = Field(ge=0)
    wind_speed_100m: float = Field(ge=0)
    wind_direction_100m: float = Field(ge=0, le=360)
    pressure: float = Field(gt=0)
    weather_model: str

    _times_to_utc = field_validator("issue_time_utc", "valid_time_utc")(_utc)


class PriceSchema(StrictSchema):
    timestamp_utc: datetime
    settlement_date: date
    settlement_period: int = Field(ge=1, le=50)
    market_index_price_gbp_mwh: float | None = None
    system_price_gbp_mwh: float | None = None
    source: str

    _timestamp_to_utc = field_validator("timestamp_utc")(_utc)
