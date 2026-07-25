"""Portfolio forecast, metric and error-attribution services."""

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


class PortfolioService:
    def __init__(self, repository: ArtifactRepository) -> None:
        self.repository = repository

    def forecast(
        self,
        *,
        method: str,
        start: datetime | None,
        end: datetime | None,
        fold: int | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        if method not in {
            "baseline",
            "bottom_up",
            "direct",
            "reconciled",
        }:
            raise APIError(
                400,
                "UNSUPPORTED_FORECAST_METHOD",
                "Unsupported portfolio forecast method.",
                {"method": method},
            )
        if start and end and start > end:
            raise APIError(
                400,
                "INVALID_DATE_RANGE",
                "start must not be after end.",
            )
        frame = self.repository.parquet("portfolio_forecasts")
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
        rows = []
        for row in frame.sort_values("valid_time_utc").itertuples(index=False):
            record: dict[str, Any] = {
                "issue_time_utc": row.issue_time_utc,
                "valid_time_utc": row.valid_time_utc,
                "settlement_date": str(row.settlement_date),
                "settlement_period": int(row.settlement_period),
                "validation_fold": int(row.validation_fold),
                "method": method,
                "model_version": row.portfolio_model_version,
                "units": "MWh",
            }
            for target in ("demand", "generation", "net"):
                record[f"actual_{target}_mwh"] = getattr(
                    row,
                    f"actual_{target}_mwh",
                )
                if method == "baseline":
                    record[f"{target}_point_mwh"] = getattr(
                        row,
                        f"baseline_{target}_mwh",
                    )
                    record[f"{target}_q10_mwh"] = None
                    record[f"{target}_q50_mwh"] = None
                    record[f"{target}_q90_mwh"] = None
                else:
                    record[f"{target}_point_mwh"] = getattr(
                        row,
                        f"{method}_{target}_point_mwh",
                    )
                    for quantile in ("q10", "q50", "q90"):
                        record[f"{target}_{quantile}_mwh"] = getattr(
                            row,
                            f"{method}_{target}_{quantile}_mwh",
                        )
            rows.append(record)
        total = len(rows)
        return records(pd.DataFrame(rows).head(limit)), total

    def metrics(
        self,
        *,
        method: str | None,
        target: str | None,
    ) -> list[dict[str, Any]]:
        frame = self.repository.parquet("portfolio_metrics")
        if method:
            frame = frame[frame["method"] == method]
        if target:
            frame = frame[frame["target"] == target]
        return records(frame)

    def attribution(self, level: str) -> list[dict[str, Any]]:
        logical = {
            "site": "portfolio_attribution_site",
            "technology": "portfolio_attribution_technology",
            "region": "portfolio_attribution_region",
        }.get(level)
        if not logical:
            raise APIError(
                400,
                "INVALID_ATTRIBUTION_LEVEL",
                "level must be site, technology or region.",
            )
        return records(self.repository.parquet(logical))

    def correlation(self) -> dict[str, Any]:
        frame = self.repository.parquet("portfolio_correlation")
        return {
            "site_ids": list(frame.columns),
            "matrix": frame.astype(float).values.tolist(),
        }
