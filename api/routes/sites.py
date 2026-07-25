"""Site, observations, quality, forecast and model-card routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_repository
from api.schemas.common import ListEnvelope, ObjectEnvelope
from api.services.artifact_repository import ArtifactRepository
from api.services.site_service import SiteService

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("", response_model=ListEnvelope, summary="List demo sites")
def list_sites(
    role: str | None = None,
    technology: str | None = None,
    archetype: str | None = None,
    region: str | None = None,
    data_origin: str | None = None,
    status: str | None = None,
    ready: bool | None = None,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = SiteService(repository).list_sites(
        role=role,
        technology=technology,
        archetype=archetype,
        region=region,
        data_origin=data_origin,
        status=status,
        ready=ready,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": offset,
        },
        "warnings": [],
    }


@router.get(
    "/{site_id}",
    response_model=ObjectEnvelope,
    summary="Get one site's metadata",
)
def get_site(
    site_id: str,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return {
        "data": SiteService(repository).get_site(site_id),
        "meta": {},
        "warnings": [],
    }


@router.get(
    "/{site_id}/observations",
    response_model=ListEnvelope,
    summary="Get bounded half-hourly site observations",
)
def observations(
    site_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
    quality_flag: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = SiteService(repository).observations(
        site_id,
        start=start,
        end=end,
        quality_flag=quality_flag,
        limit=limit,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": {
                "energy_mwh": "MWh",
                "observed_power_mw": "MW",
            },
        },
        "warnings": [],
    }


@router.get(
    "/{site_id}/quality",
    response_model=ObjectEnvelope,
    summary="Get site readiness and data-quality evidence",
)
def quality(
    site_id: str,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return {
        "data": SiteService(repository).quality(site_id),
        "meta": {},
        "warnings": [],
    }


@router.get(
    "/{site_id}/forecast",
    response_model=ListEnvelope,
    summary="Get out-of-sample site forecast distributions",
)
def forecast(
    site_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
    fold: int | None = Query(default=None, ge=1),
    model: str = "ml",
    limit: int = Query(default=500, ge=1, le=1000),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = SiteService(repository).forecast(
        site_id,
        start=start,
        end=end,
        fold=fold,
        model=model,
        limit=limit,
    )
    return {
        "data": data,
        "meta": {
            "count": total,
            "limit": limit,
            "offset": 0,
            "units": "MWh",
            "method": model,
        },
        "warnings": [],
    }


@router.get(
    "/{site_id}/metrics",
    response_model=ListEnvelope,
    summary="Get site model and baseline metrics",
)
def metrics(
    site_id: str,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = SiteService(repository).metrics(site_id)
    return {
        "data": data,
        "meta": {"count": len(data), "units": "MWh"},
        "warnings": [],
    }


@router.get(
    "/{site_id}/alerts",
    response_model=ListEnvelope,
    summary="Get artifact-derived site data-quality alerts",
)
def alerts(
    site_id: str,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = SiteService(repository).alerts(site_id)
    return {
        "data": data,
        "meta": {"count": len(data)},
        "warnings": [],
    }


@router.get(
    "/{site_id}/model-card",
    response_model=ObjectEnvelope,
    summary="Get the allowlisted site model card",
)
def model_card(
    site_id: str,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return {
        "data": SiteService(repository).model_card(site_id),
        "meta": {},
        "warnings": [],
    }
