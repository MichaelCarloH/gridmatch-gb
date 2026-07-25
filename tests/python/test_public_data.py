from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

from gridmatch.clients.base import CachedHttpClient
from gridmatch.data.manifests import SourceManifest
from gridmatch.data.repd import convert_bng_to_wgs84, process_repd, to_geojson


def test_repd_coordinate_conversion() -> None:
    longitude, latitude, valid = convert_bng_to_wgs84(pd.Series([530000, None]), pd.Series([180000, None]))
    assert bool(valid.iloc[0])
    assert abs(float(latitude.iloc[0]) - 51.50) < 0.1
    assert abs(float(longitude.iloc[0]) - (-0.13)) < 0.1
    assert not bool(valid.iloc[1])


def test_repd_fixture_exports_valid_geojson(tmp_path: Path) -> None:
    frame = process_repd("data/fixtures/repd_sample.csv")
    output = to_geojson(frame, tmp_path / "repd.geojson")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
    assert payload["features"]
    for feature in payload["features"]:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Point"
        longitude, latitude = feature["geometry"]["coordinates"]
        assert -9 <= longitude <= 3
        assert 49 <= latitude <= 62


def test_fixture_fallback_and_cache_reuse(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text('{"data": [{"value": 1}]}', encoding="utf-8")
    client = CachedHttpClient("test_source", raw_root=tmp_path / "raw", retries=0)

    def unavailable(*args, **kwargs):
        raise requests.ConnectionError("deliberate offline test")

    monkeypatch.setattr(client.session, "get", unavailable)
    first = client.fetch("example", "https://example.invalid/data", fixture_path=fixture)
    second = client.fetch("example", "https://example.invalid/data", fixture_path=fixture)
    assert first.used_fixture and first.data_origin == "public" and first.retrieval_mode == "fixture"
    assert second.from_cache and second.used_fixture
    assert first.path == second.path
    assert json.loads(second.path.read_text(encoding="utf-8"))["data"][0]["value"] == 1


def test_source_manifest_creation(tmp_path: Path) -> None:
    manifest = SourceManifest("example", "https://example.test/data", "2026-07-25T00:00:00+00:00", "data/raw/example.json", "data/processed/example.parquet", "1", "public", "Example terms", "fixture")
    path = manifest.write(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"dataset_name", "source_url", "retrieved_at", "raw_path", "processed_path", "schema_version", "data_origin"}
    assert required <= payload.keys()
    assert payload["data_origin"] == "public"
    assert payload["retrieval_mode"] == "fixture"
