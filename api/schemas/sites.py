"""Site response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from api.schemas.common import APIModel


class SiteRecord(APIModel):
    site_id: str
    name: str
    site_role: Literal["demand", "generation"]
    technology: str
    business_archetype: str
    latitude: float
    longitude: float
    installed_capacity_mw: float
    region: str
    data_origin: Literal["simulated", "public", "uploaded"]
    quality_score: float | None = None
    site_readiness: str | None = None
    modelled: bool = False


class GeoJSONFeatureCollection(APIModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict]
    bbox: list[float] | None = Field(default=None, min_length=4, max_length=4)
