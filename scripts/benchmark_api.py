"""Measure cold and warm local prototype API response times."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.dependencies import Settings
from api.index import create_app

SCENARIO = {
    "timestamp_utc": "2025-06-20T12:00:00Z",
    "forecast_model": "bottom_up",
    "short_cost_multiplier": 1.35,
    "long_value_multiplier": 0.65,
    "risk_preference": 0.0,
}
CHECKS = {
    "health": ("GET", "/health", 100.0),
    "site_list": ("GET", "/api/sites", 250.0),
    "portfolio_forecast": (
        "GET",
        "/api/portfolio/forecast?limit=100",
        500.0,
    ),
    "matching_summary": ("GET", "/api/matching/summary", 500.0),
    "hedge_scenario": (
        "POST",
        "/api/market/hedge-simulate",
        100.0,
    ),
}


def _request(
    client: TestClient,
    method: str,
    path: str,
):
    if method == "POST":
        return client.post(path, json=SCENARIO)
    return client.get(path)


def benchmark(repeats: int = 15) -> dict:
    settings = Settings()
    results = {}
    for name, (method, path, target_ms) in CHECKS.items():
        with TestClient(create_app(settings)) as cold_client:
            started = perf_counter()
            cold_response = _request(cold_client, method, path)
            cold_ms = (perf_counter() - started) * 1000
            cold_response.raise_for_status()
        with TestClient(create_app(settings)) as warm_client:
            _request(warm_client, method, path).raise_for_status()
            durations = []
            for _ in range(repeats):
                started = perf_counter()
                response = _request(warm_client, method, path)
                durations.append((perf_counter() - started) * 1000)
                response.raise_for_status()
        warm_mean = sum(durations) / len(durations)
        results[name] = {
            "cold_ms": round(cold_ms, 3),
            "warm_mean_ms": round(warm_mean, 3),
            "warm_p95_ms": round(
                sorted(durations)[int(0.95 * (len(durations) - 1))],
                3,
            ),
            "target_ms": target_ms,
            "target_passed": warm_mean < target_ms,
        }
    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repeats": repeats,
        "results": results,
        "all_warm_targets_passed": all(
            item["target_passed"] for item in results.values()
        ),
        "interpretation": (
            "Local TestClient prototype benchmark; not a production SLA."
        ),
    }
    destination = ROOT / "artifacts/metrics/api_benchmark.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(output, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return output


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
