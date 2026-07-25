"""Research notebook metadata routes."""

from fastapi import APIRouter, Depends

from api.dependencies import get_repository
from api.schemas.research import NotebookListResponse, NotebookResponse
from api.services.artifact_repository import ArtifactRepository
from api.services.research_service import ResearchService

router = APIRouter(prefix="/api/research", tags=["research"])


@router.get(
    "/notebooks",
    response_model=NotebookListResponse,
    summary="List allowlisted executed research notebooks",
)
def notebooks(
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    data = ResearchService(repository).list_notebooks()
    return {
        "data": data,
        "meta": {"count": len(data)},
        "warnings": [],
    }


@router.get(
    "/notebooks/{notebook_id}",
    response_model=NotebookResponse,
    summary="Get metadata for one allowlisted notebook",
)
def notebook(
    notebook_id: str,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict:
    return {
        "data": ResearchService(repository).notebook(notebook_id),
        "meta": {},
        "warnings": [],
    }
