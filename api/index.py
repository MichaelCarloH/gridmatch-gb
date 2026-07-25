"""GridMatch GB typed artifact-serving FastAPI application."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.dependencies import Settings, get_settings
from api.errors import install_error_handlers
from api.routes import (
    health,
    market,
    matching,
    models,
    portfolio,
    research,
    sites,
    uploads,
)
from api.services.artifact_repository import ArtifactRepository

DESCRIPTION = """
Artifact-backed API for the independent GridMatch GB research prototype.

The service exposes simulated site and portfolio data, out-of-sample forecast
artifacts, commercial renewable allocations and scenario-only hedge decisions.
It never trains models, runs historical backtests, downloads public data or
executes notebooks inside a request.

Hedge GBP values use a non-contemporaneous public price-reference scenario and
are not realised savings, financial advice or trade instructions. Matching
arcs are commercial allocations, not physical electricity paths.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings or get_settings()
    application = FastAPI(
        title="GridMatch GB API",
        version="0.1.0",
        description=DESCRIPTION,
        docs_url="/docs",
        openapi_url="/openapi.json",
        contact={
            "name": "GridMatch independent prototype",
        },
        license_info={
            "name": "Prototype repository terms",
        },
    )
    application.state.settings = configuration
    application.state.repository = ArtifactRepository(configuration)
    application.state.startup_missing_artifacts = [
        logical_id
        for logical_id, available in (
            application.state.repository.availability().items()
        )
        if not available
    ]
    origins = [
        origin
        for origin in configuration.cors_origins
        if origin != "*"
    ]
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    @application.middleware("http")
    async def enforce_response_limit(request: Request, call_next):
        raw_limit = request.query_params.get("limit")
        if raw_limit:
            try:
                limit = int(raw_limit)
            except ValueError:
                limit = 0
            if limit > configuration.max_response_rows:
                return JSONResponse(
                    status_code=422,
                    content={
                        "error": {
                            "code": "RESPONSE_LIMIT_EXCEEDED",
                            "message": (
                                "Requested limit exceeds the configured "
                                "maximum."
                            ),
                            "details": {
                                "maximum_rows": (
                                    configuration.max_response_rows
                                )
                            },
                        }
                    },
                )
        return await call_next(request)

    install_error_handlers(application)
    application.include_router(health.router)
    application.include_router(sites.router)
    application.include_router(portfolio.router)
    application.include_router(matching.router)
    application.include_router(market.router)
    application.include_router(market.compatibility_router)
    application.include_router(uploads.router)
    application.include_router(research.router)
    application.include_router(models.router)
    return application


app = create_app()
