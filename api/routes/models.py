"""Model registry and compact saved-model inference routes."""

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_repository
from api.schemas.forecasts import PredictionRequest, PredictionResponse
from api.schemas.models import ModelListResponse, ModelResponse
from api.services.artifact_repository import ArtifactRepository
from api.services.model_service import ModelService

router = APIRouter(tags=["models"])


@router.get(
    "/api/models",
    response_model=ModelListResponse,
    summary="List logical model-registry records",
)
def models(
    site_id: str | None = None,
    algorithm: str | None = None,
    target: str | None = None,
    quantile: float | None = Query(default=None, ge=0, le=1),
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data, total = ModelService(repository).list_models(
        site_id=site_id,
        algorithm=algorithm,
        target=target,
        quantile=quantile,
        status=status,
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
        "warnings": [
            "Artifact paths are logical identifiers, not filesystem paths."
        ],
    }


@router.get(
    "/api/models/{model_id}",
    response_model=ModelResponse,
    summary="Get one logical model-registry record",
)
def model(
    model_id: str,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return {
        "data": ModelService(repository).get_model(model_id),
        "meta": {},
        "warnings": [],
    }


@router.post(
    "/api/forecast/predict",
    response_model=PredictionResponse,
    summary="Run bounded inference with an existing saved site model",
    description=(
        "Requires explicit compact weather/calendar and lag inputs. "
        "Loads saved estimators only; no training or network access."
    ),
)
def predict(
    request: PredictionRequest,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = ModelService(repository).predict(
        site_id=request.site_id,
        issue_time=request.forecast_issue_time_utc,
        rows=[
            item.model_dump()
            for item in request.rows
        ],
    )
    return {
        "data": data,
        "meta": {
            "count": len(data),
            "limit": 48,
            "offset": 0,
            "units": "MWh",
        },
        "warnings": [
            "Compact demonstration inference requires caller-supplied lag features.",
            "Weather inputs must represent information available at issue time.",
        ],
    }
