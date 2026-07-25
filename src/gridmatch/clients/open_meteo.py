"""Open-Meteo retrieval preserving forecast issue and valid times."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
from typing import Iterable

import pandas as pd

from gridmatch.clients.base import CachedHttpClient, FetchResult
from gridmatch.data.schema import SchemaError


WEATHER_VARIABLES = (
    "temperature_2m",
    "cloud_cover",
    "shortwave_radiation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
)


class OpenMeteoClient:
    archive_url = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, http: CachedHttpClient | None = None, fixture_path: Path | str = "data/fixtures/open_meteo_weather.json") -> None:
        self.http = http or CachedHttpClient("open_meteo")
        self.fixture_path = Path(fixture_path)

    def weather(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        *,
        variables: Iterable[str] = WEATHER_VARIABLES,
        model_name: str = "era5",
    ) -> tuple[pd.DataFrame, FetchResult]:
        requested = tuple(variables)
        params = {"latitude": latitude, "longitude": longitude, "start_date": start_date, "end_date": end_date, "hourly": ",".join(requested), "timezone": "UTC", "models": model_name}
        fetched = self.http.fetch("weather", self.archive_url, params=params, fixture_path=self.fixture_path)
        payload = self.http.read_json(fetched)
        hourly = payload.get("hourly") if isinstance(payload, dict) else None
        if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
            raise SchemaError("Open-Meteo response missing hourly.time")
        frame = pd.DataFrame({"valid_time": pd.to_datetime(hourly["time"], utc=True)})
        for variable in requested:
            values = hourly.get(variable)
            if not isinstance(values, list) or len(values) != len(frame):
                raise SchemaError(f"Open-Meteo response missing aligned variable {variable}")
            frame[variable] = values
        frame.insert(0, "issue_time", pd.Timestamp(fetched.retrieved_at))
        frame["latitude"] = latitude
        frame["longitude"] = longitude
        frame["weather_model"] = model_name
        frame["requested_variables"] = ",".join(requested)
        frame["data_origin"] = fetched.data_origin
        if not fetched.used_fixture and not self.fixture_path.exists():
            self.fixture_path.parent.mkdir(parents=True, exist_ok=True)
            self.fixture_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return frame, fetched
