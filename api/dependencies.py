"""Typed API configuration and dependency providers."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from api.services.artifact_repository import ArtifactRepository

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseModel):
    """Environment-backed API settings with safe local defaults."""

    model_config = ConfigDict(frozen=True)

    data_dir: Path = PROJECT_ROOT / "data"
    artifact_dir: Path = PROJECT_ROOT / "artifacts"
    demo_mode: bool = True
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    max_response_rows: int = Field(default=1000, ge=1, le=10_000)
    model_cache_size: int = Field(default=8, ge=1, le=64)
    upload_max_bytes: int = Field(
        default=2_000_000,
        ge=10_000,
        le=20_000_000,
    )

    @classmethod
    def from_environment(cls) -> "Settings":
        origins = tuple(
            value.strip()
            for value in os.getenv(
                "GRIDMATCH_CORS_ORIGINS",
                "http://localhost:3000",
            ).split(",")
            if value.strip()
        )
        return cls(
            data_dir=Path(
                os.getenv("GRIDMATCH_DATA_DIR", PROJECT_ROOT / "data")
            ),
            artifact_dir=Path(
                os.getenv(
                    "GRIDMATCH_ARTIFACT_DIR",
                    PROJECT_ROOT / "artifacts",
                )
            ),
            demo_mode=os.getenv(
                "GRIDMATCH_DEMO_MODE",
                "true",
            ).lower()
            in {"1", "true", "yes"},
            cors_origins=origins,
            max_response_rows=int(
                os.getenv("GRIDMATCH_MAX_RESPONSE_ROWS", "1000")
            ),
            model_cache_size=int(
                os.getenv("GRIDMATCH_MODEL_CACHE_SIZE", "8")
            ),
            upload_max_bytes=int(
                os.getenv("GRIDMATCH_UPLOAD_MAX_BYTES", "2000000")
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_environment()


def get_repository(request: Request) -> "ArtifactRepository":
    return request.app.state.repository


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings
