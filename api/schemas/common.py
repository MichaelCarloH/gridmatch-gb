"""Shared API response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResponseMeta(APIModel):
    count: int = 0
    limit: int | None = None
    offset: int | None = None
    units: str | dict[str, str] | None = None
    method: str | None = None


class ListEnvelope(APIModel):
    data: list[dict[str, Any]]
    meta: ResponseMeta
    warnings: list[str] = Field(default_factory=list)


class ObjectEnvelope(APIModel):
    data: dict[str, Any]
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(APIModel):
    status: str
    application_version: str
    artifact_availability: dict[str, bool]
    model_registry_available: bool
    demo_mode: bool
    last_artifact_update: str | None


class MetaResponse(APIModel):
    data: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
