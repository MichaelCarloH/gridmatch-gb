"""Allowlisted research notebook metadata service."""

from __future__ import annotations

from typing import Any

from api.errors import APIError
from api.services.artifact_repository import ArtifactRepository, json_safe


class ResearchService:
    def __init__(self, repository: ArtifactRepository) -> None:
        self.repository = repository

    def list_notebooks(self) -> list[dict[str, Any]]:
        return json_safe(self.repository.json("notebooks"))

    def notebook(self, notebook_id: str) -> dict[str, Any]:
        selected = [
            item
            for item in self.list_notebooks()
            if item["name"] == notebook_id
        ]
        if not selected:
            raise APIError(
                404,
                "NOTEBOOK_NOT_FOUND",
                "Unknown notebook_id.",
                {"notebook_id": notebook_id},
            )
        return selected[0]
