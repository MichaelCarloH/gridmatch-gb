from __future__ import annotations

import numpy as np


def test_portfolio_forecast_totals_intervals_and_units(api_client) -> None:
    response = api_client.get(
        "/api/portfolio/forecast?method=bottom_up&limit=25"
    )
    assert response.status_code == 200
    assert response.json()["meta"]["units"] == "MWh"
    for row in response.json()["data"]:
        assert np.isclose(
            row["actual_net_mwh"],
            row["actual_demand_mwh"] - row["actual_generation_mwh"],
        )
        for target in ("demand", "generation", "net"):
            assert (
                row[f"{target}_q10_mwh"]
                <= row[f"{target}_q50_mwh"]
                <= row[f"{target}_q90_mwh"]
            )


def test_portfolio_methods_metrics_attribution_and_correlation(
    api_client,
) -> None:
    for method in ("baseline", "bottom_up", "direct", "reconciled"):
        response = api_client.get(
            f"/api/portfolio/forecast?method={method}&limit=1"
        )
        assert response.status_code == 200
        assert response.json()["data"][0]["method"] == method
    unsupported = api_client.get(
        "/api/portfolio/forecast?method=unknown"
    )
    assert unsupported.status_code == 400
    assert (
        api_client.get("/api/portfolio/metrics").json()["meta"]["count"]
        == 12
    )
    attribution = api_client.get(
        "/api/portfolio/error-attribution?level=site"
    )
    assert len(attribution.json()["data"]) == 12
    correlation = api_client.get("/api/portfolio/correlation")
    assert len(correlation.json()["data"]["matrix"]) == 12


def test_matching_modes_are_separate_and_conserve(api_client) -> None:
    response = api_client.get(
        "/api/matching/periods",
        params={
            "allocation_type": "realised",
            "matching_mode": "local_preference",
            "limit": 1000,
        },
    )
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 626
    assert {
        item["allocation_type"] for item in rows
    } == {"realised"}
    assert {
        item["matching_mode"] for item in rows
    } == {"local_preference"}
    for row in rows:
        assert row["matched_mwh"] <= row["total_demand_mwh"] + 1e-8
        assert row["matched_mwh"] <= row["total_generation_mwh"] + 1e-8
        assert np.isclose(
            row["residual_grid_demand_mwh"],
            row["total_demand_mwh"] - row["matched_mwh"],
        )
        assert np.isclose(
            row["unused_generation_mwh"],
            row["total_generation_mwh"] - row["matched_mwh"],
        )


def test_geojson_and_matching_arc_period_filter(api_client) -> None:
    geojson = api_client.get(
        "/api/map/sites.geojson?role=generation"
    )
    assert geojson.status_code == 200
    body = geojson.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 4
    for feature in body["features"]:
        assert feature["geometry"]["type"] == "Point"
        longitude, latitude = feature["geometry"]["coordinates"]
        assert -180 <= longitude <= 180
        assert -90 <= latitude <= 90

    arcs = api_client.get(
        "/api/map/matching-arcs",
        params={
            "settlement_period": 1,
            "allocation_type": "forecast",
            "matching_mode": "local_preference",
            "limit": 1000,
        },
    )
    assert arcs.status_code == 200
    assert arcs.json()["data"]
    assert all(
        row["settlement_period"] == 1
        and row["allocation_type"] == "forecast"
        and row["matching_mode"] == "local_preference"
        for row in arcs.json()["data"]
    )
    assert arcs.json()["meta"]["count"] < 19024


def test_matching_summary_site_summaries_and_comparison(api_client) -> None:
    summary = api_client.get("/api/matching/summary")
    assert summary.status_code == 200
    assert summary.json()["data"]["conservation_passed"] is True
    consumers = api_client.get(
        "/api/matching/consumers?allocation_type=realised"
    )
    generators = api_client.get(
        "/api/matching/generators?allocation_type=realised"
    )
    assert len(consumers.json()["data"]) == 16
    assert len(generators.json()["data"]) == 8
    comparison = api_client.get(
        "/api/matching/comparison?matching_mode=local_preference&limit=5"
    )
    assert comparison.status_code == 200
    assert len(comparison.json()["data"]) == 5
    invalid_range = api_client.get(
        "/api/matching/periods",
        params={
            "start": "2025-07-02T00:00:00Z",
            "end": "2025-07-01T00:00:00Z",
        },
    )
    assert invalid_range.status_code == 400
    assert invalid_range.json()["error"]["code"] == "INVALID_DATE_RANGE"
