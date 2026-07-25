"""DESNZ Renewable Energy Planning Database collection and cleaning."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Iterable

import pandas as pd
from pyproj import Transformer

from gridmatch.clients.base import CachedHttpClient, FetchResult
from gridmatch.data.manifests import SourceManifest
from gridmatch.data.schema import SchemaError

LOGGER = logging.getLogger(__name__)
REPD_URL = "https://assets.publishing.service.gov.uk/media/69fc56908cc72d2f863ea58d/REPD_publication_Q1_2026.csv"
REPD_FIXTURE = Path("data/fixtures/repd_sample.csv")


def clean_column_name(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())).strip("_")


def read_repd_csv(path: Path | str) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, "REPD CSV is not UTF-8 or Windows-1252")


def _pick(columns: Iterable[str], *candidates: str) -> str:
    lookup = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    for candidate in candidates:
        for column in columns:
            if candidate in column.lower():
                return column
    raise SchemaError(f"REPD column not found; expected one of {candidates}")


def convert_bng_to_wgs84(easting: pd.Series, northing: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    east = pd.to_numeric(easting, errors="coerce")
    north = pd.to_numeric(northing, errors="coerce")
    valid = east.between(0, 700000) & north.between(0, 1300000)
    longitude = pd.Series(float("nan"), index=east.index, dtype="float64")
    latitude = pd.Series(float("nan"), index=east.index, dtype="float64")
    if valid.any():
        transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(east[valid].tolist(), north[valid].tolist())
        longitude.loc[valid], latitude.loc[valid] = lon, lat
    coordinate_valid = valid & latitude.between(49, 62) & longitude.between(-9, 3)
    longitude.loc[~coordinate_valid] = float("nan")
    latitude.loc[~coordinate_valid] = float("nan")
    return longitude, latitude, coordinate_valid


def process_repd(raw_path: Path | str) -> pd.DataFrame:
    frame = read_repd_csv(raw_path)
    frame.columns = [clean_column_name(column) for column in frame.columns]
    status_col = _pick(frame.columns, "development_status", "status")
    technology_col = _pick(frame.columns, "technology_type", "technology")
    capacity_col = _pick(frame.columns, "installed_capacity_mwelec", "installed_capacity_mw", "capacity")
    name_col = _pick(frame.columns, "site_name", "project_name")
    operator_col = _pick(frame.columns, "operator_or_applicant", "operator", "developer")
    postcode_col = _pick(frame.columns, "site_postcode", "post_code", "postcode")
    easting_col = _pick(frame.columns, "x_coordinate", "easting")
    northing_col = _pick(frame.columns, "y_coordinate", "northing")
    operational = frame[frame[status_col].astype(str).str.lower().str.contains("operational", na=False)].copy()
    result = pd.DataFrame({
        "project_name": operational[name_col].astype("string"),
        "technology": operational[technology_col].astype("string"),
        "installed_capacity_mw": pd.to_numeric(operational[capacity_col], errors="coerce"),
        "operator": operational[operator_col].astype("string"),
        "status": operational[status_col].astype("string"),
        "postcode": operational[postcode_col].astype("string"),
        "easting": pd.to_numeric(operational[easting_col], errors="coerce"),
        "northing": pd.to_numeric(operational[northing_col], errors="coerce"),
    }).reset_index(drop=True)
    result["longitude"], result["latitude"], result["coordinate_valid"] = convert_bng_to_wgs84(result["easting"], result["northing"])
    result["data_origin"] = "public"
    return result


def to_geojson(frame: pd.DataFrame, destination: Path | str) -> Path:
    features = []
    for row in frame[frame["coordinate_valid"]].to_dict(orient="records"):
        longitude, latitude = float(row.pop("longitude")), float(row.pop("latitude"))
        properties = {key: (None if pd.isna(value) else value) for key, value in row.items()}
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [longitude, latitude]}, "properties": properties})
    payload = {"type": "FeatureCollection", "features": features}
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def collect_repd(client: CachedHttpClient | None = None) -> tuple[pd.DataFrame, SourceManifest, FetchResult]:
    client = client or CachedHttpClient("desnz")
    fetched = client.fetch("repd", REPD_URL, suffix=".csv", fixture_path=REPD_FIXTURE)
    frame = process_repd(fetched.path)
    if not fetched.used_fixture and not REPD_FIXTURE.exists():
        raw = read_repd_csv(fetched.path)
        cleaned = [clean_column_name(column) for column in raw.columns]
        status_name = raw.columns[cleaned.index(_pick(cleaned, "development_status", "status"))]
        sample = raw[raw[status_name].astype(str).str.lower().str.contains("operational", na=False)].head(12)
        REPD_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        sample.to_csv(REPD_FIXTURE, index=False)
    frame["data_origin"] = fetched.data_origin
    parquet_path = Path("data/processed/repd_operational_sites.parquet")
    frame.to_parquet(parquet_path, index=False)
    to_geojson(frame, "public/demo-data/repd_operational_sites.geojson")
    manifest = SourceManifest("repd", fetched.source_url, fetched.retrieved_at, str(fetched.path), str(parquet_path), "1", fetched.data_origin, "Open Government Licence v3.0", fetched.retrieval_mode)
    manifest.write()
    LOGGER.info("wrote REPD sites=%d valid_coordinates=%d", len(frame), int(frame["coordinate_valid"].sum()))
    return frame, manifest, fetched
