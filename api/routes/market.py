"""Public market-price and hedge-scenario routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_repository
from api.schemas.common import ListEnvelope, ObjectEnvelope
from api.schemas.market import HedgeSimulationRequest
from api.services.artifact_repository import ArtifactRepository
from api.services.market_service import MarketService

router = APIRouter(prefix="/api/market", tags=["market and hedge"])
compatibility_router = APIRouter(tags=["market and hedge"])


@router.get(
    "/prices",
    response_model=ListEnvelope,
    summary="Get the cached public Elexon price snapshot",
)
def prices(
    price_source: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = MarketService(repository).prices(price_source, limit)
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": "GBP/MWh",
        },
        "warnings": [
            "The public snapshot is non-contemporaneous with the volume backtest."
        ],
    }


@router.get(
    "/hedge-recommendations",
    response_model=ListEnvelope,
    summary="Get leakage-aware historical hedge recommendations",
)
def recommendations(
    start: datetime | None = None,
    end: datetime | None = None,
    fold: int | None = Query(default=None, ge=1),
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = MarketService(repository).recommendations(
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
            "units": {"volume": "MWh", "cost": "GBP"},
        },
        "warnings": [
            "Scenario costs are not realised supplier savings."
        ],
    }


@router.get(
    "/policy-summary",
    response_model=ListEnvelope,
    summary="Compare hedge-policy cost and risk metrics",
)
def policy_summary(
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = MarketService(repository).policy_summary()
    return {
        "data": data,
        "meta": {"count": len(data), "units": "GBP"},
        "warnings": [
            "Perfect foresight is an unattainable lower bound only."
        ],
    }


@router.get(
    "/sensitivity",
    response_model=ListEnvelope,
    summary="Get short/long cost-assumption sensitivity",
)
def sensitivity(
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = MarketService(repository).sensitivity()
    return {
        "data": data,
        "meta": {"count": len(data), "units": "GBP"},
        "warnings": [],
    }


@router.post(
    "/hedge-simulate",
    response_model=ObjectEnvelope,
    summary="Recompute one lightweight hedge scenario",
    description=(
        "Uses saved Phase 7 quantiles and the Phase 9 scenario function. "
        "It does not retrain or rerun the historical backtest."
    ),
)
def hedge_simulate(
    request: HedgeSimulationRequest,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    result = MarketService(repository).simulate(
        timestamp_utc=request.timestamp_utc,
        forecast_model=request.forecast_model,
        short_cost_multiplier=request.short_cost_multiplier,
        long_value_multiplier=request.long_value_multiplier,
        risk_preference=request.risk_preference,
    )
    warnings = result.pop("warnings")
    return {
        "data": result,
        "meta": {"units": {"volume": "MWh", "price": "GBP/MWh"}},
        "warnings": warnings,
    }


@compatibility_router.post(
    "/api/hedge/simulate",
    response_model=ObjectEnvelope,
    summary="Recompute one hedge scenario (compatibility route)",
)
def legacy_hedge_simulate(
    request: HedgeSimulationRequest,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return hedge_simulate(request, repository)
