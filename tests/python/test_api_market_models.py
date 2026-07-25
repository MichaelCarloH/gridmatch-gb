from __future__ import annotations

import json


def _scenario_payload() -> dict:
    return {
        "timestamp_utc": "2025-06-20T12:00:00Z",
        "forecast_model": "bottom_up",
        "short_cost_multiplier": 1.35,
        "long_value_multiplier": 0.65,
        "risk_preference": 0.0,
    }


def test_price_and_hedge_recommendation_endpoints(api_client) -> None:
    prices = api_client.get("/api/market/prices")
    assert prices.status_code == 200
    assert prices.json()["meta"]["count"] == 58
    assert prices.json()["meta"]["units"] == "GBP/MWh"
    recommendations = api_client.get(
        "/api/market/hedge-recommendations?limit=10"
    )
    assert recommendations.status_code == 200
    assert len(recommendations.json()["data"]) == 10
    assert (
        recommendations.json()["data"][0][
            "price_alignment_method"
        ]
        == "non_contemporaneous_public_settlement_period_proxy"
    )
    assert len(
        api_client.get("/api/market/policy-summary").json()["data"]
    ) == 7
    assert len(
        api_client.get("/api/market/sensitivity").json()["data"]
    ) == 9


def test_hedge_scenario_recomputation_and_invalid_assumptions(
    api_client,
) -> None:
    response = api_client.post(
        "/api/market/hedge-simulate",
        json=_scenario_payload(),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert (
        data["forecast_distribution"]["q10_mwh"]
        <= data["recommended_hedge_mwh"]
        <= data["forecast_distribution"]["q90_mwh"]
    )
    assert data["expected_short_exposure_mwh"] >= 0
    assert data["expected_long_exposure_mwh"] >= 0
    assert "Scenario-only" in data["disclaimer"]
    alias = api_client.post(
        "/api/hedge/simulate",
        json=_scenario_payload(),
    )
    assert alias.status_code == 200

    invalid = _scenario_payload()
    invalid["short_cost_multiplier"] = 0.5
    rejected = api_client.post(
        "/api/market/hedge-simulate",
        json=invalid,
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "VALIDATION_ERROR"


def test_model_registry_filters_details_and_sanitised_paths(
    api_client,
) -> None:
    response = api_client.get("/api/models?limit=100")
    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 90
    assert all(
        item["artifact_path"].startswith("model://")
        and "C:\\" not in item["artifact_path"]
        for item in response.json()["data"]
    )
    filtered = api_client.get(
        "/api/models",
        params={
            "site_id": "dem_office_london",
            "quantile": 0.1,
        },
    )
    assert filtered.json()["meta"]["count"] == 1
    model_id = filtered.json()["data"][0]["model_id"]
    detail = api_client.get(f"/api/models/{model_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["model_id"] == model_id
    missing = api_client.get("/api/models/missing-model")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "MODEL_NOT_FOUND"


def test_research_notebook_index_is_allowlisted(api_client) -> None:
    response = api_client.get("/api/research/notebooks")
    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 4
    notebook_id = response.json()["data"][0]["name"]
    detail = api_client.get(
        f"/api/research/notebooks/{notebook_id}"
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["name"] == notebook_id
    assert not detail.json()["data"]["output_path"].startswith(
        ("C:\\", "/")
    )
    unknown = api_client.get(
        "/api/research/notebooks/../../secrets"
    )
    assert unknown.status_code in {404, 422}


def test_saved_model_prediction_and_unsupported_site(
    api_client,
    prediction_payload,
) -> None:
    response = api_client.post(
        "/api/forecast/predict",
        json=prediction_payload,
    )
    assert response.status_code == 200
    row = response.json()["data"][0]
    assert row["q10_mwh"] <= row["q50_mwh"] <= row["q90_mwh"]
    assert row["point_mwh"] >= 0
    assert row["model_version"] == "site-forecast-v1"
    assert row["inference_only"] is True
    json.dumps(response.json(), allow_nan=False)

    unsupported = dict(prediction_payload)
    unsupported["site_id"] = "unknown-site"
    rejected = api_client.post(
        "/api/forecast/predict",
        json=unsupported,
    )
    assert rejected.status_code == 404
    assert rejected.json()["error"]["code"] == "SITE_NOT_FOUND"
