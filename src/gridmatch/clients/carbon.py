"""Official GB carbon-intensity client."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Mapping

from gridmatch.clients.base import CachedHttpClient, FetchResult
from gridmatch.data.schema import require_records


class CarbonIntensityClient:
    base_url = "https://api.carbonintensity.org.uk"

    def __init__(self, http: CachedHttpClient | None = None, fixture_path: Path | str = "data/fixtures/carbon_intensity.json") -> None:
        self.http = http or CachedHttpClient("carbon_intensity")
        self.fixture_path = Path(fixture_path)

    def national_for_date(self, day: str) -> tuple[list[Mapping[str, Any]], FetchResult]:
        fetched = self.http.fetch("national", f"{self.base_url}/intensity/date/{day}", fixture_path=self.fixture_path)
        payload = self.http.read_json(fetched)
        records = require_records(payload, "carbon_intensity")
        if not fetched.used_fixture and not self.fixture_path.exists():
            self.fixture_path.parent.mkdir(parents=True, exist_ok=True)
            self.fixture_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return records, fetched
