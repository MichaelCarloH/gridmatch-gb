"""Phase 3 public-data orchestration and artifact exports."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import re
from typing import Any, Iterable

import pandas as pd

from gridmatch.clients.carbon import CarbonIntensityClient
from gridmatch.clients.elexon import ElexonClient
from gridmatch.clients.neso import NesoClient
from gridmatch.clients.open_meteo import OpenMeteoClient
from gridmatch.data.calendar import BANK_HOLIDAY_URL, collect_calendar
from gridmatch.data.manifests import SourceManifest
from gridmatch.data.repd import collect_repd

LOGGER = logging.getLogger(__name__)


def _snake(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())).strip("_")


def _records_frame(records: Iterable[dict[str, Any]] | Iterable[Any], origin: str) -> pd.DataFrame:
    frame = pd.json_normalize(list(records))
    if frame.empty:
        raise ValueError("public response contains no demonstration records")
    frame.columns = [_snake(column) for column in frame.columns]
    frame["data_origin"] = origin
    return frame


def _manifest(name: str, source_url: str, retrieved_at: str, raw_path: str, processed_path: Path, origin: str, terms: str, retrieval_mode: str) -> None:
    SourceManifest(name, source_url, retrieved_at, raw_path, str(processed_path), "1", origin, terms, retrieval_mode).write()


def collect_elexon() -> dict[str, Path]:
    client = ElexonClient()
    bm_records, bm_fetch = client.bm_units()
    generation_records, generation_fetch = client.actual_generation("2026-07-15", 1)
    market_records, market_fetch = client.market_index("2026-07-15T00:00:00Z", "2026-07-15T02:00:00Z")
    system_records, system_fetch = client.system_prices("2026-07-15")
    bm = _records_frame(bm_records, bm_fetch.data_origin)
    generation = _records_frame(generation_records, generation_fetch.data_origin)
    market = _records_frame(market_records, market_fetch.data_origin)
    market["price_source"] = "market_index"
    system = _records_frame(system_records, system_fetch.data_origin)
    system["price_source"] = "system_price"
    prices = pd.concat([market, system], ignore_index=True, sort=False)
    output = {
        "bm_units": Path("data/processed/bm_units.parquet"),
        "public_generation": Path("data/processed/public_generation.parquet"),
        "prices": Path("data/processed/prices.parquet"),
    }
    bm.to_parquet(output["bm_units"], index=False)
    generation.to_parquet(output["public_generation"], index=False)
    prices.to_parquet(output["prices"], index=False)
    terms = "Elexon Insights Solution API terms"
    _manifest("bm_units", bm_fetch.source_url, bm_fetch.retrieved_at, str(bm_fetch.path), output["bm_units"], bm_fetch.data_origin, terms, bm_fetch.retrieval_mode)
    _manifest("public_generation", generation_fetch.source_url, generation_fetch.retrieved_at, str(generation_fetch.path), output["public_generation"], generation_fetch.data_origin, terms, generation_fetch.retrieval_mode)
    price_mode = "fixture" if any(fetch.used_fixture for fetch in (market_fetch, system_fetch)) else ("cache" if all(fetch.from_cache for fetch in (market_fetch, system_fetch)) else "live")
    _manifest("prices", f"{market_fetch.source_url}; {system_fetch.source_url}", max(market_fetch.retrieved_at, system_fetch.retrieved_at), f"{market_fetch.path}; {system_fetch.path}", output["prices"], "public", terms, price_mode)
    LOGGER.info("wrote Elexon bm_units=%d generation=%d prices=%d", len(bm), len(generation), len(prices))
    return output


def collect_neso_demo() -> Path:
    client = NesoClient()
    search, search_fetch = client.package_search("historic demand")
    packages = search.get("results", [])
    if not packages:
        raise ValueError("NESO package search returned no historic-demand packages")
    package_id = packages[0].get("id") or packages[0].get("name")
    resources, package, package_fetch = client.discover_resources(str(package_id))
    selected = next((resource for resource in resources if resource.get("datastore_active")), None)
    if selected:
        data, data_fetch = client.datastore_search(str(selected["id"]), limit=96)
        records = data.get("records", [])
        frame = _records_frame(records, data_fetch.data_origin)
        raw_path, source_url, retrieved_at, origin = str(data_fetch.path), data_fetch.source_url, data_fetch.retrieved_at, data_fetch.data_origin
    else:
        selected = next((resource for resource in resources if str(resource.get("format", "")).upper() == "CSV"), None)
        if not selected:
            frame = _records_frame(packages, search_fetch.data_origin)
            raw_path, source_url, retrieved_at, origin = str(search_fetch.path), search_fetch.source_url, search_fetch.retrieved_at, search_fetch.data_origin
        else:
            data_fetch = client.download_csv(str(selected["url"]), "demand_resource")
            frame = pd.read_csv(data_fetch.path).head(96)
            frame.columns = [_snake(column) for column in frame.columns]
            frame["data_origin"] = data_fetch.data_origin
            raw_path, source_url, retrieved_at, origin = str(data_fetch.path), data_fetch.source_url, data_fetch.retrieved_at, data_fetch.data_origin
    frame["neso_package_id"] = package.get("id", package_id)
    frame["neso_resource_id"] = selected.get("id") if selected else None
    path = Path("data/processed/neso_demand_demo.parquet")
    frame.to_parquet(path, index=False)
    mode = data_fetch.retrieval_mode if selected and 'data_fetch' in locals() else search_fetch.retrieval_mode
    _manifest("neso_demand_demo", source_url, retrieved_at, raw_path, path, origin, "NESO data portal terms", mode)
    LOGGER.info("wrote NESO demo rows=%d package=%s", len(frame), package_id)
    return path


def collect_weather() -> Path:
    frame, fetched = OpenMeteoClient().weather(51.5074, -0.1278, "2026-07-01", "2026-07-02")
    path = Path("data/processed/weather.parquet")
    frame.to_parquet(path, index=False)
    _manifest("weather", fetched.source_url, fetched.retrieved_at, str(fetched.path), path, fetched.data_origin, "Open-Meteo CC BY 4.0", fetched.retrieval_mode)
    return path


def collect_carbon_and_calendar() -> dict[str, Path]:
    carbon_records, carbon_fetch = CarbonIntensityClient().national_for_date("2026-07-01")
    carbon = _records_frame(carbon_records, carbon_fetch.data_origin)
    carbon_path = Path("data/processed/carbon_intensity.parquet")
    carbon.to_parquet(carbon_path, index=False)
    _manifest("carbon_intensity", carbon_fetch.source_url, carbon_fetch.retrieved_at, str(carbon_fetch.path), carbon_path, carbon_fetch.data_origin, "National Grid ESO Carbon Intensity API terms", carbon_fetch.retrieval_mode)
    calendar, calendar_fetch = collect_calendar()
    calendar_path = Path("data/processed/calendar.parquet")
    calendar.to_parquet(calendar_path, index=False)
    _manifest("calendar", BANK_HOLIDAY_URL, calendar_fetch.retrieved_at, str(calendar_fetch.path), calendar_path, calendar_fetch.data_origin, "Open Government Licence v3.0", calendar_fetch.retrieval_mode)
    return {"carbon_intensity": carbon_path, "calendar": calendar_path}


def collect_all_public_data() -> dict[str, Path]:
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    repd, _, _ = collect_repd()
    outputs: dict[str, Path] = {
        "repd": Path("data/processed/repd_operational_sites.parquet"),
        "repd_geojson": Path("public/demo-data/repd_operational_sites.geojson"),
    }
    outputs.update(collect_elexon())
    outputs["neso_demand_demo"] = collect_neso_demo()
    outputs["weather"] = collect_weather()
    outputs.update(collect_carbon_and_calendar())
    LOGGER.info("public collection complete repd_sites=%d artifacts=%d", len(repd), len(outputs))
    return outputs
