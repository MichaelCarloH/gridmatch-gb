"""Public price and lightweight hedge-scenario services."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from api.errors import APIError
from api.services.artifact_repository import (
    ArtifactRepository,
    records,
    utc_timestamp,
)
from gridmatch.market.hedging import scenario_recommendation

MAX_ABSOLUTE_HEDGE_MWH = 10.0


class MarketService:
    def __init__(self, repository: ArtifactRepository) -> None:
        self.repository = repository

    def prices(
        self,
        price_source: str | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        frame = self.repository.parquet("prices")
        if price_source:
            if price_source not in {"market_index", "system_price"}:
                raise APIError(
                    400,
                    "INVALID_PRICE_SOURCE",
                    "price_source must be market_index or system_price.",
                )
            frame = frame[frame["price_source"] == price_source]
        columns = [
            "starttime",
            "settlementdate",
            "settlementperiod",
            "price_source",
            "dataprovider",
            "price",
            "volume",
            "systemsellprice",
            "systembuyprice",
            "data_origin",
        ]
        frame = frame[columns].sort_values(
            ["settlementdate", "settlementperiod", "price_source"]
        )
        total = len(frame)
        return records(frame.head(limit)), total

    def recommendations(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        fold: int | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        frame = self.repository.parquet("hedge_recommendations")
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
        if fold is not None:
            frame = frame[frame["validation_fold"] == fold]
        frame = frame.sort_values("timestamp_utc")
        total = len(frame)
        return records(frame.head(limit)), total

    def policy_summary(self) -> list[dict[str, Any]]:
        return records(self.repository.parquet("hedge_policy_metrics"))

    def sensitivity(self) -> list[dict[str, Any]]:
        return records(self.repository.parquet("hedge_sensitivity"))

    def simulate(
        self,
        *,
        timestamp_utc: datetime,
        forecast_model: str,
        short_cost_multiplier: float,
        long_value_multiplier: float,
        risk_preference: float,
    ) -> dict[str, Any]:
        timestamp = pd.Timestamp(timestamp_utc)
        if timestamp.tzinfo is None:
            raise APIError(
                422,
                "TIMEZONE_REQUIRED",
                "timestamp_utc must include a UTC offset.",
            )
        timestamp = timestamp.tz_convert("UTC")
        forecasts = self.repository.parquet("portfolio_forecasts")
        selected = forecasts[
            pd.to_datetime(forecasts["valid_time_utc"], utc=True)
            == timestamp
        ]
        if selected.empty:
            raise APIError(
                404,
                "FORECAST_TIMESTAMP_NOT_FOUND",
                "No portfolio forecast exists for timestamp_utc.",
            )
        prices = self.repository.parquet("hedge_recommendations")
        price_row = prices[
            pd.to_datetime(prices["timestamp_utc"], utc=True)
            == timestamp
        ]
        if price_row.empty:
            raise APIError(
                503,
                "PRICE_SCENARIO_UNAVAILABLE",
                "No price scenario exists for timestamp_utc.",
            )
        forecast = selected.iloc[0].to_dict()
        price = price_row.iloc[0]
        try:
            result = scenario_recommendation(
                forecast,
                market_reference_price_gbp_mwh=float(
                    price["market_reference_price_gbp_mwh"]
                ),
                public_system_price_gbp_mwh=float(
                    price["public_system_price_gbp_mwh"]
                ),
                short_cost_multiplier=short_cost_multiplier,
                long_value_multiplier=long_value_multiplier,
                risk_preference=risk_preference,
                forecast_model=forecast_model,
            )
        except ValueError as error:
            raise APIError(
                422,
                "INVALID_HEDGE_ASSUMPTIONS",
                str(error),
            ) from error
        if abs(float(result["recommended_mwh"])) > MAX_ABSOLUTE_HEDGE_MWH:
            raise APIError(
                422,
                "HEDGE_LIMIT_EXCEEDED",
                "Recommended hedge exceeds the demo operational limit.",
                {"maximum_absolute_mwh": MAX_ABSOLUTE_HEDGE_MWH},
            )
        prefix = f"{forecast_model}_net"
        return {
            "timestamp_utc": timestamp.isoformat(),
            "selected_quantile": result["recommended_quantile"],
            "forecast_distribution": {
                "q10_mwh": forecast[f"{prefix}_q10_mwh"],
                "q50_mwh": forecast[f"{prefix}_q50_mwh"],
                "q90_mwh": forecast[f"{prefix}_q90_mwh"],
            },
            "recommended_hedge_mwh": result["recommended_mwh"],
            "expected_short_exposure_mwh": result[
                "expected_short_exposure_mwh"
            ],
            "expected_long_exposure_mwh": result[
                "expected_long_exposure_mwh"
            ],
            "reference_price_gbp_mwh": result[
                "market_reference_price_gbp_mwh"
            ],
            "system_price_gbp_mwh": result[
                "public_system_price_gbp_mwh"
            ],
            "assumptions": {
                "short_cost_multiplier": short_cost_multiplier,
                "long_value_multiplier": long_value_multiplier,
                "risk_preference": risk_preference,
                "operational_limit_absolute_mwh": (
                    MAX_ABSOLUTE_HEDGE_MWH
                ),
            },
            "forecast_model": forecast_model,
            "model_version": "hedge-decision-v1",
            "warnings": [
                "Public prices are a non-contemporaneous scenario proxy.",
                "This endpoint does not run a historical backtest.",
            ],
            "disclaimer": (
                "Scenario-only prototype output; not realised savings, "
                "financial advice or a trade instruction."
            ),
        }
