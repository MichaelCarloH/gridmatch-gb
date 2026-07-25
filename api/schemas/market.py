"""Market and hedge request schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from api.schemas.common import APIModel

ForecastModel = Literal["bottom_up", "direct", "reconciled"]


class HedgeSimulationRequest(APIModel):
    timestamp_utc: datetime
    forecast_model: ForecastModel = "bottom_up"
    short_cost_multiplier: float = Field(default=1.35, ge=1, le=5)
    long_value_multiplier: float = Field(default=0.65, ge=0, le=1)
    risk_preference: float = Field(default=0, ge=0, le=1)

    @field_validator(
        "short_cost_multiplier",
        "long_value_multiplier",
        "risk_preference",
    )
    @classmethod
    def finite_number(cls, value: float) -> float:
        if not float("-inf") < value < float("inf"):
            raise ValueError("Values must be finite")
        return value
