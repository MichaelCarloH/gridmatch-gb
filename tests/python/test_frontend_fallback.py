from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FALLBACK_ROOT = ROOT / "public" / "demo-data" / "fallback"


def _read(name: str) -> dict:
    return json.loads((FALLBACK_ROOT / name).read_text(encoding="utf-8"))


def test_static_fallback_index_resolves_every_response() -> None:
    index = _read("index.json")
    bundles: dict[str, dict] = {}
    for route, target in index["routes"].items():
        bundle = bundles.setdefault(target["bundle"], _read(target["bundle"]))
        assert target["key"] in bundle["responses"], route


def test_static_fallback_contains_governed_demo_evidence() -> None:
    index = _read("index.json")

    def response(route: str) -> dict:
        target = index["routes"][route]
        return _read(target["bundle"])["responses"][target["key"]]

    health = response("/health")
    sites = response("/api/sites?limit=100")
    matching = response("/api/matching/summary")
    portfolio = response("/api/portfolio/forecast?limit=48&method=reconciled")
    assert health["status"] == "healthy"
    assert all(health["artifact_availability"].values())
    assert sites["meta"]["count"] == 12
    assert matching["data"]["conservation_passed"] is True
    assert portfolio["data"]
    assert index["demo_period"]["label"] == "Forecast window · 17–30 Jun 2025"


def test_static_fallback_is_compact() -> None:
    total_bytes = sum(path.stat().st_size for path in FALLBACK_ROOT.glob("*.json"))
    assert total_bytes < 3 * 1024 * 1024
