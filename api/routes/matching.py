"""Renewable matching and map routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_repository
from api.schemas.common import ListEnvelope, ObjectEnvelope
from api.schemas.sites import GeoJSONFeatureCollection
from api.services.artifact_repository import ArtifactRepository
from api.services.matching_service import MatchingService
from api.services.site_service import SiteService

router = APIRouter(tags=["matching"])


@router.get(
    "/api/map/sites.geojson",
    response_model=GeoJSONFeatureCollection,
    summary="Get filtered map-ready site GeoJSON",
)
def site_geojson(
    technology: str | None = None,
    role: str | None = None,
    data_origin: str | None = None,
    modelled: bool | None = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return SiteService(repository).geojson(
        technology=technology,
        role=role,
        data_origin=data_origin,
        modelled=modelled,
    )


@router.get(
    "/api/map/matching-arcs",
    response_model=ListEnvelope,
    summary="Get bounded map-ready commercial matching arcs",
)
def map_arcs(
    timestamp: datetime | None = None,
    settlement_period: int | None = Query(default=None, ge=1, le=50),
    allocation_type: str | None = None,
    matching_mode: str | None = None,
    minimum_matched_mwh: float = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = MatchingService(repository).arcs(
        timestamp=timestamp,
        settlement_period=settlement_period,
        allocation_type=allocation_type,
        matching_mode=matching_mode,
        minimum_matched_mwh=minimum_matched_mwh,
        limit=limit,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": "MWh",
        },
        "warnings": [
            "Arcs are commercial allocations, not physical power flows."
        ],
    }


@router.get(
    "/api/matching/summary",
    response_model=ObjectEnvelope,
    summary="Get Phase 8 allocation methodology and headline metrics",
)
def summary(
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return {
        "data": MatchingService(repository).summary(),
        "meta": {},
        "warnings": [
            "Commercial/accounting matching only; not physical routing."
        ],
    }


@router.get(
    "/api/matching/periods",
    response_model=ListEnvelope,
    summary="Get period-level matching conservation metrics",
)
def periods(
    allocation_type: str | None = None,
    matching_mode: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = MatchingService(repository).periods(
        allocation_type=allocation_type,
        matching_mode=matching_mode,
        start=start,
        end=end,
        limit=limit,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": "MWh",
        },
        "warnings": [],
    }


@router.get(
    "/api/matching/allocations",
    response_model=ListEnvelope,
    summary="Get bounded generator-consumer allocation records",
)
def allocations(
    allocation_type: str = "realised",
    matching_mode: str = "local_preference",
    timestamp: datetime | None = None,
    settlement_period: int | None = Query(default=None, ge=1, le=50),
    minimum_matched_mwh: float = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = MatchingService(repository).allocations(
        allocation_type=allocation_type,
        matching_mode=matching_mode,
        timestamp=timestamp,
        settlement_period=settlement_period,
        minimum_matched_mwh=minimum_matched_mwh,
        limit=limit,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": "MWh",
        },
        "warnings": [],
    }


@router.get(
    "/api/matching/consumers",
    response_model=ListEnvelope,
    summary="Get consumer renewable-coverage summaries",
)
def consumers(
    allocation_type: str | None = None,
    matching_mode: str | None = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = MatchingService(repository).site_summary(
        "consumers",
        allocation_type,
        matching_mode,
    )
    return {
        "data": data,
        "meta": {"count": len(data), "units": "MWh"},
        "warnings": [],
    }


@router.get(
    "/api/matching/generators",
    response_model=ListEnvelope,
    summary="Get generator offtake-coverage summaries",
)
def generators(
    allocation_type: str | None = None,
    matching_mode: str | None = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = MatchingService(repository).site_summary(
        "generators",
        allocation_type,
        matching_mode,
    )
    return {
        "data": data,
        "meta": {"count": len(data), "units": "MWh"},
        "warnings": [],
    }


@router.get(
    "/api/matching/comparison",
    response_model=ListEnvelope,
    summary="Compare forecast and realised matching",
)
def comparison(
    matching_mode: str | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = MatchingService(repository).comparison(
        matching_mode,
        limit,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": "MWh",
        },
        "warnings": [],
    }
