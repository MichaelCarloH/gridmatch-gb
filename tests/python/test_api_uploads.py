from __future__ import annotations


def test_valid_upload_is_validated_in_memory(api_client) -> None:
    content = (
        "timestamp,consumption_kwh,generation_kwh\n"
        "2025-01-01T00:00:00Z,100,0\n"
        "2025-01-01T00:30:00Z,120,5\n"
        "2025-01-01T01:00:00Z,110,0\n"
    ).encode()
    response = api_client.post(
        "/api/upload/validate",
        files={"file": ("meter.csv", content, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["inferred_frequency_minutes"] == 30
    assert data["received_rows"] == 3
    assert data["expected_rows"] == 3
    assert data["completeness"] == 1
    assert data["duplicates"] == 0
    assert data["quality_score"] == 100
    assert data["site_readiness"] == "ready"
    assert data["permanent_storage"] is False
    assert len(data["annotated_preview"]) == 3


def test_invalid_upload_and_content_type(api_client) -> None:
    invalid = (
        "timestamp,consumption_kwh,generation_kwh\n"
        "2025-01-01T00:00:00Z,100,0\n"
        "2025-01-01T00:00:00Z,-2,bad\n"
    ).encode()
    response = api_client.post(
        "/api/upload/validate",
        files={"file": ("meter.csv", invalid, "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["data"]["site_readiness"] == "review"
    assert response.json()["data"]["anomalies"] > 0

    wrong_type = api_client.post(
        "/api/upload/validate",
        files={"file": ("meter.txt", b"hello", "text/plain")},
    )
    assert wrong_type.status_code == 415
    assert wrong_type.json()["error"]["code"] == "INVALID_UPLOAD_TYPE"


def test_oversized_upload_is_rejected(api_client) -> None:
    content = b"x" * 2_000_001
    response = api_client.post(
        "/api/upload/validate",
        files={"file": ("large.csv", content, "text/csv")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "UPLOAD_TOO_LARGE"
