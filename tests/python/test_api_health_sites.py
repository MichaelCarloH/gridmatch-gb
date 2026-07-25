from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.dependencies import Settings
from api.index import create_app


def test_healthy_service_and_openapi(api_client) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["model_registry_available"] is True
    assert all(body["artifact_availability"].values())
    openapi = api_client.get("/openapi.json")
    assert openapi.status_code == 200
    schema = openapi.json()
    assert "/api/market/hedge-simulate" in schema["paths"]
    assert "/api/forecast/predict" in schema["paths"]
    assert api_client.get("/docs").status_code == 200


def test_missing_artifacts_degrade_health(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        artifact_dir=tmp_path / "artifacts",
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert not all(response.json()["artifact_availability"].values())


def test_site_list_filters_and_pagination(api_client) -> None:
    all_sites = api_client.get("/api/sites?limit=5&offset=2")
    assert all_sites.status_code == 200
    assert len(all_sites.json()["data"]) == 5
    assert all_sites.json()["meta"]["count"] == 12
    assert all_sites.json()["meta"]["offset"] == 2

    solar = api_client.get(
        "/api/sites?role=generation&technology=solar&ready=true"
    )
    assert solar.status_code == 200
    assert len(solar.json()["data"]) == 2
    assert all(
        item["technology"] == "solar"
        and item["site_role"] == "generation"
        for item in solar.json()["data"]
    )
    london = api_client.get("/api/sites?search=london")
    assert london.json()["meta"]["count"] == 1


def test_known_unknown_site_quality_and_alerts(api_client) -> None:
    known = api_client.get("/api/sites/dem_office_london")
    assert known.status_code == 200
    assert known.json()["data"]["site_id"] == "dem_office_london"
    unknown = api_client.get("/api/sites/does-not-exist")
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "SITE_NOT_FOUND"
    quality = api_client.get(
        "/api/sites/gen_solar_cambridge/quality"
    )
    assert quality.status_code == 200
    assert 0 <= quality.json()["data"]["quality_score"] <= 100
    alerts = api_client.get(
        "/api/sites/gen_solar_cambridge/alerts"
    )
    assert alerts.status_code == 200
    assert any(
        item["code"] == "EXTREME_SPIKE_COUNT"
        for item in alerts.json()["data"]
    )


def test_observation_date_filter_and_default_bound(api_client) -> None:
    response = api_client.get(
        "/api/sites/dem_office_london/observations",
        params={
            "start": "2025-01-01T01:00:00Z",
            "end": "2025-01-01T02:00:00Z",
        },
    )
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 3
    assert all(
        "2025-01-01T01:00:00" <= item["timestamp_utc"][
            :19
        ] <= "2025-01-01T02:00:00"
        for item in rows
    )
    bounded = api_client.get(
        "/api/sites/dem_office_london/observations"
    )
    assert len(bounded.json()["data"]) == 200
    assert bounded.json()["meta"]["count"] == 8640


def test_site_forecast_quantiles_metrics_and_card(api_client) -> None:
    response = api_client.get(
        "/api/sites/dem_office_london/forecast?limit=20&model=ml"
    )
    assert response.status_code == 200
    for row in response.json()["data"]:
        assert row["q10_mwh"] <= row["q50_mwh"] <= row["q90_mwh"]
        assert row["units"] == "MWh"
        assert row["issue_time_utc"] < row["valid_time_utc"]
    metrics = api_client.get(
        "/api/sites/dem_office_london/metrics"
    )
    assert metrics.status_code == 200
    assert metrics.json()["data"]
    card = api_client.get(
        "/api/sites/dem_office_london/model-card"
    )
    assert card.status_code == 200
    assert card.json()["data"]["format"] == "markdown"


def test_api_responses_are_strict_json(api_client) -> None:
    for path in (
        "/health",
        "/api/sites?limit=2",
        "/api/portfolio/metrics",
        "/api/matching/periods?limit=2",
        "/api/market/policy-summary",
        "/api/models?limit=2",
    ):
        response = api_client.get(path)
        assert response.status_code == 200
        json.dumps(response.json(), allow_nan=False)
