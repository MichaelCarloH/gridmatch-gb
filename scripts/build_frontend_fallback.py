"""Build compact browser fallback bundles from the existing API artifacts."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit

import pandas as pd
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.index import app


OUTPUT_ROOT = ROOT / "public" / "demo-data" / "fallback"
FORECAST_ARTIFACT = ROOT / "artifacts" / "forecasts" / "portfolio_forecasts.parquet"


def canonical_path(path: str) -> str:
    parts = urlsplit(path)
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return f"{parts.path}{f'?{query}' if query else ''}"


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )


def base_routes() -> dict[str, list[str]]:
    return {
        "core.json": [
            "/health",
            "/api/meta",
            "/api/sites?limit=100",
            "/api/models?limit=1",
        ],
        "portfolio.json": [
            "/api/portfolio/forecast?method=reconciled&limit=48",
            *[
                f"/api/portfolio/forecast?method={method}&limit=96"
                for method in ("baseline", "bottom_up", "direct", "reconciled")
            ],
            "/api/portfolio/metrics",
            "/api/portfolio/metrics?method=reconciled",
            "/api/portfolio/error-attribution?level=site",
            "/api/portfolio/correlation",
        ],
        "market.json": [
            "/api/market/prices?limit=58",
            "/api/market/hedge-recommendations?limit=48",
            "/api/market/hedge-recommendations?limit=96",
            "/api/market/policy-summary",
        ],
        "research.json": [
            "/api/research/notebooks",
            "/api/models?limit=12",
        ],
        "map.json": [
            "/api/map/sites.geojson",
            (
                "/api/map/matching-arcs?settlement_period=1"
                "&allocation_type=realised"
                "&matching_mode=local_preference"
                "&minimum_matched_mwh=0.01"
                "&limit=200"
            ),
        ],
        "matching.json": [
            "/api/matching/summary",
            (
                "/api/matching/consumers?allocation_type=realised"
                "&matching_mode=local_preference"
            ),
            (
                "/api/matching/generators?allocation_type=realised"
                "&matching_mode=local_preference"
            ),
        ],
        "sites.json": [],
    }


def fetch_json(client: TestClient, path: str) -> object:
    response = client.get(path)
    if response.status_code != 200:
        raise RuntimeError(f"{path} returned {response.status_code}: {response.text[:300]}")
    return response.json()


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    routes = base_routes()
    bundles: dict[str, dict[str, object]] = defaultdict(dict)
    index_routes: dict[str, dict[str, str]] = {}

    with TestClient(app) as client:
        sites_response = fetch_json(client, "/api/sites?limit=100")
        site_ids = [row["site_id"] for row in sites_response["data"]]
        for site_id in site_ids:
            routes["sites.json"].extend(
                [
                    f"/api/sites/{site_id}",
                    f"/api/sites/{site_id}/forecast?model=ml&limit=96",
                    f"/api/sites/{site_id}/observations?limit=96",
                    f"/api/sites/{site_id}/metrics",
                    f"/api/sites/{site_id}/quality",
                    f"/api/sites/{site_id}/alerts",
                    f"/api/sites/{site_id}/model-card",
                ]
            )

        for allocation_type in ("realised", "forecast"):
            for matching_mode in ("local_preference", "maximum_match"):
                routes["matching.json"].append(
                    "/api/matching/periods"
                    f"?allocation_type={allocation_type}"
                    f"&matching_mode={matching_mode}&limit=96"
                )
                routes["matching.json"].append(
                    "/api/matching/allocations"
                    f"?allocation_type={allocation_type}"
                    f"&matching_mode={matching_mode}"
                    "&settlement_period=1&limit=100"
                )

        for bundle_name, paths in routes.items():
            for path in paths:
                key = canonical_path(path)
                if key not in bundles[bundle_name]:
                    bundles[bundle_name][key] = fetch_json(client, path)
                index_routes[key] = {"bundle": bundle_name, "key": key}

        health = bundles["core.json"][canonical_path("/health")]

    forecast = pd.read_parquet(
        FORECAST_ARTIFACT,
        columns=["valid_time_utc"],
    )
    start_utc = pd.Timestamp(forecast["valid_time_utc"].min()).isoformat()
    end_utc = pd.Timestamp(forecast["valid_time_utc"].max()).isoformat()

    for bundle_name, responses in bundles.items():
        write_json(
            OUTPUT_ROOT / bundle_name,
            {"version": "extension-phase20-v1", "responses": responses},
        )

    write_json(
        OUTPUT_ROOT / "index.json",
        {
            "version": "extension-phase20-v1",
            "generated_at_utc": health["last_artifact_update"],
            "demo_period": {
                "label": "Forecast window · 17–30 Jun 2025",
                "start_utc": start_utc,
                "end_utc": end_utc,
            },
            "data_origins": {
                "public": "REPD operational assets and cached GB market references",
                "simulated": "Deterministic portfolio, forecasts, allocations and scenarios",
                "uploaded": "Validated in memory and not retained by the demo",
            },
            "routes": index_routes,
        },
    )
    print(
        f"Built {len(index_routes)} static API routes across "
        f"{len(bundles)} bundles in {OUTPUT_ROOT.relative_to(ROOT)}."
    )


if __name__ == "__main__":
    main()
