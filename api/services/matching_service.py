"""Renewable allocation and map-arc services."""

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


class MatchingService:
    def __init__(self, repository: ArtifactRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate(
        allocation_type: str | None,
        matching_mode: str | None,
    ) -> None:
        if allocation_type and allocation_type not in {
            "forecast",
            "realised",
        }:
            raise APIError(
                400,
                "INVALID_ALLOCATION_TYPE",
                "allocation_type must be forecast or realised.",
            )
        if matching_mode and matching_mode not in {
            "maximum_match",
            "local_preference",
        }:
            raise APIError(
                400,
                "INVALID_MATCHING_MODE",
                "Unsupported matching_mode.",
            )

    def summary(self) -> dict[str, Any]:
        return self.repository.json("matching_summary")

    def periods(
        self,
        *,
        allocation_type: str | None,
        matching_mode: str | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self._validate(allocation_type, matching_mode)
        start_utc = utc_timestamp(start, "start") if start else None
        end_utc = utc_timestamp(end, "end") if end else None
        if start_utc is not None and end_utc is not None:
            if start_utc > end_utc:
                raise APIError(
                    400,
                    "INVALID_DATE_RANGE",
                    "start must be before or equal to end.",
                )
        frame = self.repository.parquet("matching_periods")
        if allocation_type:
            frame = frame[frame["allocation_type"] == allocation_type]
        if matching_mode:
            frame = frame[frame["matching_mode"] == matching_mode]
        timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True)
        if start_utc is not None:
            frame = frame[timestamps >= start_utc]
            timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True)
        if end_utc is not None:
            frame = frame[timestamps <= end_utc]
        frame = frame.sort_values("timestamp_utc")
        total = len(frame)
        return records(frame.head(limit)), total

    def allocations(
        self,
        *,
        allocation_type: str,
        matching_mode: str,
        timestamp: datetime | None,
        settlement_period: int | None,
        minimum_matched_mwh: float,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self._validate(allocation_type, matching_mode)
        logical = (
            "matching_forecast"
            if allocation_type == "forecast"
            else "matching_realised"
        )
        frame = self.repository.parquet(logical)
        frame = frame[frame["matching_mode"] == matching_mode]
        if timestamp:
            target = utc_timestamp(timestamp, "timestamp")
            frame = frame[
                pd.to_datetime(frame["timestamp_utc"], utc=True) == target
            ]
        if settlement_period is not None:
            frame = frame[
                frame["settlement_period"] == settlement_period
            ]
        frame = frame[
            frame["matched_mwh"] >= minimum_matched_mwh
        ].sort_values(
            ["timestamp_utc", "generator_site_id", "consumer_site_id"]
        )
        total = len(frame)
        return records(frame.head(limit)), total

    def site_summary(
        self,
        kind: str,
        allocation_type: str | None,
        matching_mode: str | None,
    ) -> list[dict[str, Any]]:
        self._validate(allocation_type, matching_mode)
        logical = (
            "matching_consumers"
            if kind == "consumers"
            else "matching_generators"
        )
        frame = self.repository.parquet(logical)
        if allocation_type:
            frame = frame[frame["allocation_type"] == allocation_type]
        if matching_mode:
            frame = frame[frame["matching_mode"] == matching_mode]
        return records(frame)

    def comparison(
        self,
        matching_mode: str | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self._validate(None, matching_mode)
        frame = self.repository.parquet("matching_comparison")
        if matching_mode:
            frame = frame[frame["matching_mode"] == matching_mode]
        total = len(frame)
        return records(frame.head(limit)), total

    def arcs(
        self,
        *,
        timestamp: datetime | None,
        settlement_period: int | None,
        allocation_type: str | None,
        matching_mode: str | None,
        minimum_matched_mwh: float,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self._validate(allocation_type, matching_mode)
        frame = self.repository.parquet("map_arcs")
        if timestamp:
            target = utc_timestamp(timestamp, "timestamp")
            frame = frame[
                pd.to_datetime(frame["timestamp_utc"], utc=True) == target
            ]
        if settlement_period is not None:
            frame = frame[
                frame["settlement_period"] == settlement_period
            ]
        if allocation_type:
            frame = frame[frame["allocation_type"] == allocation_type]
        if matching_mode:
            frame = frame[frame["matching_mode"] == matching_mode]
        frame = frame[
            frame["matched_mwh"] >= minimum_matched_mwh
        ]
        total = len(frame)
        return records(frame.head(limit)), total
