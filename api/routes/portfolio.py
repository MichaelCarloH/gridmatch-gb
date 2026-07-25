"""Portfolio forecast and metric routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_repository
from api.schemas.common import ListEnvelope, ObjectEnvelope
from api.services.artifact_repository import ArtifactRepository
from api.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get(
    "/forecast",
    response_model=ListEnvelope,
    summary="Get portfolio demand, generation and net forecasts",
)
def forecast(
    method: str = "reconciled",
    start: datetime | None = None,
    end: datetime | None = None,
    fold: int | None = Query(default=None, ge=1),
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = PortfolioService(repository).forecast(
        method=method,
        start=start,
        end=end,
        fold=fold,
        limit=limit,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": "MWh",
            "method": method,
        },
        "warnings": (
            ["Baseline forecasts do not provide quantile intervals."]
            if method == "baseline"
            else []
        ),
    }


@router.get(
    "/metrics",
    response_model=ListEnvelope,
    summary="Get portfolio forecast comparison metrics",
)
def metrics(
    method: str | None = None,
    target: str | None = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = PortfolioService(repository).metrics(
        method=method,
        target=target,
    )
    return {
        "data": data,
        "meta": {"count": len(data), "units": "MWh"},
        "warnings": [],
    }


@router.get(
    "/error-attribution",
    response_model=ListEnvelope,
    summary="Get forecast-error contribution by site, technology or region",
)
def attribution(
    level: str = "site",
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = PortfolioService(repository).attribution(level)
    return {
        "data": data,
        "meta": {"count": len(data), "units": "MWh"},
        "warnings": [],
    }


@router.get(
    "/correlation",
    response_model=ObjectEnvelope,
    summary="Get the site forecast-error correlation matrix",
)
def correlation(
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return {
        "data": PortfolioService(repository).correlation(),
        "meta": {},
        "warnings": [],
    }
