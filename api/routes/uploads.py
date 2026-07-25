"""In-memory CSV upload-validation route."""

from fastapi import APIRouter, Depends, File, UploadFile

from api.dependencies import Settings, get_app_settings
from api.schemas.uploads import UploadValidationResponse
from api.services.upload_service import UploadService

router = APIRouter(prefix="/api/upload", tags=["uploads"])


@router.post(
    "/validate",
    response_model=UploadValidationResponse,
    summary="Validate a bounded meter CSV without permanent storage",
)
async def validate_upload(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_app_settings),
) -> dict:
    content = await file.read(settings.upload_max_bytes + 1)
    result = UploadService(settings.upload_max_bytes).validate(
        filename=file.filename,
        content_type=file.content_type,
        content=content,
    )
    return {
        "data": result,
        "meta": {"units": {"input": "kWh", "output": "MWh"}},
        "warnings": [
            "Validation is in memory; the upload is not retained."
        ],
    }
