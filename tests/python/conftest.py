from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.index import app
from gridmatch.data.synthetic import generate_portfolio


@pytest.fixture(scope="session")
def synthetic_portfolio():
    return generate_portfolio()


@pytest.fixture(scope="session")
def api_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def prediction_payload():
    return {
        "site_id": "dem_office_london",
        "forecast_issue_time_utc": "2025-06-19T12:00:00Z",
        "rows": [
            {
                "valid_time_utc": "2025-06-20T12:00:00Z",
                "settlement_period": 27,
                "temperature_c": 18,
                "irradiance_wm2": 500,
                "cloud_cover_pct": 40,
                "wind_speed_mps": 7,
                "wind_direction_deg": 225,
                "wind_gust_mps": 10,
                "surface_pressure_hpa": 1013,
                "is_daylight": True,
                "lag_1": 0.3,
                "lag_2": 0.3,
                "lag_48": 0.4,
                "lag_96": 0.4,
                "lag_336": 0.4,
                "rolling_mean_48": 0.35,
                "rolling_std_48": 0.05,
                "rolling_same_period_mean": 0.4,
                "recent_residual": -0.1,
            }
        ],
    }
