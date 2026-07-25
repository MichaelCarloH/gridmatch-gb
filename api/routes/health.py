"""Health and service metadata routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_repository
from api.schemas.common import HealthResponse, MetaResponse
from api.services.artifact_repository import ArtifactRepository

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service and required artifact availability",
)
def health(
    request: Request,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    settings = request.app.state.settings
    availability = repository.availability()
    healthy = all(availability.values())
    return {
        "status": "healthy" if healthy else "degraded",
        "application_version": "0.1.0",
        "artifact_availability": availability,
        "model_registry_available": availability["model_registry"],
        "demo_mode": settings.demo_mode,
        "last_artifact_update": repository.last_artifact_update(),
    }


@router.get(
    "/api/meta",
    response_model=MetaResponse,
    summary="Describe API capabilities and serving constraints",
)
def metadata(request: Request) -> dict:
    return {
        "data": {
            "name": "GridMatch GB API",
            "version": "0.1.0",
            "openapi_url": str(request.app.openapi_url),
            "documentation_url": str(request.app.docs_url),
            "timestamp_display_timezone": "Europe/London",
            "timestamp_storage_timezone": "UTC",
            "heavy_operations_offline": [
                "data collection",
                "model training",
                "historical backtesting",
                "notebook execution",
            ],
            "disclaimer": (
                "Independent demonstration using simulated portfolio data; "
                "not a supplier settlement or trading system."
            ),
        },
        "warnings": [],
    }
